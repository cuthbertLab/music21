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
The layout.py module contains two types of objects that specify the layout on
page (or screen) for Scores and other Stream objects.  There are two main types
of Layout objects: (1) layout describing elements and (2) layout defining Streams. 

(1) ScoreLayout, PageLayout, SystemLayout, and StaffLayout objects describe the size of 
pages, the geometry of page and system margins, the distance between staves, etc.
The model for these layout objects is taken directly (perhaps too directly?)
from MusicXML.  These objects all inherit from a BaseLayout class, primarily
as an aid to finding all of these objects as a group.  ScoreLayouts give defaults
for each page, system, and staff.  Thus they contain PageLayout, SystemLayout, and
currently one or more StaffLayout objects (but probably later just one, since I can't find a reason
why MusicXML allows for multiple ones).

PageLayout and SystemLayout objects also have a property, 'isNew', which if set to `True` signifies that a new page
or system should begin here.  In theory, one could define new dimensions for a page
or system in the middle of the system or page without setting isNew to True, in
which case these measurements would start applying on the next page.  In practice,
there's really one good place to use these Layout objects and that's in the first part
in a score at offset 0 of the first measure on a page or system (or for ScoreLayout, at the beginning
of a piece outside of any parts).  But it's not an
error to put them in other places, such as at offset 0 of the first measure of a page
or system in all the other parts.  In fact, MusicXML tends to do this, and it ends up
not being a waste if a program extracts a single part from the middle of a score.

These objects are standard :class:`~music21.base.Music21Object` types, but many
properties such as .duration, .beat, will probably not apply.

When exporting to MusicXML (which is currently the only format in which music21 can and
does preserve these markings), many MusicXML readers will ignore these tags (or worse,
add a new page or system when PageLayout and SystemLayout objects are found but also
add theme wherever they want).  In Finale, this behavior disappears if the MusicXML
document notes that it <supports> new-page and new-system markings.  Music21 will add
the appropriate <supports> tags if the containing Stream has `.definesExplicitPageBreaks` 
and `.definesExplicitSystemBreaks` set to True.  When importing a score that has the
<supports> tag set, music21 will set `.definesExplicitXXXXBreaks` to True for the 
outer score and the inner parts.  However, this means that if the score is manipulated
enough that the prior layout information is obsolete, programs will need to set these
properties to False or move the Layout tags accordingly.

(2) The second set of objects are Stream subclasses that can be employed when a program
needs to easily iterate around the systems and pages defined through the layout objects
just described, or to get the exact position on a page (or a graphical representation
of a page) for a particular measure or system.  (Individual notes coming soon).  Normal
Score streams can be changed into LayoutStreams by calling `divideByPages(s)` on them.
A Score that was organized: Score->Parts->Measures would then become: LayoutScore->Pages->Systems->Parts->Measures. 

No provision for system scaling exists yet -- this is another TODO: 

The new LayoutScore has methods that enable querying what page or system a measure is in, and
specifically where on a page a measure is (or the dimensions of every measure in the piece).  However
do not call .show() on a LayoutScore -- the normal score it's derived from will work just fine.
Nor does calling .show() on a Page or System work yet, but once the LayoutStream has been created,
code like this can be done:  

     s = stream.Stream(...)
     ls = layout.divideByPages(s)
     pg2sys3 = ls.pages[1].systems[2]  # n.b.! 1, 2
     startMeasure, endMeasure = pg2sys3.startMeasure, pg2sys3.endMeasure
     scoreExcerpt = s.measures(startMeasure, endMeasure)
     scoreExcerpt.show()  # will show page 2, system 3
     
Note that while the the coordinates given by music21 for a musicxml score (based on margins, staff size, etc.)
generally reflect what is actually in a musicxml producer, unfortuantely, x-positions are far less accurately
produced by most editors.  For instance, Finale scores with measure sizes that have been manually adjusted tend to show their
unadjusted measure width and not their actual measure width in the musicxml.
'''

# may need to have object to convert between size units

import unittest

from music21 import base
from music21 import exceptions21
from music21 import spanner
from music21 import stream

from music21 import environment
_MOD = "layout.py"
environLocal = environment.Environment(_MOD)


class LayoutBase(base.Music21Object):
    def __init__(self, *args, **keywords):
        base.Music21Object.__init__(self)
    

#-------------------------------------------------------------------------------
class ScoreLayout(LayoutBase):
    '''Parameters for configuring a score's layout.
    
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
        LayoutBase.__init__(self)
        
        self.scalingMillimeters = None
        self.scalingTenths = None
        self.pageLayout = None
        self.systemLayout = None
        self.staffLayoutList = []
        self.appearance = None
        self.musicFont = None
        self.wordFont = None

        for key in keywords:
            if key.lower() == 'scalingmillimeters':
                self.scalingMillimeters = keywords[key]
            elif key.lower() == 'scalingtenths':
                self.scalingTenths = keywords[key]
            elif key.lower() == 'pagelayout':
                self.rightMargin = keywords[key]
            elif key.lower() == 'systemlayout':
                self.systemLayout = keywords[key]
            elif key.lower() == 'stafflayout':
                self.staffLayoutList = keywords[key]
            elif key.lower() == 'appearance':
                self.appearance = keywords[key]
            elif key.lower() == 'musicfont':
                self.musicFont = keywords[key]
            elif key.lower() == 'wordfont':
                self.wordFont = keywords[key]

    def __repr__(self):
        return "<music21.layout.ScoreLayout>"

    def tenthsToMillimeters(self, tenths):
        '''
        given the scalingMillimeters and scalingTenths,
        return the value in millimeters of a number of
        musicxml "tenths" where a tenth is a tenth of the distance
        from one staff line to another

        returns 0.0 if either of scalingMillimeters or scalingTenths
        is undefined.
        
        >>> from music21 import *
        >>> sl = layout.ScoreLayout(scalingMillimeters = 2.0, scalingTenths=10)
        >>> print sl.tenthsToMillimeters(10)
        2.0
        >>> print sl.tenthsToMillimeters(17) # printing to round
        3.4
        '''
        if self.scalingMillimeters is None or self.scalingTenths is None:
            return 0.0
        millimetersPerTenth = float(self.scalingMillimeters)/self.scalingTenths
        return millimetersPerTenth * tenths
    

#-------------------------------------------------------------------------------
class PageLayout(LayoutBase):
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
        LayoutBase.__init__(self)
        
        self.pageNumber = None
        self.leftMargin = None
        self.rightMargin = None
        self.topMargin = None
        self.bottomMargin = None
        self.pageHeight = None
        self.pageWidth = None

        # store if this is the start of a new page
        self.isNew = None

        for key in keywords:
            if key.lower() == 'pagenumber':
                self.pageNumber = keywords[key]
            elif key.lower() == 'leftmargin':
                self.leftMargin = keywords[key]
            elif key.lower() == 'rightmargin':
                self.rightMargin = keywords[key]
            elif key.lower() == 'topmargin':
                self.topMargin = keywords[key]
            elif key.lower() == 'bottommargin':
                self.bottomMargin = keywords[key]
            elif key.lower() == 'pageheight':
                self.pageHeight = keywords[key]
            elif key.lower() == 'pagewidth':
                self.pageWidth = keywords[key]
            elif key.lower() == 'isnew':
                self.isNew = keywords[key]

    def __repr__(self):
        return "<music21.layout.PageLayout>"


#-------------------------------------------------------------------------------
class SystemLayout(LayoutBase):
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
        LayoutBase.__init__(self)
        
        self.leftMargin = None
        self.rightMargin = None
        # no top or bottom margins

        # this is probably the distance between adjacent systems
        self.distance = None
        self.topDistance = None

        # store if this is the start of a new system
        self.isNew = None

        for key in keywords:
            if key.lower() == 'leftmargin':
                self.leftMargin = keywords[key]
            elif key.lower() == 'rightmargin':
                self.rightMargin = keywords[key]

            elif key.lower() == 'distance':
                self.distance = keywords[key]
            elif key.lower() == 'topdistance':
                self.topDistance = keywords[key]
            elif key.lower() == 'isnew':
                self.isNew = keywords[key]

    def __repr__(self):
        return "<music21.layout.SystemLayout>"

class StaffLayout(LayoutBase):
    '''
    Object that configures or alters the distance between
    one staff and another in a system.

    StaffLayout objects may be found on Measure or 
    Part Streams.
    
    The musicxml equivalent <staff-layout> lives in
    the <defaults> and in <print> attributes.
    
    >>> from music21 import *
    >>> sl = layout.StaffLayout(distance=3, staffNumber=1)
    >>> sl
    <music21.layout.StaffLayout distance 3, staffNumber 1>
    >>> sl.distance
    3
    
    The "number" attribute refers to which staff number
    in a part group this refers to.  Thus, it's not
    necessary in music21, but we store it if it's there.
    (defaults to None)
    
    >>> sl.staffNumber
    1
    '''
    def __init__(self, *args, **keywords):
        LayoutBase.__init__(self)
        
        # this is the distance between adjacent staves
        self.distance = None

        self.staffNumber = None

        for key in keywords:
            if key.lower() == 'distance':
                self.distance = keywords[key]
            elif key.lower() == 'staffnumber':
                self.staffNumber = keywords[key]
 
    def __repr__(self):
        return "<music21.layout.StaffLayout distance %d, staffNumber %r>" % (self.distance, self.staffNumber)

#-------------------------------------------------------------------------------
class LayoutException(exceptions21.Music21Exception):
    pass

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

        if 'symbol' in keywords:
            self.symbol = keywords['symbol'] # user property
        if 'barTogether' in keywords:
            self.barTogether = keywords['barTogether'] # user property
        if 'name' in keywords:
            self.name = keywords['name'] # user property
        if 'abbreviation' in keywords:
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
        elif value.lower() in ['square']:
            self._symbol = 'bracket' # not supported in XML2; in XML3
        
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


#----------------------------------------------------------------
# Stream subclasses for layout

def divideByPages(scoreIn, printUpdates=False, fastMeasures=False):
    '''
    Divides a score into a series of smaller scores according to page
    breaks.  Only searches for PageLayout.isNew or SystemLayout.isNew 
    on the first part.  Returns a new `LayoutScore` object.
    
    If fastMeasures is True, then the newly created System objects
    do not have Clef signs, Key Signatures, or necessarily all the
    applicable spanners in them.  On the other hand, the position
    (on the page) information will be just as correct with
    fastMeasures = True and it will run much faster on large scores
    (because our spanner gathering algorithm is currently O(n^2);
    something TODO: to fix.)
    '''
    pageMeasureTuples = getPageRegionMeasureNumbers(scoreIn)
    systemMeasureTuples = getSystemRegionMeasureNumbers(scoreIn)
    firstMeasureNumber = pageMeasureTuples[0][0]
    lastMeasureNumber = pageMeasureTuples[-1][1]

    
    scoreLists = LayoutScore()
    scoreLists.definesExplicitPageBreaks = True
    scoreLists.definesExplicitSystemBreaks = True
    scoreLists.startMeasure = firstMeasureNumber
    scoreLists.endMeasure = lastMeasureNumber
    for el in scoreIn:
        if 'Part' not in el.classes:
            if 'ScoreLayout' in el.classes:
                scoreLists.scoreLayout = el
            scoreLists.insert(el.getOffsetBySite(scoreIn), el)
    
    pageNumber = 0
    systemNumber = 0
    for pageStartM, pageEndM in pageMeasureTuples:
        pageNumber += 1
        if printUpdates is True:
            print "updating page", pageNumber
        #thisPage = scoreIn.measures(pageStartM, pageEndM)
        #thisPage.__class__ = Page
        thisPage = Page()
        thisPage.measureStart = pageStartM
        thisPage.measureEnd = pageEndM
        thisPage.pageNumber = pageNumber
        if fastMeasures is True:
            thisPageAll = scoreIn.measures(pageStartM, pageEndM, collect=[], gatherSpanners=False)
        else:
            thisPageAll = scoreIn.measures(pageStartM, pageEndM)
        thisPage.systemStart = systemNumber + 1
        for el in thisPageAll:
            if 'Part' not in el.classes and 'StaffGroup' not in el.classes: 
                thisPage.insert(el.getOffsetBySite(thisPageAll), el)
        firstMeasureOfFirstPart = thisPageAll.parts[0].getElementsByClass('Measure')[0]
        for el in firstMeasureOfFirstPart:
            if 'PageLayout' in el.classes:
                thisPage.pageLayout = el       

        
        for systemStartM, systemEndM in systemMeasureTuples:
            if systemStartM < pageStartM or systemEndM > pageEndM:
                continue
            systemNumber += 1
            if fastMeasures is True:
                thisSystem = scoreIn.measures(systemStartM, systemEndM, collect=[], gatherSpanners=False)           
            else:
                thisSystem = scoreIn.measures(systemStartM, systemEndM)
            thisSystem.__class__ = System
            thisSystem.measureStart = systemStartM
            thisSystem.measureEnd = systemEndM
            allSystemLayouts = thisSystem.flat.getElementsByClass('SystemLayout')
            if len(allSystemLayouts) > 0:
                thisSystem.systemLayout = allSystemLayouts[0]
            else:
                thisSystem.systemLayout = None
            
            thisPage._appendCore(thisSystem)
        thisPage.systemEnd = systemNumber
        thisPage._elementsChanged()
        scoreLists._appendCore(thisPage)
    scoreLists._elementsChanged()
    return scoreLists    
    
def getPageRegionMeasureNumbers(scoreIn):
    return getRegionMeasureNumbers(scoreIn, 'Page')

def getSystemRegionMeasureNumbers(scoreIn):
    return getRegionMeasureNumbers(scoreIn, 'System')    

def getRegionMeasureNumbers(scoreIn, region='Page'):
    '''
    get a list where each entry is a 2-tuplet whose first number 
    refers to the first measure on a page and whose second number
    is the last measure on the page.
    '''
    if region == 'Page':
        classesToReturn = ['PageLayout']
    elif region == 'System':
        classesToReturn = ['PageLayout', 'SystemLayout']
    
    firstPart = scoreIn.parts[0]
    # first measure could be 1 or 0 (or something else)
    allMeasures = firstPart.getElementsByClass('Measure')
    firstMeasureNumber = allMeasures[0].number
    lastMeasureNumber = allMeasures[-1].number
    measureStartList = [firstMeasureNumber]
    measureEndList = []
    allPageLayout = firstPart.flat.getElementsByClass(classesToReturn)

    for pl in allPageLayout:
        plMeasureNumber = pl.measureNumber
        if plMeasureNumber not in measureStartList: # in case of firstMeasureNumber or system and page layout at same time.
            measureStartList.append(plMeasureNumber)
            measureEndList.append(plMeasureNumber - 1)
    measureEndList.append(lastMeasureNumber)
    measureList = zip(measureStartList, measureEndList)
    return measureList

class LayoutScore(stream.Opus):
    '''
    Designation that this Score is
    divided into Pages, Systems, Staves (=Parts),
    Measures, etc.
    
    Used for computing location of notes, etc.
    '''
    def __init__(self, *args, **keywords):
        stream.Opus.__init__(self, *args, **keywords)
        self.scoreLayout = None
        self.startMeasure = None
        self.endMeasure = None
    
    def _getPages(self):
        return self.getElementsByClass(Page)
    
    pages = property(_getPages)

    def getPageAndSystemNumberFromMeasureNumber(self, measureNumber):
        '''
        Given a layoutScore from divideByPages and a measureNumber returns a tuple
        of (pageId, systemId).  Note that pageId is probably one less than the page number,
        assuming that the first page number is 1, the pageId for the first page will be 0.
        
        Similarly, the first systemId on each page will be 0
    
        >>> from music21 import *
        >>> #_DOCS_SHOW g = corpus.parse('luca/gloria')
        >>> #_DOCS_SHOW gl = layout.divideByPages(g)
        >>> #_DOCS_SHOW gl.getPageAndSystemNumberFromMeasureNumber(100)
        >>> (3, 2) #_DOCS_HIDE
        (3, 2)
        '''
        foundPage = None
        foundPageId = None

        for pageId, thisPage in enumerate(self.pages):
            if measureNumber < thisPage.measureStart or measureNumber > thisPage.measureEnd:
                continue
            foundPage = thisPage
            foundPageId = pageId
            break
    
        if foundPage is None:
            raise LayoutException("Cannot find this measure on any page!")
    
        foundSystem = None
        foundSystemId = None 
        for systemId, thisSystem in enumerate(foundPage.systems):
            if measureNumber < thisSystem.measureStart or measureNumber > thisSystem.measureEnd:
                continue
            foundSystem = thisSystem
            foundSystemId = systemId
            break
    
        if foundSystem is None:
            raise LayoutException("that's strange, this measure was supposed to be on this page, but I couldn't find it anywhere!")
        return (foundPageId, foundSystemId)    
    
    def getMarginsAndSizeForPageId(self, pageId):
        '''
        return a tuple of (top, left, bottom, right, width, height) margins for a given pageId in tenths
        
        Default of (100, 100, 100, 100, 850, 1100) if undefined
        
        >>> from music21 import *
        >>> #_DOCS_SHOW g = corpus.parse('luca/gloria')
        >>> #_DOCS_SHOW g.parts[0].getElementsByClass('Measure')[22].getElementsByClass('PageLayout')[0].leftMargin = 204.0
        >>> #_DOCS_SHOW gl = layout.divideByPages(g)
        >>> #_DOCS_SHOW gl.getMarginsAndSizeForPageId(1)
        >>> (171.0, 204.0, 171.0, 171.0, 1457.0, 1886.0) #_DOCS_HIDE
        (171.0, 204.0, 171.0, 171.0, 1457.0, 1886.0)
        '''
        ## define defaults
        pageMarginTop = 100
        pageMarginLeft = 100
        pageMarginRight = 100
        pageMarginBottom = 100
        pageWidth = 850
        pageHeight = 1100
        
        thisPage = self.pages[pageId]

        # override defaults with scoreLayout
        if self.scoreLayout is not None:
            scl = self.scoreLayout
            if scl.pageLayout is not None:
                pl = scl.pageLayout
                if pl.pageWidth is not None:
                    pageWidth = pl.pageWidth
                if pl.pageHeight is not None:
                    pageHeight = pl.pageHeight
                if pl.topMargin is not None:
                    pageMarginTop = pl.topMargin
                if pl.leftMargin is not None:
                    pageMarginLeft = pl.leftMargin
                if pl.rightMargin is not None:
                    pageMarginRight = pl.rightMargin
                if pl.bottomMargin is not None:
                    pageMarginBottom = pl.bottomMargin                 

        # override global information with page specific pageLayout
        if thisPage.pageLayout is not None:
            pl = thisPage.pageLayout
            if pl.pageWidth is not None:
                pageWidth = pl.pageWidth
            if pl.pageHeight is not None:
                pageHeight = pl.pageHeight
            if pl.topMargin is not None:
                pageMarginTop = pl.topMargin
            if pl.leftMargin is not None:
                pageMarginLeft = pl.leftMargin
            if pl.rightMargin is not None:
                pageMarginRight = pl.rightMargin
            if pl.bottomMargin is not None:
                pageMarginBottom = pl.bottomMargin                 
 
        return (pageMarginTop, pageMarginLeft, pageMarginBottom, pageMarginRight, pageWidth, pageHeight)

    def getPositionForSystem(self, pageId, systemId):
        '''
        first systems on a page use a different positioning.
        
        returns a tuple of the (top, left, right, and bottom) where each unit is relative to the page margins
        
        N.B. right is NOT the width -- it is different.  It is the offset to the right margin.  weird, inconsistent, but most useful...
        bottom is the hard part to compute...
        
#        >>> from music21 import *
#        >>> g = corpus.parse('luca/gloria')
#        >>> gl = layout.divideByPages(g)
#        >>> gl.getPositionForSystem(0, 0)
#        (62.0, 1.0, 0.0, 362.0)
#        >>> gl.getPositionForSystem(0, 1)
#        (468.0, 4.0, 0.0, 768.0)
#        >>> gl.getPositionForSystem(0, 2)
#        (874.0, 4.0, 0.0, 1174.0)
#        >>> gl.getPositionForSystem(1, 0)
#        (62.0, 4.0, 0.0, 362.0)
#        >>> gl.getPositionForSystem(1, 1)
#        (468.0, 4.0, 0.0, 768.0)
        '''
        leftMargin = 0
        rightMargin = 0
        # no top or bottom margins
        
        # distance from previous
        previousDistance = 0
        systemHeight = 400
                
        # override defaults with scoreLayout
        if self.scoreLayout is not None:
            scl = self.scoreLayout
            if scl.systemLayout is not None:
                sl = scl.systemLayout
                if sl.leftMargin is not None:
                    leftMargin = sl.leftMargin
                if sl.rightMargin is not None:
                    rightMargin = sl.rightMargin
                if systemId == 0:
                    if sl.topDistance is not None:
                        previousDistance = sl.topDistance
                else:
                    if sl.distance is not None:
                        previousDistance = sl.distance

        # override global information with system specific pageLayout
        thisSystem = self.pages[pageId].systems[systemId]
        
        if thisSystem.systemLayout is not None:
            sl = thisSystem.systemLayout
            if sl.leftMargin is not None:
                leftMargin = sl.leftMargin
            if sl.rightMargin is not None:
                rightMargin = sl.rightMargin
            if systemId == 0:
                if sl.topDistance is not None:
                    previousDistance = sl.topDistance
            else:
                if sl.distance is not None:
                    previousDistance = sl.distance

        if systemId > 0:
            lastSystemDimensions = self.getPositionForSystem(pageId, systemId - 1)
            bottomOfLastSystem = lastSystemDimensions[3]
        else:
            bottomOfLastSystem = 0
            
        numParts = len(thisSystem.parts)
        lastPart = numParts -1  # assuming no invisible staves for now...
        unused_systemStart, systemHeight = self.getPositionForStaff(pageId, systemId, lastPart)
        
        top = previousDistance + bottomOfLastSystem
        bottom = systemHeight + previousDistance + bottomOfLastSystem    
        return (top, leftMargin, rightMargin, bottom)

        
    def getPositionForStaff(self, pageId, systemId, partId):
        '''
        return a tuple of (top, bottom) for a staff, specified by a given pageId, systemId, and partId in tenths
 
        Specified with respect to the top of the system.

        Staff scaling (<staff-details> in musicxml inside an <attributes> object) not taken into account, nor non 5-line staves
                
#        >>> from music21 import *
#        >>> g = corpus.parse('luca/gloria')
#        >>> gl = layout.divideByPages(g)
#        >>> gl.getPositionForStaff(0, 0, 0)
#        (0, 40)
#        >>> gl.getPositionForStaff(0, 0, 1)
#        (144.0, 184.0)
#        >>> gl.getPositionForStaff(0, 0, 2)
#        (260.0, 300.0)
#        >>> gl.getPositionForStaff(0, 1, 0)
#        (0, 40)
        '''
        ## define defaults
        staffDistanceFromPrevious = 0
        staffHeight = 40
        
        if partId != 0:
            staffDistanceFromPrevious = 40 # sensible default?
            
            if self.scoreLayout is not None:
                scl = self.scoreLayout
                if len(scl.staffLayoutList) > 0:
                    staffDistanceFromPrevious = scl.staffLayoutList[0].distance
    
            # override global information with staff specific pageLayout
            thisStaff = self.pages[pageId].systems[systemId].parts[partId]
            try:
                firstMeasureOfStaff = thisStaff.getElementsByClass('Measure')[0]
                allStaffLayouts = firstMeasureOfStaff.getElementsByClass('StaffLayout')
                if len(allStaffLayouts) > 0:
                    staffLayoutObj = allStaffLayouts[0]
                    if staffLayoutObj.distance is not None:
                        staffDistanceFromPrevious = staffLayoutObj.distance
            except: 
                environLocal.warn("No measures found in pageId %d, systemId %d, partId %d" % (pageId, systemId, partId))
        
        if partId > 0:
            unused_staffDistanceFromStart, previousStaffBottom = self.getPositionForStaff(pageId, systemId, partId - 1)
        else:
            previousStaffBottom = 0
        
        staffDistanceFromStart = staffDistanceFromPrevious + previousStaffBottom
        staffBottom = staffDistanceFromStart + staffHeight
        
        return (staffDistanceFromStart, staffBottom)        

    def getPositionForPartMeasure(self, partId, measureNumber, returnFormat='tenths'):
        '''
        Given a layoutScore from divideByPages, a partId, and a measureNumber, 
        returns a tuple of ((top, left), (bottom, right), pageId) 
        allowing an exact position for the measure.  
        If returnFormat is "tenths", then it will be returned in tenths.
        
        If returnFormat is "float", returns each as a number from 0 to 1 where 0 is the top or left
        of the page, and 1 is the bottom or right of the page.

#        >>> from music21 import *
#        >>> g = corpus.parse('luca/gloria')
#        >>> gl = layout.divideByPages(g)
#        >>> gl.getPositionForPartMeasure(0, 1)
#        ((233.0, 175.0), (273.0, 376.0), 0)
#        >>> gl.getPositionForPartMeasure(0, 1, returnFormat='float')
#        ((0.123..., 0.120...), (0.144..., 0.258...), 0)
#        >>> gl.getPositionForPartMeasure(0, 7)
#        ((233.0, 1107.0), (273.0, 1287.0), 0)
#        >>> gl.getPositionForPartMeasure(1, 8)
#        ((783.0, 175.0), (823.0, 398.0), 0)
        '''
        pageId, systemId = self.getPageAndSystemNumberFromMeasureNumber(measureNumber)
        
        startXMeasure, endXMeasure = self.measurePositionWithinStaff(measureNumber, pageId, systemId)
        staffTop, staffBottom = self.getPositionForStaff(pageId, systemId, partId)
        systemTop, systemLeft, unused_systemRight, unused_systemBottom = self.getPositionForSystem(pageId, systemId)
        pageMarginTop, pageMarginLeft, unused_pageMarginBottom, unusedPageMarginRight, pageWidth, pageHeight = self.getMarginsAndSizeForPageId(pageId)
        
        top = pageMarginTop + systemTop + staffTop
        left = pageMarginLeft + systemLeft + startXMeasure
        bottom = pageMarginTop + systemTop + staffBottom
        right = pageMarginLeft + systemLeft + endXMeasure
        
        if returnFormat == 'tenths':
            return ((top, left), (bottom, right), pageId)
        else:
            pageWidth = float(pageWidth)
            pageHeight = float(pageHeight)
            topRatio = top/pageHeight
            leftRatio = left/pageWidth
            bottomRatio = bottom/pageHeight
            rightRatio = right/pageWidth
            return ((topRatio, leftRatio), (bottomRatio, rightRatio), pageId)
         
        #return self.getPositionForPartIdSystemIdPageIdMeasure(partId, systemId, pageId, measureNumber, returnFormat)

    def measurePositionWithinStaff(self, measureNumber, pageId=None, systemId=None):
        '''
        Given a measure number, find the start and end X positions (with respect to the system margins) for the measure.
        
        if pageId and systemId are given, then it will speed up the search. But not necessary
    
#        >>> from music21 import *
#        >>> g = corpus.parse('luca/gloria')
#        >>> gl = layout.divideByPages(g)
#        >>> gl.measurePositionWithinStaff(1, 0, 0)
#        (0, 201.0)
#        >>> gl.measurePositionWithinStaff(2, 0, 0)
#        (201.0, 380.0)
#        >>> gl.measurePositionWithinStaff(3, 0, 0)
#        (380.0, 547.0)
#        >>> gl.measurePositionWithinStaff(7)
#        (932.0, 1112.0)
#        >>> gl.measurePositionWithinStaff(8)
#        (0, 223.0)
        '''
        if pageId is None or systemId is None:
            pageId, systemId = self.getPageAndSystemNumberFromMeasureNumber(measureNumber)
            
        thisSystem = self.pages[pageId].systems[systemId]
        startOffset = 0
        width = None
        measureStream = thisSystem.parts[0].getElementsByClass('Measure')
        for m in measureStream:
            #print m
            if m.layoutWidth is not None:
                width = float(m.layoutWidth)
            mNumber = m.number
            if mNumber == measureNumber:
                break
            else:
                startOffset += width
        if width is None:
            # no widths defined:
            width = 0 # bad guess but do later.
            
        return startOffset, startOffset + width
    
    def getAllMeasurePositionsInDocument(self, returnFormat='tenths', printUpdates=False):
        '''
        returns a list of dictionaries, where each dictionary gives the measure number
        and other information, etc. in the document.
        
        # >>> from music21 import *
        # >>> g = corpus.parse('luca/gloria')
        # >>> gl = layout.divideByPages(g)
        # >>> gl.getAllMeasurePositionsInDocument()
        '''
        numParts = len(self.pages[0].systems[0].parts)
        allRetInfo = []
        for mNum in range(self.startMeasure, self.endMeasure):
            if printUpdates is True:
                print "Doing measure ", mNum
            mList = []
            for pNum in range(numParts):
                tupleInfo = self.getPositionForPartMeasure(pNum, mNum, returnFormat)
                infoDict = {}
                infoDict['measureNumberActual'] = mNum
                infoDict['measureNumber'] = mNum - 1
                infoDict['partNumber'] = pNum
                infoDict['top'] = tupleInfo[0][0]
                infoDict['left'] = tupleInfo[0][1]
                infoDict['bottom'] = tupleInfo[1][0]
                infoDict['right'] = tupleInfo[1][1]
                infoDict['pageNumber'] = tupleInfo[2]
                mList.append(infoDict)
            allRetInfo.append(mList)
        return allRetInfo

class Page(stream.Score):
    '''
    Designation that all the music in this Stream
    belongs on a single notated page.
    '''
    def __init__(self, *args, **keywords):
        stream.Score.__init__(self, *args, **keywords)
        self.pageNumber = 1
        self.measureStart = None
        self.measureEnd = None
        self.systemStart = None
        self.systemEnd = None
        self.pageLayout = None

    def _getSystems(self):
        return self.getElementsByClass(System)
    
    systems = property(_getSystems)

    
class System(stream.Score):
    '''
    Designation that all the music in this Stream
    belongs on a single notated system.
    '''
    def __init__(self, *args, **keywords):
        stream.Stream.__init__(self, *args, **keywords)
        self.systemNumber = 1
        self.systemLayout = None
        self.measureStart = None
        self.measureEnd = None

#class Staff(stream.Part):
#    '''
#    Designation that all the music in this Stream
#    belongs on a single Staff.
#    '''
#    def __init__(self, *args, **keywords):
#        stream.Part.__init__(self, *args, **keywords)
#        self.staffNumber = 1


_DOC_ORDER = [ScoreLayout, PageLayout, SystemLayout, StaffLayout, LayoutBase,
              LayoutScore, Page]
#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):
        import music21
        from music21 import note
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
        c = corpus.parse('luca/gloria', forceSource=True).parts[0]
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

