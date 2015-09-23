# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         musicxml/xmlToM21.py
# Purpose:      Conversion from MusicXML to Music21
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
import copy
import math
#import pprint
import sys
#import traceback
import unittest
from music21.ext import six

if six.PY3:
    import xml.etree.ElementTree as ET  # @UnusedImport
else:
    try:
        import xml.etree.cElementTree as ET
    except ImportError:
        import xml.etree.ElementTree as ET
        

from music21 import common
from music21 import exceptions21
from music21.musicxml import xmlObjects

# modules that import this include converter.py.
# thus, cannot import these here
from music21 import bar
from music21 import beam
from music21 import chord
from music21 import clef
from music21 import duration
from music21 import dynamics
from music21 import expressions
from music21 import harmony # for chord symbols
from music21 import instrument
from music21 import interval # for transposing instruments
from music21 import key
from music21 import layout
from music21 import metadata
from music21 import note
from music21 import meter
from music21 import pitch
from music21 import repeat
from music21 import spanner
from music21 import stream
from music21 import tempo
from music21 import text # for text boxes
from music21 import tie

from music21 import environment
_MOD = "musicxml.xmlToM21"
environLocal = environment.Environment(_MOD)

#-------------------------------------------------------------------------------
class MusicXMLImportException(exceptions21.Music21Exception):
    pass

class XMLBarException(MusicXMLImportException):
    pass


#-------------------------------------------------------------------------------
# Helpers...

# Durations

def musicXMLTypeToType(value):
    '''
    Utility function to convert a MusicXML duration type to an music21 duration type.
    
    Changes 'long' to 'longa' and deals with a Guitar Pro 5.2 bug in MusicXML
    export, that exports a 32nd note with the type '32th'.

    >>> musicxml.xmlToM21.musicXMLTypeToType('long')
    'longa'
    >>> musicxml.xmlToM21.musicXMLTypeToType('32th')
    '32nd'
    >>> musicxml.xmlToM21.musicXMLTypeToType('quarter')
    'quarter'
    >>> musicxml.xmlToM21.musicXMLTypeToType(None)
    Traceback (most recent call last):
    MusicXMLImportException...
    '''
    # MusicXML uses long instead of longa
    if value not in duration.typeToDuration:
        if value == 'long':
            return 'longa'
        elif value == '32th':
            return '32nd'
        else:
            raise MusicXMLImportException('found unknown MusicXML type: %s' % value)
    else:
        return value
    
def _floatOrIntStr(strObj):
    '''
    Convert a string to float or int if possible...
    
    >>> _f = musicxml.xmlToM21._floatOrIntStr
    >>> _f("20.3")
    20.3
    >>> _f("20.0")
    20
    >>> _f(None) is None
    True
    >>> _f("hi")
    'hi'
    '''
    if strObj is None:
        return None
    try:
        val = float(strObj)
        if val == int(val):
            val = int(val)
        return val
    except ValueError:
        return strObj
        
def _setAttributeFromAttribute(m21El, xmlEl, xmlAttributeName, attributeName=None, transform=None):
    '''
    If xmlEl has a at least one element of tag==tag with some text. If
    it does, set the attribute either with the same name (with "foo-bar" changed to
    "fooBar") or with attributeName to the text contents.
    
    Pass a function or lambda function as transform to transform the value before setting it
    
    >>> from xml.etree.ElementTree import fromstring as El
    >>> e = El('<page-layout new-page="yes" page-number="4" />')

    >>> setb = musicxml.xmlToM21._setAttributeFromAttribute
    >>> pl = layout.PageLayout()
    >>> setb(pl, e, 'page-number')
    >>> pl.pageNumber
    '4'

    >>> setb(pl, e, 'new-page', 'isNew')
    >>> pl.isNew
    'yes'


    Transform the pageNumber value to an int.

    >>> setb(pl, e, 'page-number', transform=int)
    >>> pl.pageNumber
    4
    
    More complex...
    
    >>> convBool = musicxml.xmlObjects.yesNoToBoolean
    >>> setb(pl, e, 'new-page', 'isNew', transform=convBool)
    >>> pl.isNew
    True
    '''
    value = xmlEl.get(xmlAttributeName) # find first
    if value is None:
        return

    if transform is not None:
        value = transform(value)

    if attributeName is None:
        attributeName = common.hyphenToCamelCase(xmlAttributeName)
    setattr(m21El, attributeName, value)
    
def _setAttributeFromTagText(m21El, xmlEl, tag, attributeName=None, transform=None):
    '''
    If xmlEl has a at least one element of tag==tag with some text. If
    it does, set the attribute either with the same name (with "foo-bar" changed to
    "fooBar") or with attributeName to the text contents.
    
    Pass a function or lambda function as `transform` to transform the value before setting it
    
    >>> from xml.etree.ElementTree import Element, SubElement
    >>> e = Element('accidental')
    >>> a = SubElement(e, 'alter')
    >>> a.text = '-2'

    >>> seta = musicxml.xmlToM21._setAttributeFromTagText
    >>> acc = pitch.Accidental()
    >>> seta(acc, e, 'alter')
    >>> acc.alter
    '-2'

    Transform the alter text to an int.

    >>> seta(acc, e, 'alter', transform=int)
    >>> acc.alter
    -2
    
    >>> e2 = Element('score-partwise')
    >>> a2 = SubElement(e2, 'movement-title')
    >>> a2.text = "Trout"
    >>> md = metadata.Metadata()
    >>> seta(md, e2, 'movement-title', 'movementName')
    >>> md.movementName
    'Trout'
    
    set a different attribute
    
    >>> seta(md, e2, 'movement-title', 'composer')
    >>> md.composer
    'Trout'
    '''
    matchEl = xmlEl.find(tag) # find first
    if matchEl is None:
        return
    value = matchEl.text
    if value in (None, ""):
        return 

    if transform is not None:
        value = transform(value)

    if attributeName is None:
        attributeName = common.hyphenToCamelCase(tag)
    setattr(m21El, attributeName, value)

#-------------------------------------------------------------------------------
class XMLParserBase(object):
    '''
    contains functions that could be called
    at multiple levels of parsing (Score, Part, Measure).
    '''
    mxAccidentalNameToM21 = {'quarter-sharp': 'half-sharp',
                             'three-quarters-sharp': 'one-and-a-half-sharp',
                             'quarter-flat': 'half-flat',
                             'three-quarters-flat': 'one-and-a-half-flat',
                             'flat-flat': 'double-flat',
                             'sharp-sharp': 'double-sharp',                                 
                             }

    
    def __init__(self):
        pass
    
    def setPosition(self, mxObject, m21Object):
        '''
        get positioning information for an object from
        x-position
        '''
        defaultX = mxObject.get('default-x')
        if defaultX is not None:
            m21Object.xPosition = defaultX
        # TODO: attr: default-y, relative-x, relative-y
        # TODO: standardize "positionVertical, etc.

    def xmlPrintToPageLayout(self, mxPrint, inputM21=None):
        '''
        Given an mxPrint object, set object data for 
        the print section of a layout.PageLayout object
    
        
        >>> from xml.etree.ElementTree import fromstring as El
        >>> MP = musicxml.xmlToM21.MeasureParser()

        
        >>> mxPrint = El('<print new-page="yes" page-number="5">' +
        ...    '    <page-layout><page-height>4000</page-height>' + 
        ...    '        <page-margins><left-margin>20</left-margin>' + 
        ...    '                 <right-margin>30.25</right-margin></page-margins>' + 
        ...    '</page-layout></print>')
    
        >>> pl = MP.xmlPrintToPageLayout(mxPrint)
        >>> pl.isNew
        True
        >>> pl.rightMargin
        30.25
        >>> pl.leftMargin
        20
        >>> pl.pageNumber
        5    
        >>> pl.pageHeight
        4000
        '''
        if inputM21 is None:
            pageLayout = layout.PageLayout()
        else:
            pageLayout = inputM21
        
        setb = _setAttributeFromAttribute
        setb(pageLayout, mxPrint, 'new-page', 'isNew', transform=xmlObjects.yesNoToBoolean)
        setb(pageLayout, mxPrint, 'page-number', transform=int)
    
        for x in mxPrint:
            if x.tag == 'page-layout':
                self.xmlPageLayoutToPageLayout(x, inputM21=pageLayout)
                break
    
        if inputM21 is None:
            return pageLayout
        
    def xmlPageLayoutToPageLayout(self, mxPageLayout, inputM21=None):
        '''
        get a PageLayout object from an mxPageLayout
        
        Called out from mxPrintToPageLayout because it
        is also used in the <defaults> tag
        '''
        if inputM21 is None:
            pageLayout = layout.PageLayout()
        else:
            pageLayout = inputM21

        seta = _setAttributeFromTagText
        
        seta(pageLayout, mxPageLayout, 'page-height', transform=_floatOrIntStr)
        seta(pageLayout, mxPageLayout, 'page-width', transform=_floatOrIntStr)
        
        #TODO -- record even, odd, both margins
        mxPageMargins = mxPageLayout.find('page-margins')
        if mxPageMargins is not None:
            for direction in ('top', 'bottom', 'left', 'right'):
                seta(pageLayout, mxPageMargins, direction + '-margin', transform=_floatOrIntStr)    
    
        if inputM21 is None:
            return pageLayout


    def xmlPrintToSystemLayout(self, mxPrint, inputM21=None):
        '''
        Given an mxPrint object, set object data
        
        >>> from xml.etree.ElementTree import fromstring as El
        >>> MP = musicxml.xmlToM21.MeasureParser()

        
        >>> mxPrint = El('<print new-system="yes">' +
        ...    '    <system-layout><system-distance>55</system-distance>' + 
        ...    '        <system-margins><left-margin>20</left-margin>' + 
        ...    '                 <right-margin>30.25</right-margin></system-margins>' + 
        ...    '</system-layout></print>')
        >>> sl = MP.xmlPrintToSystemLayout(mxPrint)
        >>> sl.isNew
        True
        >>> sl.rightMargin
        30.25
        >>> sl.leftMargin
        20
        >>> sl.distance
        55
        '''
        if inputM21 is None:
            systemLayout = layout.SystemLayout()
        else:
            systemLayout = inputM21
    
        setb = _setAttributeFromAttribute
        setb(systemLayout, mxPrint, 'new-system', 'isNew', xmlObjects.yesNoToBoolean)
            
        #mxSystemLayout = mxPrint.get('systemLayout')
        mxSystemLayout = mxPrint.find('system-layout') # blank
    
        if mxSystemLayout is not None:
            self.xmlSystemLayoutToSystemLayout(mxSystemLayout, inputM21=systemLayout)
    
        if inputM21 is None:
            return systemLayout


    def xmlSystemLayoutToSystemLayout(self, mxSystemLayout, inputM21=None):
        '''
        get a SystemLayout object from an <system-layout> element
        
        Called out from xmlPrintToSystemLayout because it
        is also used in the <defaults> tag
        '''
        if inputM21 is None:
            systemLayout = layout.SystemLayout()
        else:
            systemLayout = inputM21
    
        seta = _setAttributeFromTagText

        #TODO -- record even, odd, both margins
        mxSystemMargins = mxSystemLayout.find('system-margins')
        if mxSystemMargins is not None:
            for direction in ('top', 'bottom', 'left', 'right'):
                seta(systemLayout, mxSystemMargins, direction + '-margin', transform=_floatOrIntStr)    

        seta(systemLayout, mxSystemLayout, 'system-distance', 'distance', transform=_floatOrIntStr)
        seta(systemLayout, mxSystemLayout, 'top-system-distance', 'topDistance', transform=_floatOrIntStr)
        
        # TODO: system-dividers

        if inputM21 is None:
            return systemLayout

    def xmlStaffLayoutToStaffLayout(self, mxStaffLayout, inputM21=None):
        '''
        get a StaffLayout object from an <staff-layout> tag
        
        In music21, the <staff-layout> and <staff-details> are
        intertwined in a StaffLayout object.
        '''
        if inputM21 is None:
            staffLayout = layout.StaffLayout()
        else:
            staffLayout = inputM21
        seta = _setAttributeFromTagText
        seta(staffLayout, mxStaffLayout, 'staff-distance', 'distance', transform=_floatOrIntStr)
        #ET.dump(mxStaffLayout)

        data = mxStaffLayout.get('number')
        if data is not None:
            staffLayout.staffNumber = int(data)
            
        if hasattr(self, 'staffLayoutObjects'):
            self.staffLayoutObjects.append(staffLayout)

        
        if inputM21 is None:
            return staffLayout
    

class PartGroup():
    '''
    Small helper class for keeping track of part-groups from XML since they
    are converted to StaffGroup spanners much later.
    '''
    def __init__(self, mxPartGroup):
        self.mxPartGroup = mxPartGroup
        self.partGroupIds = []
        number = mxPartGroup.get('number')
        if number is not None: 
            number = int(number)
        else:
            number = 1
        self.number = number
        
    def add(self, partGroupId):
        self.partGroupIds.append(partGroupId)
    
#-------------------------------------------------------------------------------

class MusicXMLImporter(XMLParserBase):
    '''
    Object for importing .xml, .mxl, .musicxml, MusicXML files into music21.
    '''
    def __init__(self):
        XMLParserBase.__init__(self)
        self.xmlText = None
        self.xmlFilename = None
        self.xmlRoot = None
        self.stream = stream.Score()
        
        self.definesExplicitSystemBreaks = False
        self.definesExplicitPageBreaks = False

        self.spannerBundle = self.stream.spannerBundle
        self.partIdDict = {}
        self.m21PartObjectsById = {}
        self.partGroupList = []
        self.parts = []
        
        self.musicXmlVersion = "1.0"
    
    def scoreFromFile(self, filename):
        '''
        main program: opens a file given by filename and returns a complete
        music21 Score from it.
        '''
        # load filename into text
        self.readFile(filename)
        #self.parseXMLText()
        return self.stream
    
    def readFile(self, filename):
        etree = ET.parse(filename)
        self.xmlRoot = etree.getroot()
        if self.xmlRoot.tag != 'score-partwise':
            raise MusicXMLImportException("Cannot parse MusicXML files not in score-partwise. " + 
                                          "Root tag was '{0}'".format(self.xmlRoot.tag))
        self.xmlRootToScore(self.xmlRoot, self.stream)
    
    def parseXMLText(self):
        sio = six.StringIO(self.xmlText)
        try:
            etree = ET.parse(sio)
            self.xmlRoot = etree.getroot()
        except ET.ParseError:
            try:
                self.xmlRoot = ET.XML(self.xmlText)
            except ET.ParseError:
                raise # try to do something better here...
        if self.xmlRoot.tag != 'score-partwise':
            raise MusicXMLImportException("Cannot parse MusicXML files not in score-partwise. " + 
                                          "Root tag was '{0}'".format(self.xmlRoot.tag))
        self.xmlRootToScore(self.xmlRoot, self.stream)

    def xmlRootToScore(self, mxScore, inputM21=None):
        '''
        parse an xml file into a Score() object.
        '''
        if inputM21 is None:
            s = self.Score()
        else:
            s = inputM21
        
        mxVersion = mxScore.get('version')
        if mxVersion is None:
            mxVersion = "1.0"
        self.musicXmlVersion = mxVersion
        
        md = self.xmlMetadata(mxScore)
        s._insertCore(0, md)
        
        mxDefaults = mxScore.find('defaults')
        if mxDefaults is not None:
            scoreLayout = self.xmlDefaultsToScoreLayout(mxDefaults)
            s._insertCore(0, scoreLayout)

        for mxCredit in mxScore.findall('credit'):
            credit = self.xmlCreditToTextBox(mxCredit)
            s._insertCore(0, credit)

        self.parsePartList(mxScore)
        for p in mxScore.findall('part'):
            partId = p.get('id')
            part = self.xmlPartToPart(p, self.partIdDict[partId])
            if part is not None: # for instance, in partStreams
                s._insertCore(0.0, part)
                self.m21PartObjectsById[partId] = part


        self.partGroups()

        # copy spanners that are complete into the Score. 
        # basically just the StaffGroups for now.
        rm = []
        for sp in self.spannerBundle.getByCompleteStatus(True):
            self.stream._insertCore(0, sp)
            rm.append(sp)
        # remove from original spanner bundle
        for sp in rm:
            self.spannerBundle.remove(sp)

        s.elementsChanged()
        s.definesExplicitSystemBreaks = self.definesExplicitSystemBreaks
        s.definesExplicitPageBreaks = self.definesExplicitPageBreaks
        for p in s.parts:
            p.definesExplicitSystemBreaks = self.definesExplicitSystemBreaks
            p.definesExplicitPageBreaks = self.definesExplicitPageBreaks
        
        if inputM21 is None:
            return s

    def xmlPartToPart(self, mxPart, partIdDict):
        parser = PartParser(mxPart, mxPartInfo=partIdDict, parent=self)
        parser.parse()
        if parser.appendToScoreAfterParse is True:
            return parser.stream
        else:
            return None

    def parsePartList(self, mxScore):
        '''
        Parses the <part-list> tag and adds
        <score-part> entries into self.partIdDict[partId]
        and adds them to any open <part-group> entries,
        stored as PartGroup objects in self.partGroupList
        
        '''
        mxPartList = mxScore.find('part-list')
        if mxPartList is None:
            return
        openPartGroups = []
        for partListElement in mxPartList:
            if partListElement.tag == 'score-part':
                partId = partListElement.get('id')
                self.partIdDict[partId] = partListElement
                for pg in openPartGroups:
                    pg.add(partId)
            elif partListElement.tag == 'part-group':
                if partListElement.get('type') == 'start':
                    pg = PartGroup(partListElement)
                    self.partGroupList.append(pg)
                    openPartGroups.append(pg)
                elif partListElement.get('type') == 'stop':
                    number = partListElement.get('number')
                    if number is not None: 
                        number = int(number)
                    else:
                        number = 1
                    opgTemp = []
                    for pg in openPartGroups:
                        if pg.number != number:
                            opgTemp.append(pg)
                    openPartGroups = opgTemp
        
    def xmlCreditToTextBox(self, mxCredit):
        '''Convert a MusicXML credit to a music21 TextBox
            
        >>> import xml.etree.ElementTree as ET
        >>> credit = ET.fromstring('<credit page="2"><credit-words>Testing</credit-words></credit>')
    
        >>> MI = musicxml.xmlToM21.MusicXMLImporter()
        >>> tb = MI.xmlCreditToTextBox(credit)
        >>> tb.page
        2
        >>> tb.content
        'Testing'
        
        OMIT_FROM_DOCS
        
        Capella generates empty credit-words
        
        >>> credit = ET.fromstring('<credit><credit-words/></credit>')
        >>> tb = MI.xmlCreditToTextBox(credit)
        >>> tb
        <music21.text.TextBox "">
        '''
        tb = text.TextBox()
        pageNum = mxCredit.get('page')
        if pageNum is None:
            pageNum = 1
        else:
            pageNum = int(pageNum)
        tb.page = pageNum
        content = []
        for cw in mxCredit.findall('credit-words'):
            if cw.text not in (None, ""):
                content.append(cw.text)
        if len(content) == 0: # no text defined
            tb.content = ""
            return tb # capella generates empty credit-words
            #raise MusicXMLImportException('no credit words defined for a credit tag')
        tb.content = '\n'.join(content) # join with \n
    
        cw1 = mxCredit.find('credit-words')
        # take formatting from the first, no matter if multiple are defined
        tb.positionVertical = cw1.get('default-y')
        tb.positionHorizontal = cw1.get('default-x')
        tb.justify = cw1.get('justify')
        tb.style = cw1.get('font-style')
        tb.weight = cw1.get('font-weight')
        tb.size = cw1.get('font-size')
        tb.alignVertical = cw1.get('valign')
        tb.alignHorizontal = cw1.get('halign')        
        # TODO: credit type
        # TODO: link
        # TODO: bookmark
        # TODO: credit-image
        
        return tb
        
    def xmlDefaultsToScoreLayout(self, mxDefaults, inputM21=None):
        '''
        Convert a <defaults> tag to a :class:`~music21.layout.ScoreLayout` 
        object
        '''
        if inputM21 is None:
            scoreLayout = layout.ScoreLayout()
        else:
            scoreLayout = inputM21

        seta = _setAttributeFromTagText

        mxScaling = mxDefaults.find('scaling')
        if mxScaling is not None:
            seta(scoreLayout, mxScaling, 'millimeters', 'scalingMillimeters', transform=_floatOrIntStr)
            seta(scoreLayout, mxScaling, 'tenths', 'scalingTenths', transform=_floatOrIntStr)
    
        mxPageLayout = mxDefaults.find('page-layout')
        if mxPageLayout is not None:
            scoreLayout.pageLayout = self.xmlPageLayoutToPageLayout(mxPageLayout)
        mxSystemLayout = mxDefaults.find('system-layout')
        if mxSystemLayout is not None:
            scoreLayout.systemLayout = self.xmlSystemLayoutToSystemLayout(mxSystemLayout)
        for mxStaffLayout in mxDefaults.findall('staff-layout'):
            staffLayout = self.xmlStaffLayoutToStaffLayout(mxStaffLayout)
            scoreLayout.staffLayoutList.append(staffLayout)
        
        # TODO: appearance
        # TODO: music-font
        # TODO: word-font
        # TODO: lyric-font
        # TODO: lyric-language
        
        return scoreLayout


    def partGroups(self):
        '''
        set StaffGroup objects from the <part-group> tags.
        '''
        seta = _setAttributeFromTagText
        for pgObj in self.partGroupList:
            staffGroup = layout.StaffGroup()
            for partId in pgObj.partGroupIds:
                # get music21 part from partIdDictionary
                try:
                    staffGroup.addSpannedElements(self.m21PartObjectsById[partId])
                except KeyError as ke:
                    foundOne = False
                    for partIdTest in sorted(self.m21PartObjectsById):
                        if partIdTest.startswith(partId + '-Staff'):
                            staffGroup.addSpannedElements(self.m21PartObjectsById[partIdTest])
                            foundOne = True
                                                
                    if foundOne is False:
                        raise MusicXMLImportException("Cannot find part in m21PartIdDictionary:"
                                + " %s \n   Full Dict:\n   %r " % (ke, self.m21PartObjectsById))
            partGroup = pgObj.mxPartGroup
            seta(staffGroup, partGroup, 'group-name', 'name')
            # TODO: group-name-display
            seta(staffGroup, partGroup, 'group-abbreviation', 'abbreviation')
            # TODO: group-abbreviation-display
            if partGroup.find('group-symbol') is not None:            
                seta(staffGroup, partGroup, 'group-symbol', 'symbol')
            else:
                staffGroup.symbol = 'brace' # MusicXML default
            
            seta(staffGroup, partGroup, 'group-barline', 'barTogether')    
            # TODO: group-time
            # TODO: editorial
            staffGroup.completeStatus = True
            self.spannerBundle.append(staffGroup)
            #self.stream._insertCore(0, staffGroup)
        self.stream.elementsChanged()
                

        
    def xmlMetadata(self, el=None, inputM21=None):
        '''
        Converts part of the root element into a metadata object
        
        Supported: work-title, work-number, opus, movement-number,
        movement-title, identification (creator)
        
        Not supported: rights, encoding, source, relation, miscellaneous
        '''
        if el is None:
            el = self.root

        if inputM21 is None:
            md = metadata.Metadata()
        else:
            md = inputM21
            
        seta = _setAttributeFromTagText
        #work
        work = el.find('work')
        if work is not None:
            seta(md, work, 'work-title', 'title')
            seta(md, work, 'work-number', 'number')
            seta(md, work, 'opus', 'opusNumber')
        
        seta(md, el, 'movement-number')
        seta(md, el, 'movement-title', 'movementName')
        
        identification = el.find('identification')
        if identification is not None:
            for creator in identification.findall('creator'):
                c = self.creatorToContributor(creator)
                md.addContributor(c)
            encoding = identification.find('encoding')
            if encoding is not None:
                for supports in encoding.findall('supports'):
                    attr = supports.get('attribute')
                    value = supports.get('value')
                    if (attr, value) == ('new-system', 'yes'):
                        self.definesExplicitSystemBreaks = True
                    elif (attr, value) == ('new-page', 'yes'):
                        self.definesExplicitPageBreaks = True
        
        # TODO: rights
        # TODO: encoding (incl. supports)
        # TODO: source
        # TODO: relation
        # TODO: miscellaneous
        if inputM21 is None:
            return md
        
    def creatorToContributor(self, creator, inputM21=None):
        '''
        Given an <creator> tag, fill the necessary parameters of a Contributor.
    
        >>> import xml.etree.ElementTree as ET
        >>> creator = ET.fromstring('<creator type="composer">Beethoven, Ludwig van</creator>')
    
        >>> MI = musicxml.xmlToM21.MusicXMLImporter()
        >>> c = MI.creatorToContributor(creator)
        >>> c
        <music21.metadata.primitives.Contributor object at 0x...>
        >>> c.role
        'composer'
        >>> c.name
        'Beethoven, Ludwig van'
        
        Pass in a Contributor object and set it...
        
        >>> c2 = metadata.Contributor()
        >>> MI.creatorToContributor(creator, c2)
        >>> c2.role
        'composer'
        '''
        if inputM21 is None:
            c = metadata.Contributor()
        else:
            c = inputM21
            
        creatorType = creator.get('type')
        if (creatorType is not None and 
            creatorType in metadata.Contributor.roleNames):
            c.role = creatorType
        
        creatorText = creator.text
        if creatorText is not None:
            c.name = creatorText.strip()
        if inputM21 is None:
            return c        
        

#------------------------------------------------------------------------------
class PartParser(XMLParserBase):
    '''
    parser to work with a single <part> tag.
    
    called out for multiprocessing potential in future
    '''
    def __init__(self, mxPart=None, mxPartInfo=None, parent=None):
        XMLParserBase.__init__(self)
        self.mxPart = mxPart
        self.mxPartInfo = mxPartInfo
        if mxPart is not None:
            self.partId = mxPart.get('id')
        else:
            self.partId = ""
        self._parent = common.wrapWeakref(parent)
        if parent is not None:
            self.spannerBundle = parent.spannerBundle
        else:
            self.spannerBundle = spanner.SpannerBundle()
        self.stream = stream.Part()
        self.atSoundingPitch = True
        
        self.staffReferenceList = []
        
        self.lastTimeSignature = None
        self.lastTransposition = None  # may change at measure boundaries
        self.lastMeasureWasShort = False
        self.lastMeasureOffset = 0.0
        
        self.maxStaves = 1
        
        self.lastMeasureNumber = 0
        self.lastNumberSuffix = None
        
        self.activeInstrument = None
        self.firstMeasureParsed = False # has the first measure been parsed yet?
        self.activeAttributes = None # divisions, clef, etc.        
        self.lastDivisions = None
        
        self.appendToScoreAfterParse = True

    def _getParent(self):
        return common.unwrapWeakref(self._parent)

    parent = property(_getParent)
    
    def parse(self):
        self.parsePartInfo()
        self.parseMeasures()
        self.stream.atSoundingPitch = self.atSoundingPitch
    
        # TODO: this does not work with voices; there, Spanners 
        # will be copied into the Score 

        # copy spanners that are complete into the part, as this is the 
        # highest level container that needs them
        rm = []
        for sp in self.spannerBundle.getByCompleteStatus(True):
            self.stream._insertCore(0, sp)
            rm.append(sp)
        # remove from original spanner bundle
        for sp in rm:
            self.spannerBundle.remove(sp)
        # s is the score; adding the part to the score
        self.stream.elementsChanged()

        
        if self.maxStaves > 1:
            self.separateOutPartStaves()
        else:
            self.stream.addGroupForElements(self.partId) # set group for components 
            self.stream.groups.append(self.partId) # set group for stream itself
    
    def parseMeasures(self):
        part = self.stream
        for mxMeasure in self.mxPart.iterfind('measure'):
            self.xmlMeasureToMeasure(mxMeasure)
        part.elementsChanged()
    
    def separateOutPartStaves(self):
        '''
        Take a Part with multiple staves and make them a set of PartStaff objects.
        '''
        # get staves will return a number, between 1 and count
        #for staffCount in range(mxPart.getStavesCount()):
        for staffNumber in self._getUniqueStaffKeys():
            partStaffId = '%s-Staff%s' % (self.partId, staffNumber)
            #environLocal.printDebug(['partIdStaff', partIdStaff, 'copying streamPart'])
            # this deepcopy is necessary, as we will remove components
            # in each staff that do not belong
            
            # TODO: Do n-1 deepcopies, instead of n, since the last PartStaff can just remove from the original Part
            streamPartStaff = copy.deepcopy(self.stream)
            # assign this as a PartStaff, a subclass of Part
            streamPartStaff.__class__ = stream.PartStaff
            streamPartStaff.id = partStaffId
            # remove all elements that are not part of this staff
            mStream = streamPartStaff.getElementsByClass('Measure')
            for i, staffReference in enumerate(self.staffReferenceList):
                staffExclude = self._getStaffExclude(staffReference, staffNumber)
                if len(staffExclude) > 0:
                    m = mStream[i]
                    for eRemove in staffExclude:
                        for eMeasure in m:
                            if eMeasure.derivation.origin is eRemove and eMeasure.derivation.method == '__deepcopy__':
                                #print("removing element", eMeasure, " from ", m)
                                m.remove(eMeasure)
                                break
                        for v in m.voices:
                            v.remove(eRemove)
                            for eVoice in v.elements:
                                if eVoice.derivation.origin is eRemove and eVoice.derivation.method == '__deepcopy__':
                                    #print("removing element", eRemove, " from ", m, ' voice', v)
                                    v.remove(eVoice)
                # after adjusting voices see if voices can be reduced or
                # removed
                #environLocal.printDebug(['calling flattenUnnecessaryVoices: voices before:', len(m.voices)])
                m.flattenUnnecessaryVoices(force=False, inPlace=True)
                #environLocal.printDebug(['calling flattenUnnecessaryVoices: voices after:', len(m.voices)])
            # TODO: copying spanners may have created orphaned
            # spanners that no longer have valid connections
            # in this part; should be deleted
            streamPartStaff.addGroupForElements(partStaffId)
            streamPartStaff.groups.append(partStaffId)
            streamPartStaff.elementsChanged()
            self.parent.stream._insertCore(0, streamPartStaff)
            self.parent.m21PartObjectsById[partStaffId] = streamPartStaff
        
        self.appendToScoreAfterParse = False
        self.parent.stream.elementsChanged()
    
    def _getStaffExclude(self, staffReference, targetKey):
        '''
        Given a staff reference dictionary, remove and combine in a list all elements that 
        are NOT part of the given key. Thus, return a list of all entries to remove.
        It keeps those elements under staff key None (common to all) and 
        those under given key. This then is the list of all elements that should be deleted.
        '''
        post = []
        for k in staffReference:
            if k in (None, 'None') or targetKey in (None, 'None'):
                continue
            elif int(k) == int(targetKey):
                continue
            post += staffReference[k]
        return post

            
    def _getUniqueStaffKeys(self):
        '''
        Given a list of staffReference dictionaries, 
        collect and return a list of all unique keys except None
        '''
        post = []
        for staffReference in self.staffReferenceList:
            for k in staffReference:
                if k not in (None, 'None') and k not in post:
                    post.append(k)
        post.sort()
        return post
           
    def measureParsingError(self, mxMeasure, e):
        measureNumber = "unknown"
        try:
            measureNumber = mxMeasure.get('number')
        except (AttributeError, NameError, ValueError):
            pass
        # see http://stackoverflow.com/questions/6062576/adding-information-to-a-python-exception
        execInfoTuple = sys.exc_info()
        if hasattr(e, 'message'):
            emessage = e.message
        else:
            emessage = execInfoTuple[0].__name__ + " : " #+ execInfoTuple[1].__name__
        unused_message = "In measure (" + measureNumber + "): " + emessage
        raise(e)
        #raise type(e)(pprint.pformat(traceback.extract_tb(execInfoTuple[2])))
    
    def xmlMeasureToMeasure(self, mxMeasure):
        parser = MeasureParser(mxMeasure, parent=self)
        try:
            parser.parse()
        except Exception as e: # pylint: disable=broad-except
            self.measureParsingError(mxMeasure, e)
        
        if parser.staves > self.maxStaves:
            self.maxStaves = parser.staves
            
        if parser.transposition is not None:
            #environLocal.warn(["Got a transposition,", parser.transposition])
            if (self.lastTransposition is None 
                and self.firstMeasureParsed is False
                and self.activeInstrument is not None):
                self.activeInstrument.transposition = parser.transposition
                #environLocal.warn("Put trans on active instrument")
            elif self.activeInstrument is not None:
                # will this catch something like Bb clarinet to Bb Soprano Sax to Eb clarinet? 
                newInst = copy.deepcopy(self.activeInstrument)
                newInst.transposition = parser.transposition 
                #environLocal.warn("Put trans on new instrument")
                self.activeInstrument = newInst
                self.stream._insertCore(self.lastMeasureOffset, newInst)
            else:
                environLocal.warn("Received a transposition tag, but nowhere to put it!")
                
            self.lastTransposition = parser.transposition
            self.atSoundingPitch = False
        self.firstMeasureParsed = True
        self.staffReferenceList.append(parser.staffReference)
        if parser.measureNumber != self.lastMeasureNumber:
            # we do this check so that we do not compound suffixes, i.e.:
            # 23, 23.X1, 23.X1X2, 23.X1X2X3
            # and instead just do:
            # 23, 23.X1, 23.X2, etc.
            self.lastMeasureNumber = parser.measureNumber
            self.lastNumberSuffix = parser.numberSuffix      
        m = parser.stream
        if m.timeSignature is not None:
            self.lastTimeSignature = m.timeSignature
        elif self.lastTimeSignature is None and m.timeSignature is None:
            # if no time signature is defined, need to get a default
            ts = meter.TimeSignature()
            self.lastTimeSignature = ts
        
        if parser.fullMeasureRest is True:
            r1 = m.getElementsByClass('Rest')[0]
            if (r1.duration.quarterLength == 4.0 
                    and r1.duration.quarterLength != self.lastTimeSignature.barDuration.quarterLength):
                r1.duration.quarterLength = self.lastTimeSignature.barDuration.quarterLength
                m.elementsChanged()            

        self.stream._insertCore(self.lastMeasureOffset, m)
        self.adjustTimeAttributesFromMeasure(m)
        
        return m
        
    def adjustTimeAttributesFromMeasure(self, m):
        # note: we cannot assume that the time signature properly
        # describes the offsets w/n this bar. need to look at 
        # offsets within measure; if the .highestTime value is greater
        # use this as the next offset

        mHighestTime = m.highestTime
        #environLocal.warn([self.lastTimeSignature])
        #environLocal.warn([self.lastTimeSignature.barDuration])
        
        lastTimeSignatureQuarterLength = self.lastTimeSignature.barDuration.quarterLength

        if mHighestTime >= lastTimeSignatureQuarterLength:
            mOffsetShift = mHighestTime

        elif mHighestTime == 0.0 and len(m.flat.notesAndRests) == 0:
            ## this routine fixes a bug in PDFtoMusic and other MusicXML writers
            ## that omit empty rests in a Measure.  It is a very quick test if
            ## the measure has any notes.  Slower if it does not.
            r = note.Rest()
            r.duration.quarterLength = lastTimeSignatureQuarterLength
            m.insert(0.0, r)
            mOffsetShift = lastTimeSignatureQuarterLength

        else: # use time signature
            # for the first measure, this may be a pickup
            # must detect this when writing, as next measures offsets will be 
            # incorrect
            if self.lastMeasureOffset == 0.0:
                # cannot get bar duration proportion if cannot get a ts
                if m.barDurationProportion() < 1.0:
                    m.padAsAnacrusis()
                    #environLocal.printDebug(['incompletely filled Measure found on musicxml import; interpreting as a anacrusis:', 'padingLeft:', m.paddingLeft])
                mOffsetShift = mHighestTime
                
            # assume that, even if measure is incomplete, the next bar should
            # start at the duration given by the time signature, not highestTime
            ### no...let's not do this...
            else:
                mOffsetShift = mHighestTime #lastTimeSignatureQuarterLength
                if self.lastMeasureWasShort is True:
                    if m.barDurationProportion() < 1.0:
                        m.padAsAnacrusis() # probably a pickup after a repeat or phrase boundary or something
                        self.lastMeasureWasShort = False
                else:
                    if mHighestTime < lastTimeSignatureQuarterLength:
                        self.lastMeasureWasShort = True
                    else:
                        self.lastMeasureWasShort = False
                        
        self.lastMeasureOffset += mOffsetShift
        
        
    def parsePartInfo(self):
        instrumentObj = self.getDefaultInstrument()
        #self.firstInstrumentObject = instrumentObj # not used.
        if instrumentObj.bestName() is not None:
            self.stream.id = instrumentObj.bestName()
        self.activeInstrument = instrumentObj
        self.stream._insertCore(0.0, instrumentObj) # add instrument at zero offset
        
    def getDefaultInstrument(self, mxPartInfo=None):
        r'''
        >>> scorePart = (r'<score-part id="P4"><part-name>Bass</part-name>' + 
        ...     '<part-abbreviation>B.</part-abbreviation>' +
        ...     '<score-instrument id="P4-I4">' +
        ...     '    <instrument-name>Instrument 4</instrument-name>' +
        ...     '</score-instrument>' +
        ...     '<midi-instrument id="P4-I4">' +
        ...     '   <midi-channel>4</midi-channel>' +
        ...     '<midi-program>1</midi-program>' +
        ...     '</midi-instrument>' +
        ...     '</score-part>')
        >>> from xml.etree.ElementTree import fromstring as EL
        >>> PP = musicxml.xmlToM21.PartParser()
        
        >>> mxPartInfo = EL(scorePart)
        >>> i = PP.getDefaultInstrument(mxPartInfo)
        >>> i.partName
        'Bass'
        >>> i.partAbbreviation
        'B.'
        
        '''
        if mxPartInfo is None:
            mxInfo = self.mxPartInfo
        else:
            mxInfo = mxPartInfo
        
        def _clean(badStr):
            # need to remove badly-formed strings
            if badStr is None:
                return None
            badStr = badStr.strip()
            goodStr = badStr.replace('\n', ' ')
            return goodStr
        
        def _adjustMidiData(mc):
            return int(mc) - 1
        
        seta = _setAttributeFromTagText

        #print(ET.tostring(mxInfo, encoding='unicode'))
        i = instrument.Instrument()
        i.partId = self.partId
        i.groups.append(self.partId)

        # put part info into the instrument object and retrieve it later...
        seta(i, mxInfo, 'part-name', transform=_clean)
        # TODO: partNameDisplay
        seta(i, mxInfo, 'part-abbreviation', transform=_clean)
        # TODO: partAbbreviationDisplay        
        # TODO: groups
        
        # for now, just get first instrument
        # TODO: get all instruments!
        mxScoreInstrument = mxInfo.find('score-instrument')
        if mxScoreInstrument is not None:
            seta(i, mxScoreInstrument, 'instrument-name', transform=_clean)
            seta(i, mxScoreInstrument, 'instrument-abbreviation', transform=_clean)
        # TODO: instrument-sound
        # TODO: solo / ensemble
        # TODO: virtual-instrument
        # TODO: store id attribute somewhere
        
        # for now, just get first midi instrument
        # TODO: get all
        # TODO: midi-device
        mxMIDIInstrument = mxInfo.find('midi-instrument')
        # TODO: midi-name
        # TODO: midi-bank transform=_adjustMidiData
        # TODO: midi-unpitched
        # TODO: midi-volume
        # TODO: pan
        # TODO: elevation
        # TODO: store id attribute somewhere
        if mxMIDIInstrument is not None:
            seta(i, mxMIDIInstrument, 'midi-program', transform=_adjustMidiData)
            seta(i, mxMIDIInstrument, 'midi-channel', transform=_adjustMidiData)

        # TODO: reclassify 
        return i
#------------------------------------------------------------------------------
class MeasureParser(XMLParserBase):
    '''
    parser to work with a single <measure> tag.
    
    called out for simplicity
    '''
    attributeTagsToMethods = {'time': 'handleTimeSignature',
                     'clef': 'handleClef',
                     'key': 'handleKeySignature',
                     'staff-details': 'handleStaffDetails',
                     }
    musicDataMethods = {'note': 'xmlToNote',
                        'backup': 'xmlBackup',
                        'forward': 'xmlForward',
                        'direction': 'xmlDirection',
                        'attributes': 'parseAttributesTag',
                        'harmony': 'xmlHarmony',
                        'figured-bass': None,
                        'sound': None,
                        'barline': 'xmlBarline',
                        'grouping': None,
                        'link': None,
                        'bookmark': None,    
                        # TODO: clefs??? 
                        # Note: <print> is handled separately...                   
                        }
    # TODO: editorial, i.e., footnote and level
    # TODO: staves (num staves)
    # TODO: part-symbol
    # TODO: directive DEPRECATED since MusicXML 2.0
    # TODO: measure-style
    def __init__(self, mxMeasure=None, parent=None):
        XMLParserBase.__init__(self)
        
        self.mxMeasure = mxMeasure
        self.mxMeasureElements = []
        
        self.parent = parent # PartParser
        self.transposition = None
        if parent is not None:
            self.spannerBundle = parent.spannerBundle
        else:
            self.spannerBundle = spanner.SpannerBundle()
            
        self.staffReference = {}
        self.useVoices = False
        self.voiceIndices = set()
        self.staves = 1
        
        self.activeAttributes = None
        self.attributesAreInternal = True
        
        self.measureNumber = None
        self.numberSuffix = None
        
        self.divisions = None
        
        self.staffLayoutObjects = []
        self.stream = stream.Measure()
        
        self.mxNoteList = [] # for accumulating notes in chords
        self.mxLyricList = [] # for accumulating lyrics assigned to chords
        self.nLast = None # for adding notes to spanners.
        self.chordVoice = None # Sibelius 7.1 only puts a <voice> tag on the
                        # first note of a chord, so we need to make sure
                        # that we keep track of the last voice...
        self.fullMeasureRest = False
        self.restAndNoteCount = {'rest': 0, 'note': 0} # for keeping track
                        # of full-measureRests.
        
        self.parseIndex = 0
        self.offsetMeasureNote = 0.0
    
    def getStaffNumberStr(self, mxObjectOrNumber):
        '''
        gets a string representing a staff number, or None
        from an mxObject or a number...
        '''
        #environLocal.printDebug(['addToStaffReference(): called with:', music21Object])
        if common.isListLike(mxObjectOrNumber):
            if len(mxObjectOrNumber) > 0:
                mxObjectOrNumber = mxObjectOrNumber[0] # if a chord, get the first components
            else: # if an empty list
                environLocal.printDebug(['got an mxObject as an empty list', mxObjectOrNumber])
                return
        # add to staff reference
        try:
            staffObject = mxObjectOrNumber.find('staff')
        except AttributeError:
            staffObject = None
            
        if staffObject is not None:
            try:
                k = staffObject.text.strip()
            except AttributeError:
                k = None
        else:
            k = None
        # some objects store staff assignment simply as number
        if k is None:
            try:
                k = mxObjectOrNumber.get('number')
            except AttributeError: # a normal number
                k = mxObjectOrNumber

        return k
        
    def addToStaffReference(self, mxObjectOrNumber, m21Object):
        '''
        Utility routine for importing musicXML objects; 
        here, we store a reference to the music21 object in a dictionary, 
        where keys are the staff values. Staff values may be None, 1, 2, etc.
        '''
        staffReference = self.staffReference
        staffKey = self.getStaffNumberStr(mxObjectOrNumber) # a str of a number or None
        if staffKey not in staffReference:
            staffReference[staffKey] = []
        staffReference[staffKey].append(m21Object)
    
    def insertCoreAndRef(self, offset, mxObjectOrNumber, m21Object):
        self.addToStaffReference(mxObjectOrNumber, m21Object)
        self.stream._insertCore(offset, m21Object)
        
    def parse(self):
        # handle <print> before anything else, because it can affect
        # attributes!
        for mxPrint in self.mxMeasure.findall('print'):
            self.xmlPrint(mxPrint)
        
        self.parseMeasureAttributes()
        self.updateVoiceInformation()
        self.mxMeasureElements = list(self.mxMeasure) # for grabbing next note
        for i, mxObj in enumerate(self.mxMeasureElements):
            self.parseIndex = i # for grabbing next note
            if mxObj.tag in self.musicDataMethods:
                methName = self.musicDataMethods[mxObj.tag]
                if methName is not None:
                    meth = getattr(self, methName)
                    meth(mxObj)
        
        if self.useVoices is True:
            for v in self.stream.voices:
                if len(v) > 0: # do not bother with empty voices
                    v.makeRests(inPlace=True)
                v.elementsChanged()
        self.stream.elementsChanged()
        
        if (self.restAndNoteCount['rest'] == 1
                and self.restAndNoteCount['note'] == 0):
            # TODO: do this on a per voice basis.
            self.fullMeasureRest = True 
        
    def xmlBackup(self, mxObj):
        change = float(mxObj.find('duration').text.strip()) / self.divisions
        self.offsetMeasureNote -= change     

    def xmlForward(self, mxObj):
        change = float(mxObj.find('duration').text.strip()) / self.divisions
        self.offsetMeasureNote += change     

    def xmlPrint(self, mxPrint):
        '''
        <print> handles changes in pages, numbering, layout,
        etc. so can generate PageLayout, SystemLayout, or StaffLayout
        objects.
        
        Should also be able to set measure attributes on self.stream
        '''
        def hasPageLayout(mxPrint):
            if mxPrint.get('new-page') not in (None, 'no'):
                return True
            if mxPrint.get('page-number') is not None:
                return True
            if mxPrint.find('page-layout') is not None:
                return True            
            return False
        
        def hasSystemLayout(mxPrint):
            if mxPrint.get('new-system') not in (None, 'no'):
                return True
            if mxPrint.find('system-layout') is not None:
                return True            
            return False
        
        addPageLayout = hasPageLayout(mxPrint)
        addSystemLayout = hasSystemLayout(mxPrint)
        addStaffLayout = False if mxPrint.find('staff-layout') is None else True
        
        #--- now we know what we need to add, add em
        m = self.stream
        if addPageLayout is True:
            pl = self.xmlPrintToPageLayout(mxPrint)
            m._insertCore(0.0, pl) # should this be parserOffset?
        if addSystemLayout is True or addPageLayout is False:
            sl = self.xmlPrintToSystemLayout(mxPrint)
            m._insertCore(0.0, sl)
        if addStaffLayout is True:
            # assumes addStaffLayout is there...
            slFunc = self.xmlStaffLayoutToStaffLayout
            stlList = [slFunc(mx) for mx in mxPrint.iterfind('staff-layout')]
            # If bugs incorporate Ariza additional checks, but
            # I think that we don't want to add to an existing staffLayoutObject
            # so that staff distance can change.
            for stl in stlList:
                if stl is None or stl.staffNumber is None:
                    continue # sibelius likes to give empty staff layouts!
                self.insertCoreAndRef(0.0, str(stl.staffNumber), stl)
        m.elementsChanged()
        # TODO: measure-layout -- affect self.stream
        # TODO: measure-numbering
        # TODO: part-name-display
        # TODO: part-abbreviation display
        # TODO: print-attributes: staff-spacing, blank-page; skip deprecated staff-spacing
        
    def xmlToNote(self, mxNote):
        '''
        handles everything for creating a Note or Rest or Chord
        '''
        try:
            mxObjNext = self.mxMeasureElements[self.parseIndex + 1]
            if mxObjNext.tag == 'note' and mxObjNext.find('chord') is not None:
                nextNoteIsChord = True
            else:
                nextNoteIsChord = False
        except IndexError: # last note in measure
            nextNoteIsChord = False

        # TODO: Cue notes (no sounding tie)

        # the first note of a chord is not identified directly; only
        # by looking at the next note can we tell if we have the first
        # note of a chord
        isChord = False
        isRest = False
        # TODO: Unpitched
        
        offsetIncrement = 0.0

        if mxNote.find('rest') is not None: # it is a note
            isRest = True
        if mxNote.find('chord') is not None:
            isChord = True

        if isRest is True:
            self.restAndNoteCount['rest'] += 1
        elif isChord is False: 
            self.restAndNoteCount['note'] += 1
        # do not count extra pitches in chord as note.
        # it might be the first note of the chord...
        if nextNoteIsChord:
            isChord = True # first note of chord is not identified.
            voiceOfChord = mxNote.find('voice')
            if voiceOfChord is not None:
                vIndex = voiceOfChord.text
                try:
                    vIndex = int(vIndex)
                except ValueError:
                    pass
                self.chordVoice = vIndex

        if isChord is True: # and isRest is False...?            
            self.mxNoteList.append(mxNote)
            # store lyrics for latter processing
            for mxLyric in mxNote.findall('lyric'):
                self.mxLyricList.append(mxLyric)
        elif isChord is False and isRest is False: # normal note...
            self.restAndNoteCount['note'] += 1
            try:
                n = self.xmlToSimpleNote(mxNote)
            except MusicXMLImportException as strerror:
                raise MusicXMLImportException('cannot translate note in measure {0}: {1}'.format(self.measureNumber, strerror))
        else: # its a rest
            self.restAndNoteCount['rest'] += 1
            n = self.xmlToRest(mxNote)

        if isChord is False: # normal note or rest...
            self.updateLyricsFromList(n, mxNote.findall('lyric'))            
            self.addToStaffReference(mxNote, n)
            self.addNoteToMeasureOrVoice(mxNote, n)        
            offsetIncrement = n.duration.quarterLength
            self.nLast = n # update

            

        # if we we have notes in the note list and the next
        # note either does not exist or is not a chord, we 
        # have a complete chord
        if len(self.mxNoteList) > 0 and nextNoteIsChord is False:
            # TODO: move spanners from first note to Chord.  See slur in m2 of schoenberg/op19 #2
            c = self.xmlToChord(self.mxNoteList)
            # add any accumulated lyrics
            self.updateLyricsFromList(c, self.mxLyricList)
            self.addToStaffReference(self.mxNoteList, c)
            self.addNoteToMeasureOrVoice(mxNote, c)        
            self.mxNoteList = [] # clear for next chord
            self.mxLyricList = []

            offsetIncrement = c.quarterLength
            self.nLast = c # update

        # only increment Chords after completion
        self.offsetMeasureNote += offsetIncrement

    def xmlToChord(self, mxNoteList):
        '''
        Given an a list of mxNotes, fill the necessary parameters

        >>> from xml.etree.ElementTree import fromstring as EL
        >>> MP = musicxml.xmlToM21.MeasureParser()
        
        >>> MP.divisions = 10080
        
        >>> qnDuration = r'<duration>7560</duration><type>quarter</type>'
        
        >>> a = EL(r'<note><pitch><step>A</step><octave>3</octave></pitch>' + qnDuration + '</note>')
        >>> b = EL(r'<note><chord/><pitch><step>B</step><octave>3</octave></pitch>' 
        ...          + qnDuration + '</note>')

        >>> c = MP.xmlToChord([a, b])
        >>> len(c.pitches)
        2
        >>> c.pitches[0]
        <music21.pitch.Pitch A3>
        >>> c.pitches[1]
        <music21.pitch.Pitch B3>
    
        >>> a = EL(r'<note><pitch><step>A</step><octave>3</octave></pitch>' + qnDuration + 
        ...         '<notehead>diamond</notehead></note>')
        >>> c = MP.xmlToChord([a, b])
        >>> c.getNotehead(c.pitches[0])
        'diamond'
        '''
        notes = []
        for mxNote in mxNoteList:
            notes.append(self.xmlToSimpleNote(mxNote, freeSpanners=False))
        c = chord.Chord(notes)
        self.spannerBundle.freePendingSpannedElementAssignment(c)
        return c
    
    def xmlToSimpleNote(self, mxNote, freeSpanners=True):
        '''
        Translate a MusicXML <note> (without <chord/>) 
        to a :class:`~music21.note.Note`.
    
        The `spannerBundle` parameter can be a list or a Stream 
        for storing and processing Spanner objects.
        
        If inputM21 is not `None` then that object is used
        for translating. Otherwise a new Note is created.
        
        if freeSpanners is False then pending spanners will not be freed
        
        Returns a `note.Note` object.

        >>> from xml.etree.ElementTree import fromstring as EL
        >>> MP = musicxml.xmlToM21.MeasureParser()
        
        >>> MP.divisions = 10080
        
        >>> mxNote = EL('<note><pitch><step>D</step>' +
        ...     '<alter>-1</alter><octave>6</octave></pitch>' + 
        ...     '<duration>7560</duration>' +
        ...     '<type>eighth</type><dot/></note>')
               
        >>> n = MP.xmlToSimpleNote(mxNote)
        >>> n
        <music21.note.Note D->
        >>> n.octave
        6
        >>> n.duration
        <music21.duration.Duration 0.75>
        
        >>> beams = EL('<beam>begin</beam>')
        >>> mxNote.append(beams)
        >>> n = MP.xmlToSimpleNote(mxNote)
        >>> n.beams
        <music21.beam.Beams <music21.beam.Beam 1/start>>
        
        >>> stem = EL('<stem>up</stem>')
        >>> mxNote.append(stem)
        >>> n = MP.xmlToSimpleNote(mxNote)
        >>> n.stemDirection
        'up'
        '''
        n = note.Note()
        
        self.xmlToPitch(mxNote, n.pitch) # send whole note since accidental display not in <pitch> 
        
        beamList = mxNote.findall('beam')
        if len(beamList) > 0:
            n.beams = self.xmlToBeams(beamList)
    
        mxStem = mxNote.find('stem')
        if mxStem is not None:
            n.stemDirection = mxStem.text.strip()
            # TODO: y-position
            # TODO: color
    
        # gets the notehead object from the mxNote and sets value of the music21 note 
        # to the value of the notehead object        
        mxNotehead = mxNote.find('notehead')
        # TODO: notehead-text
        if mxNotehead is not None:
            self.xmlNotehead(n, mxNotehead)    
    
        # after this, use combined function for notes and rests...
        return self.xmlNoteToGeneralNoteHelper(n, mxNote, freeSpanners=freeSpanners)
    

    # beam and beams
    def xmlToBeam(self, mxBeam, inputM21=None):
        '''
        given an mxBeam object return a :class:`~music21.beam.Beam` object
    
        >>> from xml.etree.ElementTree import fromstring as EL
        >>> MP = musicxml.xmlToM21.MeasureParser()
        
        >>> mxBeam = EL('<beam>begin</beam>')
        >>> a = MP.xmlToBeam(mxBeam)
        >>> a.type
        'start'
    
        >>> mxBeam = EL('<beam>continue</beam>')
        >>> a = MP.xmlToBeam(mxBeam)
        >>> a.type
        'continue'
    
        >>> mxBeam = EL('<beam>end</beam>')
        >>> a = MP.xmlToBeam(mxBeam)
        >>> a.type
        'stop'
    
        >>> mxBeam = EL('<beam>forward hook    </beam>')
        >>> a = MP.xmlToBeam(mxBeam)
        >>> a.type
        'partial'
        >>> a.direction
        'right'
    
        >>> mxBeam = EL('<beam>backward hook</beam>')
        >>> a = MP.xmlToBeam(mxBeam)
        >>> a.type
        'partial'
        >>> a.direction
        'left'
    
        >>> mxBeam = EL('<beam>crazy</beam>')
        >>> a = MP.xmlToBeam(mxBeam)
        Traceback (most recent call last):
        MusicXMLImportException: unexpected beam type encountered (crazy)
        '''
        if inputM21 is None:
            beamOut = beam.Beam()
        else:
            beamOut = inputM21
            
        # TODO: get number to preserve
        # TODO: repeater; is deprecated -- maybe not.
        # TODO: fan
        # TODO: color
            
        mxType = mxBeam.text.strip()
        if mxType == 'begin':
            beamOut.type = 'start'
        elif mxType == 'continue':
            beamOut.type = 'continue'
        elif mxType == 'end':
            beamOut.type = 'stop'
        elif mxType == 'forward hook':
            beamOut.type = 'partial'
            beamOut.direction = 'right'
        elif mxType == 'backward hook':
            beamOut.type = 'partial'
            beamOut.direction = 'left'
        else:
            raise MusicXMLImportException('unexpected beam type encountered (%s)' % mxType)
    
        if inputM21 is None:
            return beamOut


    def xmlToBeams(self, mxBeamList, inputM21=None):
        '''given a list of mxBeam objects, sets the beamsList
    
        >>> from xml.etree.ElementTree import fromstring as EL
        >>> MP = musicxml.xmlToM21.MeasureParser()
        
        >>> mxBeam1 = EL('<beam>begin</beam>')
        >>> mxBeam2 = EL('<beam>begin</beam>')
        >>> mxBeamList = [mxBeam1, mxBeam2]
        >>> b = MP.xmlToBeams(mxBeamList)
        >>> b
        <music21.beam.Beams <music21.beam.Beam 1/start>/<music21.beam.Beam 2/start>>
        '''
        if inputM21 is None:
            beamsOut = beam.Beams()
        else:
            beamsOut = inputM21
        
        for i, mxBeam in enumerate(mxBeamList):
            beamObj = self.xmlToBeam(mxBeam)
            beamObj.number = i + 1
            beamsOut.beamsList.append(beamObj)
    
        if inputM21 is None:
            return beamsOut

    
    def xmlNotehead(self, n, mxNotehead):
        if mxNotehead.text not in ('', None):
            n.notehead = mxNotehead.text
        nhf = mxNotehead.get('filled')
        if nhf is not None:
            if nhf == 'yes':
                n.noteheadFill = True 
            elif nhf == 'no':
                n.noteheadFill = False 
        if mxNotehead.get('color') is not None:
            n.color = mxNotehead.get('color')
        # TODO font
        # TODO parentheses
    
    def xmlToPitch(self, mxNote, inputM21=None):
        '''
        Given a MusicXML Note object, set this Pitch object to its values.
    
        >>> import xml.etree.ElementTree as ET        
        >>> MP = musicxml.xmlToM21.MeasureParser()

        >>> b = ET.fromstring('<note><pitch><step>E</step><alter>-1</alter><octave>3</octave></pitch></note>')
        >>> a = MP.xmlToPitch(b)
        >>> print(a)
        E-3
        
        Conflicting alter and accidental -- accidental wins:
        
        >>> b = ET.fromstring('<note><pitch><step>E</step><alter>-1</alter><octave>3</octave></pitch><accidental>sharp</accidental></note>')
        >>> a = MP.xmlToPitch(b)
        >>> print(a)
        E#3
        '''
        seta = _setAttributeFromTagText
        if inputM21 == None:
            p = pitch.Pitch()
        else:
            p = inputM21
        
        if mxNote.tag == 'pitch':
            mxPitch = mxNote
        else:
            mxPitch = mxNote.find('pitch')
            if mxPitch is None: # whoops!!!!
                return p
        
        seta(p, mxPitch, 'step')
        seta(p, mxPitch, 'octave', transform=int)
        mxAlter = mxPitch.find('alter')
        accAlter = None
        if mxAlter is not None:
            accAlter = int(mxAlter.text.strip()) 
                
        mxAccidental = mxNote.find('accidental')
        mxAccidentalName = None
        if mxAccidental is not None and mxAccidental.text is not None:
            # MuseScore 0.9 made empty accidental tags for notes that did not
            # need an accidental display.
            mxAccidentalName = mxAccidental.text.strip()

        if mxAccidentalName is not None:
            try:
                accObj = self.xmlToAccidental(mxAccidental)
                p.accidental = accObj
                p.accidental.displayStatus = True
            except pitch.AccidentalException:
                # MuseScore 0.9.6 generates Accidentals with empty objects
                pass
        elif accAlter is not None:
            try:
                p.accidental = pitch.Accidental(float(accAlter))
            except pitch.AccidentalException:
                raise MusicXMLImportException('incorrect accidental {0} for pitch {1}' .format(accAlter, p))
            p.accidental.displayStatus = False

        return p
    
    def xmlToAccidental(self, mxAccidental, inputM21=None):
        '''
        >>> import xml.etree.ElementTree as ET        
        >>> MP = musicxml.xmlToM21.MeasureParser()

        >>> a = ET.fromstring('<accidental>half-flat</accidental>')
        >>> b = pitch.Accidental()
        >>> MP.xmlToAccidental(a, b)
        >>> b.name
        'half-flat'
        >>> b.alter
        -0.5
        '''    
        if inputM21 is None:
            acc = pitch.Accidental()
        else:
            acc = inputM21
     
        mxName = mxAccidental.text.strip().lower()
        if mxName in self.mxAccidentalNameToM21: 
            name = self.mxAccidentalNameToM21[mxName]
        else:
            name = mxName
        # need to use set here to get all attributes up to date
        acc.set(name)
    
        if inputM21 is None:
            return acc
        

    
    def xmlToRest(self, mxRest):
        r = note.Rest()
        return self.xmlNoteToGeneralNoteHelper(r, mxRest)

    def xmlNoteToGeneralNoteHelper(self, n, mxNote, freeSpanners=True):
        spannerBundle = self.spannerBundle
        if freeSpanners is True:
            spannerBundle.freePendingSpannedElementAssignment(n)

        # print object == 'no' and grace notes may have a type but not
        # a duration. they may be filtered out at the level of Stream 
        # processing
        if mxNote.get('print-object') == 'no':
            n.hideObjectOnPrint = True

        mxGrace = mxNote.find('grace')
        isGrace = False
        if mxGrace is not None:
            isGrace = True
            graceType = mxNote.find('type')
            if graceType is None:
                # this technically puts it in the
                # wrong place in the sequence, but it won't matter
                ET.SubElement(mxNote, '<type>eighth</type>')
        
        self.xmlToDuration(mxNote, n.duration)
        colorAttr = mxNote.get('color')
        if colorAttr is not None:
            n.color = colorAttr
        
        self.setPosition(mxNote, n)
        
        if mxNote.find('tie') is not None:
            n.tie = self.xmlToTie(mxNote)
            # provide all because of tied...
            # TODO: find tied if tie is not found... (cue notes)
            
        mxNotations = mxNote.find('notations')
        if mxNotations is not None:
            self.xmlNotations(mxNotations, n)

        # translate if necessary, otherwise leaves unchanged
        if isGrace is True:
            n = self.xmlGraceToGrace(mxGrace, n)
        
        return n
            
        # TODO: attr: font
        # TODO: attr: printout
        # TODO: attr: dynamics
        # TODO: attr: end-dynamics
        # TODO: attr: attack
        # TODO: attr: release
        # TODO: attr: time-only
        # TODO: attr: pizzicato
        # TODO: play
        # TODO: editorial-voice
        # TODO: instrument
        
    def xmlToDuration(self, mxNote, inputM21=None):
        '''
        Translate a `MusicXML` <note> object's
        <duration>, <type>, <dot>, tuplets, etc. 
        to a music21 :class:`~music21.duration.Duration` object.
    
        >>> from xml.etree.ElementTree import fromstring as EL
        >>> MP = musicxml.xmlToM21.MeasureParser()
        
        >>> MP.divisions = 10080
        
        >>> mxNote = EL('<note><pitch><step>D</step>' +
        ...     '<alter>-1</alter><octave>6</octave></pitch>' + 
        ...     '<duration>7560</duration>' +
        ...     '<type>eighth</type><dot/></note>')

        >>> c = duration.Duration()
        >>> MP.xmlToDuration(mxNote, c)
        >>> c
        <music21.duration.Duration 0.75>
        >>> c.quarterLength
        0.75
        >>> c.type
        'eighth'
        >>> c.dots
        1
        '''
        if inputM21 == None:
            d = None
        else:
            d = inputM21
    
        divisions = self.divisions
        mxDuration = mxNote.find('duration')
        if mxDuration is not None:
            noteDivisions = float(mxDuration.text.strip())
            qLen = float(noteDivisions) / divisions
        else:
            noteDivisions = None
            qLen = 0.0
            
            
        mxType = mxNote.find('type')
        if mxType is not None:
            typeStr = mxType.text.strip()
            durationType = musicXMLTypeToType(typeStr)
            forceRaw = False
            numDots = len(mxNote.findall('dot'))
            # divide mxNote duration count by divisions to get qL
            # mxNotations = mxNote.get('notationsObj')
            mxTimeModification = mxNote.find('time-modification')
    
            if mxTimeModification is not None:
                tup = self.xmlToTuplet(mxNote)
                # TODO: nested tuplets...
                # get all necessary config from mxNote
            else:
                tup = None

        else: # some rests do not define type, and only define duration
            durationType = None # no type to get, must use raw
            forceRaw = True
            # TODO: empty-placement
            
        # two ways to create durations, raw (from qLen) and cooked (from type, time-mod, dots)
        if forceRaw:
            if d is not None:
                #environLocal.printDebug(['forced to use raw duration', durRaw])
                durRaw = duration.Duration() # raw just uses qLen
                # the qLen set here may not be computable, but is not immediately
                # computed until setting components
                durRaw.quarterLength = qLen
                try:
                    d.components = durRaw.components
                except duration.DurationException: # TODO: Test
                    qLenRounded = 2.0**round(math.log(qLen, 2)) # math.log2 appears in py3.3
                    environLocal.printDebug(['mxToDuration', 
                            'rounding duration to {0} as type is not'.format(qLenRounded) + 
                            'defined and raw quarterlength ({0}) is not a computable duration'.format(qLen)])
                    #environLocal.printDebug(['mxToDuration', 'raw qLen', qLen, durationType, 
                    #                         'mxNote:', ET.tostring(mxNote, encoding='unicode'), 
                    #                         'last mxDivisions:', divisions])
                    durRaw.quarterLength = qLenRounded
            else:
                d = duration.Duration(quarterLength=qLen)
        else: # a cooked version builds up from pieces
            dt = duration.durationTupleFromTypeDots(durationType, numDots)
            if d is not None:
                d.clear()
                d.addDurationTuple(dt)
            else:
                d = duration.Duration(durationTuple=dt)

            if tup is not None:
                d.appendTuplet(tup)
    
        if inputM21 is None:
            return d    

    def xmlGraceToGrace(self, mxGrace, noteOrChord):
        '''
        Given a completely formed, non-grace Note or Chord that should become one
        create and return a m21 grace version of the same.
        '''
        post = noteOrChord.getGrace()
        if mxGrace.get('slash') in ('yes', None):
            post.duration.slash = True
        else:
            post.duration.slash = False
    
        post.duration.stealTimePrevious = mxGrace.get('steal-time-previous')
        post.duration.stealTimeFollowing = mxGrace.get('steal-time-following')
        # TODO: make-time
    
        return post
    
    def xmlNotations(self, mxNotations, n):
        # TODO: editorial
        # TODO: attr: print-object
        
        # TODO: adjust tie with tied
        # TODO: tuplet -- look of time-modification.
        # TODO: slide
        # TODO: dynamics
        # TODO: arpeggiate
        # TODO: non-arpeggiate
        # TODO: accidental-mark
        # TODO: other-notation
        
        def flatten(mx, name):
            findall = mx.findall(name)
            return [item for sublist in findall for item in sublist]
        
        for mxObj in flatten(mxNotations, 'technical'):
            technicalObj = self.xmlTechnicalToArticulation(mxObj)
            if technicalObj is not None:
                n.articulations.append(technicalObj)

        for mxObj in flatten(mxNotations, 'articulations'):
            articulationObj = self.xmlToArticulation(mxObj)
            if articulationObj is not None:
                n.articulations.append(articulationObj)
                
        
        # get any fermatas, store on expressions
        for mxObj in mxNotations.findall('fermata'):
            fermata = expressions.Fermata()
            ftype = mxObj.get('type')
            if ftype is not None:
                fermata.type = ftype
            n.expressions.append(fermata)

        for mxObj in flatten(mxNotations, 'ornaments'):
            if mxObj.tag in (xmlObjects.ORNAMENT_MARKS):
                post = self.xmlOrnamentToExpression(mxObj)
                if post is not None:
                    n.expressions.append(post)
                #environLocal.printDebug(['adding to epxressions', post])
            elif mxObj.tag == 'wavy-line':
                self.xmlOneSpanner(mxObj, n, expressions.TrillExtension)
            elif mxObj.tag == 'tremolo':
                self.xmlToTremolo(mxObj, n)
        
        
        # create spanners for rest
        self.xmlNotationsToSpanners(mxNotations, n)

    def xmlTechnicalToArticulation(self, mxObj):  
        '''
        Convert an mxArticulationMark to a music21.articulations.Articulation
        object or one of its subclasses.
        
        >>> from xml.etree.ElementTree import fromstring as EL
        >>> MP = musicxml.xmlToM21.MeasureParser()

        >>> mxTech = EL('<down-bow placement="below"/>')
        >>> a = MP.xmlTechnicalToArticulation(mxTech)
        >>> a
        <music21.articulations.DownBow>
        >>> a.placement
        'below'
        '''    
        tag = mxObj.tag
        if tag in xmlObjects.TECHNICAL_MARKS:
            tech = xmlObjects.TECHNICAL_MARKS[tag]()
            # print-style
            placement = mxObj.get('placement')
            if placement is not None:
                tech.placement = placement
            return tech
        else:
            environLocal.printDebug("Cannot translate %s in %s." % (tag, mxObj))
            return None
        
        
    def xmlToArticulation(self, mxObj):
        '''
        Return an articulation from an mxObj, setting placement
        
        >>> from xml.etree.ElementTree import fromstring as EL
        >>> MP = musicxml.xmlToM21.MeasureParser()

        >>> mxArt = EL('<spiccato placement="above"/>')
        >>> a = MP.xmlToArticulation(mxArt)
        >>> a
        <music21.articulations.Spiccato>
        >>> a.placement
        'above'
        '''
        tag = mxObj.tag
        if tag in xmlObjects.ARTICULATION_MARKS:
            artic = xmlObjects.ARTICULATION_MARKS[tag]()
            # print-style
            placement = mxObj.get('placement')
            if placement is not None:
                artic.placement = placement
            return artic
        else:
            environLocal.printDebug("Cannot translate %s in %s." % (tag, mxObj))
            return None
        
    def xmlOrnamentToExpression(self, mxObj):
        '''
        Convert mxOrnament into a music21 ornament. 
        
        This only processes non-spanner ornaments. 
        Many mxOrnaments are spanners: these are handled elsewhere.
    
        Returns None if cannot be converted or not defined.

        Return an articulation from an mxObj, setting placement
        
        >>> from xml.etree.ElementTree import fromstring as EL
        >>> MP = musicxml.xmlToM21.MeasureParser()

        >>> mxOrn = EL('<inverted-turn placement="above"/>')
        >>> a = MP.xmlOrnamentToExpression(mxOrn)
        >>> a
        <music21.expressions.InvertedTurn>
        >>> a.placement
        'above'

        If it can't be converted, return None

        >>> mxOrn = EL('<crazy-slide placement="above"/>')
        >>> a = MP.xmlOrnamentToExpression(mxOrn)
        >>> a is None
        True
        
        Not supported currently: 'accidental-mark', 'vertical-turn', 
        'delayed-turn', 'delayed-inverted-turn'
        '''
        tag = mxObj.tag
        try:
            orn = xmlObjects.ORNAMENT_MARKS[tag]()
        except KeyError: # should already be checked...
            return None
        # print-style
        # trill-sound?
        placement = mxObj.get('placement')
        if placement is not None:
            orn.placement = placement
        return orn

    def xmlDirectionTypeToSpanners(self, mxObj):
        '''
        Some spanners, such as MusicXML wedge, bracket, and dashes, 
        are encoded as MusicXML directions.
        
        >>> from xml.etree.ElementTree import fromstring as EL
        >>> MP = musicxml.xmlToM21.MeasureParser()
        >>> n1 = note.Note("D4")
        >>> MP.nLast = n1

        >>> len(MP.spannerBundle)
        0
        >>> mxDirectionType = EL('<wedge type="crescendo" number="2"/>')
        >>> MP.xmlDirectionTypeToSpanners(mxDirectionType)
        >>> len(MP.spannerBundle)
        1
        >>> sp = MP.spannerBundle[0]
        >>> sp
        <music21.spanner.Crescendo >
        
        >>> mxDirectionType2 = EL('<wedge type="stop" number="2"/>')
        >>> MP.xmlDirectionTypeToSpanners(mxDirectionType2)
        >>> len(MP.spannerBundle)
        1
        >>> sp = MP.spannerBundle[0]
        >>> sp
        <music21.spanner.Crescendo <music21.note.Note D>>        
        
        '''    
        targetLast = self.nLast
        
        if mxObj.tag == 'wedge':
            mType = mxObj.get('type')
            if mType == 'crescendo':
                spClass = dynamics.Crescendo
            elif mType == 'diminuendo':
                spClass = dynamics.Diminuendo
            elif mType == 'stop':
                spClass = dynamics.DynamicWedge # parent of Cresc/Dim

            if mType != 'stop':
                sp = self.xmlOneSpanner(mxObj, None, spClass, allowDuplicateIds=True)
                self.spannerBundle.setPendingSpannedElementAssignment(sp, 'GeneralNote')                
            else:
                idFound = mxObj.get('number')
                spb = self.spannerBundle.getByClassIdLocalComplete(
                    'DynamicWedge', idFound, False) # get first
                try:
                    sp = spb[0]
                except IndexError:
                    raise MusicXMLImportException("Error in geting DynamicWedges..." + 
                          "Measure no. " + str(self.measureNumber) + " " + str(self.parent.partId))
                sp.completeStatus = True
                # will only have a target if this follows the note
                if targetLast is not None:
                    sp.addSpannedElements(targetLast)

        if mxObj.tag in ('bracket', 'dashes'):
            mxType = mxObj.get('type')
            idFound = mxObj.get('number')
            if mxType == 'start':
                sp = spanner.Line()
                sp.idLocal = idFound
                if mxObj.tag == 'dashes':
                    sp.startTick = 'none'
                    sp.lineType = 'dashed'
                else:
                    sp.startHeight = mxObj.get('end-length')
                    sp.startTick = mxObj.get('line-end')
                    sp.lineType = mxObj.get('line-type')
    
                self.spannerBundle.append(sp)
                # define this spanner as needing component assignment from
                # the next general note
                self.spannerBundle.setPendingSpannedElementAssignment(sp, 'GeneralNote')
            elif mxType == 'stop':
                # need to retrieve an existing spanner
                # try to get base class of both Crescendo and Decrescendo
                sp = self.spannerBundle.getByClassIdLocalComplete('Line',
                        idFound, False)[0] # get first
                sp.completeStatus = True
                
                if mxObj.tag == 'dashes':
                    sp.endTick = 'none'
                else:
                    sp.endTick = mxObj.get('line-end')
                    sp.endHeight = mxObj.get('end-length')
                    sp.lineType = mxObj.get('line-type')
    
                # will only have a target if this follows the note
                if targetLast is not None:
                    sp.addSpannedElements(targetLast)
            else:
                raise MusicXMLImportException('unidentified mxType of mxBracket:', mxType)
#             if self.measureNumber > 95 and self.measureNumber < 102:
#                 environLocal.warn([sp, sp.completeStatus, self.measureNumber])
#                 environLocal.warn(['mxDirectionToSpanners', 'found mxBracket', mxType, idFound])

        
    def xmlNotationsToSpanners(self, mxNotations, n):
        for mxObj in mxNotations.findall('slur'):
            self.xmlOneSpanner(mxObj, n, spanner.Slur)
        for mxObj in mxNotations.findall('glissando'):
            self.xmlOneSpanner(mxObj, n, spanner.Glissando)
        
    def xmlToTremolo(self, mxTremolo, n):
        # tremolo is tricky -- can be either an
        # expression or spanner...
        tremoloType = mxTremolo.get('type')
        isSingle = True
        if tremoloType in ('start', 'stop'):
            isSingle = False
            
        try:
            numMarks = int(mxTremolo.text.strip())
        except (ValueError, AttributeError):
            #environLocal.warn("could not convert ", dir(mxObj))
            numMarks = 3
        if isSingle is True:
            ts = expressions.Tremolo()
            ts.numberOfMarks = numMarks
            n.expressions.append(ts)
        else:
            tremSpan = self.xmlOneSpanner(mxTremolo, n, expressions.TremoloSpanner)
            tremSpan.numberOfMarks = numMarks
            
    def xmlOneSpanner(self, mxObj, target, spannerClass, allowDuplicateIds=False):
        '''
        Some spanner types do not have an id necessarily, we allow duplicates of them
        if allowDuplicateIds is True. Wedges are one.
        '''
        idFound = mxObj.get('number')

        # returns a new spanner bundle with just the result of the search
        sb = self.spannerBundle.getByClassIdLocalComplete(spannerClass, idFound, False)
        if len(sb) > 0 and allowDuplicateIds is False: 
            # if we already have a spanner matching
            #environLocal.printDebug(['found a match in SpannerBundle'])
            su = sb[0] # get the first
        else: # create a new slur
            su = spannerClass()
            su.idLocal = idFound
            placement = mxObj.get('placement')
            if placement is not None:
                # not all spanners have placement
                su.placement = placement
            self.spannerBundle.append(su)

        # add a reference of this note to this spanner
        if target is not None:
            su.addSpannedElements(target)
        #environLocal.printDebug(['adding n', n, id(n), 'su.getSpannedElements', su.getSpannedElements(), su.getSpannedElementIds()])
        if mxObj.get('type') == 'stop':
            su.completeStatus = True
            # only add after complete
        return su
    
    def xmlToTie(self, mxNote):
        '''
        Translate a MusicXML <note> with <tie> subelements
        :class:`~music21.tie.Tie` object
        '''
        t = tie.Tie()
        allTies = mxNote.findall('tie')
        if len(allTies) == 0:
            return None
        
        typesFound = []
        for mxTie in allTies:
            typesFound.append(mxTie.get('type'))
    
        if len(typesFound) == 1:
            t.type = typesFound[0]
        elif 'stop' in typesFound and 'start' in typesFound:
            t.type = 'continue'
        else:
            environLocal.printDebug(['found unexpected arrangement of multiple tie types when ' +
                         'importing from musicxml:', typesFound])
        # TODO: look at notations for printed, non-sounding ties
#         mxNotations = mxNote.get('notations')
#         if mxNotations != None:
#             mxTiedList = mxNotations.getTieds()
        return t

    
    def xmlToTuplet(self, mxNote, inputM21=None):
        '''
        Given an mxNote, based on mxTimeModification 
        and mxTuplet objects, return a Tuplet object
        (or alter the input object and then return it)
        
        >>> import xml.etree.ElementTree as ET        
        >>> MP = musicxml.xmlToM21.MeasureParser()
        
        >>> mxNote = ET.fromstring('<note><type>16th</type><time-modification><actual-notes>5</actual-notes><normal-notes>4</normal-notes></time-modification></note>')
        >>> t = MP.xmlToTuplet(mxNote)
        >>> t
        <music21.duration.Tuplet 5/4/16th>
        ''' 
        if inputM21 is None:
            t = duration.Tuplet()
        else:
            t = inputM21
        if t.frozen is True:
            raise duration.TupletException("A frozen tuplet (or one attached to a duration) " +
                                           "is immutable")
        mxTimeModification = mxNote.find('time-modification')
        #environLocal.printDebug(['got mxTimeModification', mxTimeModification])
        seta = _setAttributeFromTagText
        seta(t, mxTimeModification, 'actual-notes', 'numberNotesActual', transform=int)
        seta(t, mxTimeModification, 'normal-notes', 'numberNotesNormal', transform=int)
        
        mxNormalType = mxTimeModification.get('normal-type')
        if mxNormalType is not None:
            musicXMLNormalType = mxNormalType.text.strip()
        else:
            musicXMLNormalType = mxNote.find('type').text.strip()

        t.setDurationType(musicXMLTypeToType(musicXMLNormalType))
        
        # TODO: implement dot
        # mxNormalDot = mxTimeModification.get('normal-dot')
    
        mxNotations = mxNote.find('notations')
        #environLocal.printDebug(['got mxNotations', mxNotations])
    
        if mxNotations is not None:
            # TODO: findall -- these are unbounded...
            mxTuplet = mxNotations.find('tuplet')
            if mxTuplet is not None:
                # TODO: tuplet-actual
                # TODO: tuplet-normal               
                t.type = mxTuplet.get('type') # required
                 
                t.bracket = xmlObjects.yesNoToBoolean(mxTuplet.get('bracket'))
                #environLocal.printDebug(['got bracket', self.bracket])
                showNumber = mxTuplet.get('show-number')
                if showNumber is not None and showNumber == 'none':
                    # do something for 'both'; 'actual' is the default
                    t.tupletActualShow = 'none'
                # TODO: show-type
                # TODO: line-shape
                # TODO: position
                t.placement = mxTuplet.get('placement') 
    
        if inputM21 is None:
            return t


    def updateLyricsFromList(self, n, lyricList):
        '''
        Takes a list of <lyric> elements and update the
        note's lyrics from that list.

        >>> import xml.etree.ElementTree as ET        
        >>> MP = musicxml.xmlToM21.MeasureParser()
        
        >>> mxLyric1 = ET.fromstring('<lyric><text>Hi</text></lyric>')
        >>> mxLyric2 = ET.fromstring('<lyric><text>Hi</text></lyric>')
        >>> n = note.Note()
        >>> MP.updateLyricsFromList(n, [mxLyric1, mxLyric2])
        >>> n.lyrics
        [<music21.note.Lyric number=1 syllabic=single text="Hi">, <music21.note.Lyric number=2 syllabic=single text="Hi">]
        '''
        currentLyricNumber = 1
        for mxLyric in lyricList:
            lyricObj = self.xmlToLyric(mxLyric)
            if lyricObj.number == 0:
                lyricObj.number = currentLyricNumber
            n.lyrics.append(lyricObj)
            currentLyricNumber += 1

    def xmlToLyric(self, mxLyric, inputM21=None):
        '''
        Translate a MusicXML <lyric> tag to a 
        music21 :class:`~music21.note.Lyric` object.
        
        If inputM21 is a :class:`~music21.note.Lyric` object, then the values of the 
        mxLyric are transfered there and nothing returned.
        
        Otherwise, a new `Lyric` object is created and returned.
        
        >>> import xml.etree.ElementTree as ET        
        >>> MP = musicxml.xmlToM21.MeasureParser()
        
        >>> mxLyric = ET.fromstring('<lyric number="4"><syllabic>single</syllabic><text>word</text></lyric>')
        >>> lyricObj = note.Lyric()
        >>> MP.xmlToLyric(mxLyric, lyricObj)
        >>> lyricObj
        <music21.note.Lyric number=4 syllabic=single text="word">
        
        Non-numeric MusicXML lyric "number"s are converted to identifiers:
        
        >>> mxLyric.set('number', 'part2verse1')    
        >>> l2 = MP.xmlToLyric(mxLyric)
        >>> l2
        <music21.note.Lyric number=0 identifier="part2verse1" syllabic=single text="word">
        '''
        if inputM21 is None:
            l = note.Lyric()
        else:
            l = inputM21
    
        try:
            l.text = mxLyric.find('text').text.strip()
        except AttributeError:
            pass # sometimes there are empty lyrics
            
        # This is new to account for identifiers
        
        number = mxLyric.get('number')
        
        try:
            number = int(number)
            l.number = number
        except (TypeError, ValueError):
            l.number = 0  #If musicXML lyric number is not a number, set it to 0. This tells the caller of
                            #mxToLyric that a new number needs to be given based on the lyrics context amongst other lyrics.
            if number is not None:
                l.identifier = number
        
        # Used to be l.number = mxLyric.get('number')
        mxSyllabic = mxLyric.find('syllabic')
        if mxSyllabic is not None:
            l.syllabic = mxSyllabic.text.strip()
    
        if inputM21 is None:
            return l
        

    def addNoteToMeasureOrVoice(self, mxNote, n):
        m = self.stream
        if self.useVoices:
            useVoice = mxNote.find('voice')
            if useVoice is None:
                useVoice = self.chordVoice
                if useVoice is None:
                    environLocal.warn("Cannot translate a note with a missing voice tag when no previous voice tag was given.  Assuming voice 1... Object is %r " % mxNote)
                    useVoice = 1
            else:
                useVoice = useVoice.text.strip()
            try:
                thisVoice = m.voices[useVoice]
            except stream.StreamException:
                thisVoice = None
                
            if thisVoice is None:
                environLocal.warn('Cannot find voice %d for Note %r; putting outside of voices...' % (useVoice, mxNote))
                environLocal.warn('Current voices: {0}'.format([v for v in m.voices]))

                m._insertCore(self.offsetMeasureNote, n)
            else:
                thisVoice._insertCore(self.offsetMeasureNote, n)
        else:
            m._insertCore(self.offsetMeasureNote, n)

      
    def xmlBarline(self, mxBarline):
        '''
        Handles everything for putting a barline into a Stream
        and updating repeat characteristics.
        '''
        m = self.stream

        mxRepeatObj = mxBarline.find('repeat')
        if mxRepeatObj is not None:
            barline = self.xmlToRepeat(mxBarline)
        else:
            barline = self.xmlToBarline(mxBarline)

        # barline objects also store ending objects, that mark begin
        # and end of repeat bracket designations
        mxEndingObj = mxBarline.find('ending')
        if mxEndingObj is not None:
            #environLocal.printDebug(['found mxEndingObj', mxEndingObj, 'm', m]) 
            # get all incomplete spanners of the appropriate class that are
            # not complete
            rbSpanners = self.spannerBundle.getByClass('RepeatBracket').getByCompleteStatus(False)
            # if we have no complete bracket objects, must start a new one
            if len(rbSpanners) == 0:
                # create with this measure as the object
                rb = spanner.RepeatBracket(m)
                # there may just be an ending marker, and no start
                # this implies just one measure
                if mxEndingObj.get('type') in ('stop', 'discontinue'):
                    rb.completeStatus = True
                    rb.number = mxEndingObj.get('number')
                # set number; '' or None is interpreted as 1
                self.spannerBundle.append(rb)
            # if we have any incomplete, this must be the end
            else:
                #environLocal.printDebug(['matching RepeatBracket spanner', 'len(rbSpanners)', len(rbSpanners)])
                rb = rbSpanners[0] # get RepeatBracket
                # try to add this measure; may be the same
                rb.addSpannedElements(m)
                # in general, any rb found should be the opening, and thus
                # this is the closing; can check
                if mxEndingObj.get('type') in ('stop', 'discontinue'):
                    rb.completeStatus = True
                    rb.number = mxEndingObj.get('number')
                else:
                    environLocal.warn('found mxEnding object that is not stop message, even though there is still an open start message. -- ignoring it')

        if barline.location == 'left':
            #environLocal.printDebug(['setting left barline', barline])
            m.leftBarline = barline
        elif barline.location == 'right':
            #environLocal.printDebug(['setting right barline', barline])
            m.rightBarline = barline
        else:
            environLocal.printDebug(['not handling barline that is neither left nor right', barline, barline.location])

    def xmlToRepeat(self, mxBarline, inputM21=None):
        '''
        Given an mxBarline (not an mxRepeat object) with repeatObj as a parameter, 
        file the necessary parameters and return a bar.Repeat() object
    
        >>> import xml.etree.ElementTree as ET        
        >>> MP = musicxml.xmlToM21.MeasureParser()
        
        >>> mxBarline = ET.fromstring('<barline><bar-style>light-heavy</bar-style>' + 
        ...       '<repeat direction="backward"/></barline>')
        >>> r = MP.xmlToRepeat(mxBarline)
        >>> r
        <music21.bar.Repeat direction=end>
    
        Test that the music21 style for a backwards repeat is called "final"
        (because it resembles a final barline) but that the musicxml style
        is called light-heavy.
    
        >>> r.style
        'final'
        >>> r.direction
        'end'

        # TODO: replace after changing output not to use toMxObjects
        
        >>> mxBarline2 = musicxml.toMxObjects.repeatToMx(r)
        >>> mxBarline2.get('barStyle')
        'light-heavy'
        '''
        if inputM21 is None:
            r = bar.Repeat()
        else:
            r = inputM21

    
        seta = _setAttributeFromTagText
        seta(r, mxBarline, 'bar-style', 'style')
        # TODO: editorial
        # TODO: wavy-line
        # TODO: segno, coda, fermata,
        # TODO: winged
        location = mxBarline.get('location')
        if location is not None:
            r.location = location
    
        mxRepeat = mxBarline.find('repeat')
        if mxRepeat is None:
            raise bar.BarException('attempting to create a Repeat from an MusicXML bar that does not ' +
                                   'define a repeat')
    
        mxDirection = mxRepeat.get('direction')
        #environLocal.printDebug(['mxRepeat', mxRepeat, mxRepeat._attr])
        if mxDirection is None:
            raise MusicXMLImportException("Repeat sign direction is required")
        
        if mxDirection.lower() == 'forward':
            r.direction = 'start'
        elif mxDirection.lower() == 'backward':
            r.direction = 'end'
        else:
            raise bar.BarException('cannot handle mx direction format:', mxDirection)
    
        if mxRepeat.get('times') != None:
            # make into a number
            r.times = int(mxRepeat.get('times'))
    
        if inputM21 is None:
            return r

    def xmlToBarline(self, mxBarline, inputM21=None):
        '''
        Given an mxBarline, fill the necessary parameters
    
        >>> import xml.etree.ElementTree as ET        
        >>> MP = musicxml.xmlToM21.MeasureParser()
        
        >>> mxBarline = ET.fromstring('<barline location="right"><bar-style>light-light</bar-style></barline>')
        >>> b = MP.xmlToBarline(mxBarline)
        >>> b
        <music21.bar.Barline style=double>
        >>> b.style  # different in music21 than musicxml
        'double'
        >>> b.location
        'right'
        '''
        if inputM21 is None:
            b = bar.Barline()
        else:
            b = inputM21

        seta = _setAttributeFromTagText
        seta(b, mxBarline, 'bar-style', 'style')
        location = mxBarline.get('location')
        if location is not None:
            b.location = location
    
        if inputM21 is None:
            return b

    
    def xmlHarmony(self, mxHarmony):
        h = self.xmlToChordSymbol(mxHarmony)
        self.insertCoreAndRef(self.offsetMeasureNote, mxHarmony, h)
    
    def xmlToChordSymbol(self, mxHarmony):
        '''
        Convert a <harmony> tag to a harmony.ChordSymbol object:
        
        >>> from xml.etree.ElementTree import fromstring as EL
        >>> MP = musicxml.xmlToM21.MeasureParser()
        
        >>> elStr = '<harmony><root><root-step>D</root-step><root-alter>-1</root-alter></root><kind>major-seventh</kind></harmony>'
        >>> mxHarmony = EL(elStr)

        >>> cs = MP.xmlToChordSymbol(mxHarmony)
        >>> cs
        <music21.harmony.ChordSymbol D-maj7>
    
        >>> cs.figure
        'D-maj7'
    
        >>> cs.pitches
        (<music21.pitch.Pitch D-3>, <music21.pitch.Pitch F3>, <music21.pitch.Pitch A-3>, <music21.pitch.Pitch C4>)
    
        >>> cs.root()
        <music21.pitch.Pitch D-3>
        
        TODO: this is very classically-oriented.  Make more Jazz/Rock like possible/default?.
        
        >>> mxHarmony.find('kind').text = 'major-sixth'
        >>> cs = MP.xmlToChordSymbol(mxHarmony)
        >>> cs
        <music21.harmony.ChordSymbol D-6>
    
        >>> cs.figure
        'D-6'
    
        >>> cs.pitches
        (<music21.pitch.Pitch D-3>, <music21.pitch.Pitch F3>, <music21.pitch.Pitch A-3>, <music21.pitch.Pitch B-3>)
    
        >>> cs.root()
        <music21.pitch.Pitch D-3>  
        '''
        # TODO: frame
        # TODO: offset
        # TODO: editorial
        # TODO: staff
        # TODO: attrGroup: print-object
        # TODO: attr: print-frame
        # TODO: attrGroup: print-style
        # TODO: attrGroup: placement
        
        #environLocal.printDebug(['mxToChordSymbol():', mxHarmony])
        cs = harmony.ChordSymbol()
        seta = _setAttributeFromTagText

        # TODO: root vs. function;  see group "harmony-chord")
        mxRoot = mxHarmony.find('root')
        if mxRoot is not None: # choice: <root> or <function>
            mxRS = mxRoot.find('root-step')
            rootText = mxRS.text
            if rootText in (None, ""):
                rootText = mxRS.get('text') # two ways to do it... this should do display even
                    # if content is supported.
            r = pitch.Pitch(rootText)
            mxRootAlter =  mxRoot.find('root-alter')
            if mxRootAlter is not None:
                # can provide integer to create accidental on pitch
                r.accidental = pitch.Accidental(int(mxRootAlter.text))
            # set Pitch object on Harmony
            cs.root(r)
        else:
            # function instead
            seta(cs, mxHarmony, 'function', 'romanNumeral')
            
            
        mxKind = mxHarmony.find('kind')
        if mxKind is not None and mxKind.text is not None: # two ways of doing it...
            cs.chordKind = mxKind.text.strip()
            mxKindText = mxKind.get('text') # attribute
            if mxKindText is not None:
                cs.chordKindStr = mxKindText
        # TODO: attr: use-symbols
        # TODO: attr: stack-degrees
        # TODO: attr: parentheses-degrees
        # TODO: attr: bracket-degrees
        # TODO: attrGroup: print-style
        # TODO: attrGroup: halign
        # TODO: attrGroup: valign
    
        mxInversion = mxHarmony.find('inversion')
        if mxInversion is not None:
            cs.inversion(int(mxInversion.text.strip()), transposeOnSet=False) # must be an int
        # TODO: print-style
    
        mxBass = mxHarmony.find('bass')
        if mxBass is not None:
            # required
            b = pitch.Pitch(mxBass.find('bass-step').text)
            # optional
            mxBassAlter = mxBass.find('bass-alter')
            if mxBassAlter is not None:
                # can provide integer to create accidental on pitch
                b.accidental = pitch.Accidental(int(mxBassAlter.text))
            # set Pitch object on Harmony
            cs.bass(b)
        else:
            cs.bass(r) #set the bass to the root if root is none
        
        mxDegrees = mxHarmony.findall('degree')
        
        for mxDegree in mxDegrees: # a list of components
            hd = harmony.ChordStepModification()
            seta(hd, mxDegree, 'degree-value', 'degree', int)
            seta(hd, mxDegree, 'degree-alter', 'interval', int)
            seta(hd, mxDegree, 'degree-type', 'modType')
            cs.addChordStepModification(hd)

        cs._updatePitches()
        #environLocal.printDebug(['xmlToChordSymbol(): Harmony object', h])
        if cs.root().name != r.name:
            cs.root(r)
        
        return cs
    
    
    def xmlDirection(self, mxDirection):
        '''
        convert a <direction> tag to an expression, metronome mark, etc.
        and add it to the core and staff direction.
        '''
        offsetDirection = self.xmlToOffset(mxDirection)
        totalOffset = offsetDirection + self.offsetMeasureNote
        
        # staffKey is the staff that this direction applies to. not
        # found in mxDir but in mxDirection itself.
        staffKey = self.getStaffNumberStr(mxDirection)
        # TODO: editorial-voice-direction
        # TODO: staff
        # TODO: sound
        for mxDirType in mxDirection.findall('direction-type'):
            for mxDir in mxDirType:
                # TODO: rehearsal
                # TODO: pedal
                # TODO: octave-shift
                # TODO: harp-pedals
                # TODO: damp
                # TODO: damp-all
                # TODO: eyeglasses
                # TODO: string-mute
                # TODO: scordatura
                # TODO: image
                # TODO: principal-voice
                # TODO: accordion-registration
                # TODO: percussion
                # TODO: other-direction
                tag = mxDir.tag
                if tag == 'dynamics': #fp, mf, etc., each as a tag
                    # in rare cases there may be more than one dynamic in the same
                    # direction, so we iterate
                    for dyn in mxDir:
                        # TODO: other-dynamic
                        d = dynamics.Dynamic(dyn.tag)
                        _setAttributeFromAttribute(d, mxDirection, 'placement', '_positionPlacement')
                        
                        self.insertCoreAndRef(totalOffset, staffKey, d)
    
                elif tag in ('wedge', 'bracket', 'dashes'):
                    self.xmlDirectionTypeToSpanners(mxDir)
    
                elif tag == 'segno':
                    rm = repeat.Segno()
                    rm._positionDefaultX = mxDir.get('default-x')
                    rm._positionDefaultY = mxDir.get('default-y')
                    self.insertCoreAndRef(totalOffset, staffKey, rm)
                elif tag == 'coda':
                    rm = repeat.Coda()
                    rm._positionDefaultX = mxDir.get('default-x')
                    rm._positionDefaultY = mxDir.get('default-y')
                    self.insertCoreAndRef(totalOffset, staffKey, rm)
    
                elif tag == 'metronome':
                    mm = self.xmlToTempoIndication(mxDir)
                    # SAX was offsetMeasureNote; bug? should be totalOffset???
                    self.insertCoreAndRef(totalOffset, staffKey, mm)
                elif tag == 'words':
                    te = self.xmlToTextExpression(mxDir)
                    #environLocal.printDebug(['got TextExpression object', repr(te)])
                    # offset here is a combination of the current position
                    # (offsetMeasureNote) and and the direction's offset
                    re = te.getRepeatExpression()
                    if re is not None:
                        # the repeat expression stores a copy of the text
                        # expression within it; replace it here on insertion
                        self.insertCoreAndRef(totalOffset, staffKey, re)
                    else:
                        self.insertCoreAndRef(totalOffset, staffKey, te)

    def xmlToTextExpression(self, mxWords):
        '''
        Given an mxDirection, create a textExpression
        '''
        #environLocal.printDebug(['mxToTextExpression()', mxWords, mxWords.charData])
        # content can be passed with creation argument
        if mxWords.text is None:
            mxWords.text = "" # easier...
        te = expressions.TextExpression(mxWords.text.strip())

        setb = _setAttributeFromAttribute
        setb(te, mxWords, 'justify')
        setb(te, mxWords, 'font-size', 'size', transform=_floatOrIntStr)
        setb(te, mxWords, 'letter-spacing', transform=_floatOrIntStr)
        setb(te, mxWords, 'enclosure')
        setb(te, mxWords, 'default-y', 'positionVertical', transform=_floatOrIntStr)

        # two parameters that are combined
        style = mxWords.get('font-style')
        if style == 'normal':
            style = None

        weight = mxWords.get('font-weight')
        if weight == 'normal':
            weight = None
        if style is not None and weight is not None:
            if style == 'italic' and weight == 'bold':
                te.style = 'bolditalic'
        # one is None
        elif style == 'italic':
            te.style = 'italic'
        elif weight == 'bold':
            te.style = 'bold'

        return te

    def xmlToTempoIndication(self, mxMetronome, mxWords=None):
        '''
        Given an mxMetronome, convert to either a TempoIndication subclass, 
        either a tempo.MetronomeMark or tempo.MetricModulation.
    
        >>> from xml.etree.ElementTree import fromstring as EL
        >>> MP = musicxml.xmlToM21.MeasureParser()
        
        >>> m = EL(r'<metronome><per-minute>125</per-minute><beat-unit>half</beat-unit></metronome>')
        >>> MP.xmlToTempoIndication(m)
        <music21.tempo.MetronomeMark Half=125.0>

        Metric modulation:

        >>> m = EL(r'<metronome><beat-unit>long</beat-unit><beat-unit>32nd</beat-unit><beat-unit-dot/></metronome>')
        >>> MP.xmlToTempoIndication(m)
        <music21.tempo.MetricModulation <music21.tempo.MetronomeMark Imperfect Longa=None>=<music21.tempo.MetronomeMark Dotted 32nd=None>>
        '''
        # get lists of durations and texts
        durations = []
        numbers = []
    
        dActive = None
        for mxObj in mxMetronome:
            tag = mxObj.tag
            if tag == 'beat-unit':
                durationType = musicXMLTypeToType(mxObj.text)
                dActive = duration.Duration(type=durationType)
                durations.append(dActive)   
            elif tag == 'beat-unit-dot':
                if dActive is None:
                    raise MusicXMLImportException('encountered metronome components out of order')
                dActive.dots += 1 # add one dot each time these are encountered
            # should come last
            elif tag == 'per-minute':
                #environLocal.printDebug(['found PerMinute', mxObj])
                # store as a number
                perMin = mxObj.text
                if perMin is not None and perMin.strip() != "":
                    try: 
                        numbers.append(float(perMin))
                    except ValueError:
                        pass # TODO: accept text per minute
        # TODO: metronome-relation -- specifies how to relate multiple beatunits
        # metronomeRelations = mxMetronome.find('metronome-relation')
        if len(durations) > 1: # Metric Modulation!        
            mm = tempo.MetricModulation()
            #environLocal.printDebug(['found metric modulaton:', 'durations', durations])
            if len(durations) < 2:
                raise MusicXMLImportException('found incompletely specified musicxml metric moduation: '+
                                             'fewer than two durations defined')
            # all we have are referents, no values are defined in musicxml
            # will need to update context after adding to Stream
            mm.oldReferent = durations[0]
            mm.newReferent = durations[1]
        else:
            #environLocal.printDebug(['found metronome mark:', 'numbers', numbers])
            mm = tempo.MetronomeMark()
            if len(numbers) > 0:
                mm.number = numbers[0]
            if len(durations) > 0:
                mm.referent = durations[0]
            # TODO: set text if defined in words
            if mxWords is not None:
                pass
    
        paren = mxMetronome.get('parentheses')
        if paren is not None:
            if paren == 'yes':
                mm.parentheses = True
        return mm
        
        
    def xmlToOffset(self, mxObj):
        '''
        Finds an <offset> inside the mxObj and returns it as 
        a music21 offset (in quarterLengths)
        
        >>> from xml.etree.ElementTree import fromstring as EL
        >>> MP = musicxml.xmlToM21.MeasureParser()
        >>> MP.divisions = 40
        >>> off = EL(r'<direction><offset>100</offset></direction>')
        >>> MP.xmlToOffset(off)
        2.5
        '''
        
        try:
            offset = float(mxObj.find('offset').text.strip())
        except (ValueError, AttributeError):
            return 0.0
        return offset/self.divisions
    
    def parseMeasureAttributes(self):        
        self.parseMeasureNumbers()        
        # TODO: implicit
        # TODO: non-controlling 
        # may need to do a format/unit conversion?        
        width = self.mxMeasure.get('width')
        if width is not None:
            width = _floatOrIntStr(width)
            self.stream.layoutWidth = width
        self.divisions = self.parent.lastDivisions
             

    def parseAttributesTag(self, mxAttributes):
        self.attributesAreInternal = False
        self.activeAttributes = mxAttributes
        self.parent.activeAttributes = self.activeAttributes
        for mxSub in mxAttributes:
            meth = None
            # key, clef, time, details
            if mxSub.tag in self.attributeTagsToMethods:
                meth = getattr(self, self.attributeTagsToMethods[mxSub.tag])
            if meth is not None:
                meth(mxSub)
            elif mxSub.tag == 'staves':
                self.staves = int(mxSub.text)
        
        transposeTag = mxAttributes.find('transpose')
        if transposeTag is not None:
            self.transposition = self.xmlTransposeToInterval(transposeTag)
            #environLocal.warn("Got a transposition of ", str(self.transposition) )
        divisionsTag = mxAttributes.find('divisions')
        if divisionsTag is not None:
            self.divisions = common.opFrac(float(divisionsTag.text))
            self.parent.lastDivisions = self.divisions


    def xmlTransposeToInterval(self, mxTranspose):
        '''Convert a MusicXML Transpose object to a music21 Interval object.
        >>> import xml.etree.ElementTree as ET        
        >>> MP = musicxml.xmlToM21.MeasureParser()
        
        >>> t = ET.fromstring('<transpose><diatonic>-1</diatonic><chromatic>-2</chromatic></transpose>')
        >>> MP.xmlTransposeToInterval(t)
        <music21.interval.Interval M-2>
    
        >>> t = ET.fromstring('<transpose><diatonic>-5</diatonic><chromatic>-9</chromatic></transpose>')
        >>> MP.xmlTransposeToInterval(t)
        <music21.interval.Interval M-6>
        
        It should be like this:
        
        >>> t = ET.fromstring('<transpose><diatonic>-8</diatonic><chromatic>-2</chromatic>' + 
        ...         '<octave-change>-1</octave-change></transpose>')
        >>> MP.xmlTransposeToInterval(t)
        <music21.interval.Interval M-9>
        
        but it is sometimes encoded this way (Finale; MuseScore), so we will deal...

        >>> t = ET.fromstring('<transpose><diatonic>-1</diatonic><chromatic>-2</chromatic>' + 
        ...         '<octave-change>-1</octave-change></transpose>')
        >>> MP.xmlTransposeToInterval(t)
        <music21.interval.Interval M-9>
        
        '''
        ds = None
        
        mxDiatonic = mxTranspose.find('diatonic')
        if mxDiatonic is not None:
            ds = int(mxDiatonic.text)
            
        cs = None
        mxChromatic = mxTranspose.find('chromatic')
        if mxChromatic is not None:
            cs = int(mxChromatic.text)
    
        oc = 0
        mxOctaveChange = mxTranspose.find('octave-change')
        if mxOctaveChange is not None:
            oc = int(mxOctaveChange.text) * 12
    
        # TODO: presently not dealing with <double>
        # doubled one octave down from what is currently written 
        # (as is the case for mixed cello / bass parts in orchestral literature)
        #environLocal.printDebug(['ds', ds, 'cs', cs, 'oc', oc])
        if ds is not None and ds != 0 and cs is not None and cs != 0:
            # diatonic step can be used as a generic specifier here if 
            # shifted 1 away from zero
            if ds < 0:
                diatonicActual = ds - 1
            else:
                diatonicActual = ds + 1
            
            try:          
                post = interval.intervalFromGenericAndChromatic(diatonicActual, cs + oc)
            except interval.IntervalException:
                # some people don't use -8 for diatonic for down a 9th, assuming
                # that octave-change will take care of it.  So try again.
                if ds < 0:
                    diatonicActual = (ds + int(oc*7/12)) - 1
                else:
                    diatonicActual = (ds + int(oc*7/12)) + 1

                post = interval.intervalFromGenericAndChromatic(diatonicActual, cs + oc)
                
                
        else: # assume we have chromatic; may not be correct spelling
            post = interval.Interval(cs + oc)
        return post

    def handleTimeSignature(self, mxTime):
        # TODO: interchangeable
        # TODO: senza-misura
        # TODO: attr: separator
        # TODO: attr: symbol
        # TODO: attr: number (done?)
        # TODO: print-style-align
        # TODO: print-object
        ts = self.xmlToTimeSignature(mxTime)
        self.insertCoreAndRef(0, mxTime, ts)
        
    def xmlToTimeSignature(self, mxTime):
        '''
        >>> import xml.etree.ElementTree as ET
        >>> mxTime = ET.fromstring('<time><beats>3</beats><beat-type>8</beat-type></time>')
        
        >>> MP = musicxml.xmlToM21.MeasureParser()
        >>> MP.xmlToTimeSignature(mxTime)
        <music21.meter.TimeSignature 3/8>      
        '''
        n = []
        d = []
        # just get first one for now;
        for beatOrType in mxTime:
            if beatOrType.tag == 'beats':
                n.append(beatOrType.text) # may be 3+2
            elif beatOrType.tag == 'beat-type':
                d.append(beatOrType.text)
        # convert into a string
        msg = []
        for i in range(len(n)):
            msg.append('%s/%s' % (n[i], d[i]))
    
        #environLocal.warn(['loading meter string:', '+'.join(msg)])
        if len(msg) == 1: # normal
            ts = meter.TimeSignature(msg[0])
        else:
            ts = meter.TimeSignature()
            ts.load('+'.join(msg))
        
        return ts
        
    def handleClef(self, mxClef):
        clefObj = self.xmlToClef(mxClef)
        self.insertCoreAndRef(self.offsetMeasureNote, mxClef, clefObj)
    
    def xmlToClef(self, mxClef):
        '''
        >>> import xml.etree.ElementTree as ET
        >>> mxClef = ET.fromstring('<clef><sign>G</sign><line>2</line></clef>')
        
        >>> MP = musicxml.xmlToM21.MeasureParser()
        >>> MP.xmlToClef(mxClef)
        <music21.clef.TrebleClef>        

        >>> mxClef = ET.fromstring('<clef><sign>TAB</sign></clef>')
        >>> MP.xmlToClef(mxClef)
        <music21.clef.TabClef>        
        '''
        sign = mxClef.find('sign').text.strip()
        if sign.lower() in ('tab', 'percussion', 'none', 'jianpu'):
            clefObj = clef.clefFromString(sign)
        else:
            line = mxClef.find('line').text.strip()
            mxOctaveChange = mxClef.find('clef-octave-change')
            if mxOctaveChange != None:
                octaveChange = int(mxOctaveChange.text)
            else:
                octaveChange = 0
            clefObj = clef.clefFromString(sign + line, octaveChange)
    
        # TODO: number
        # TODO: additional
        # TODO: size
        # TODO: after-barline
        # TODO: print-style
        # TODO: print-object
    
        return clefObj
        
    def handleKeySignature(self, mxKey):
        keySig = self.xmlToKeySignature(mxKey)
        self.insertCoreAndRef(0, mxKey, keySig)

    def xmlToKeySignature(self, mxKey):
        '''
        >>> import xml.etree.ElementTree as ET
        >>> mxKey = ET.fromstring('<key><fifths>-4</fifths><mode>minor</mode></key>')
        
        >>> MP = musicxml.xmlToM21.MeasureParser()
        >>> MP.xmlToKeySignature(mxKey)
        <music21.key.KeySignature of 4 flats, mode minor>
        '''
        ks = key.KeySignature()
        seta = _setAttributeFromTagText
        seta(ks, mxKey, 'fifths', 'sharps', transform=int)
        seta(ks, mxKey, 'mode')
        return ks
    
    def handleStaffDetails(self, mxDetails):
        '''
        StaffDetails (staff-details) handles attributes about
        the staff itself -- its size, number of lines, tuning,
        frets, etc.
        
        It is different from StaffLayout (staff-layout) which
        only handles relationship of one staff to another (the
        distance)
        
        Rather than returning a StaffLayout object,
        it adds it to self.staffLayoutObjects checking
        to see if there is already an incomplete
        StaffLayout object for this staff.
        '''
        seta = _setAttributeFromTagText
        # staffNumber refers to the staff number for this Part -- i.e., usually None or 1
        # except for a piano score, etc.
        #ET.dump(mxDetails)

        staffNumber = mxDetails.get('number')
        foundMatch = False
        if staffNumber is not None:
            staffNumber = int(staffNumber)
            for stl in self.staffLayoutObjects: # staff layout objects in this part
                if stl.staffNumber == staffNumber:
                    try:
                        seta(stl, mxDetails, 'staff-size', transform=_floatOrIntStr)
                    except TypeError:
                        staffSize = mxDetails.find('staff-size')
                        if staffSize is not None:
                            raise TypeError("Incorrect number for mxStaffDetails.staffSize: %s", staffSize)
                    # get staff-lines too?
                    foundMatch = True
                    break
        else:
            # applies to all staves...
            for stl in self.staffLayoutObjects: # staff layout objects in this part
                if stl.staffSize is None: # override...
                    seta(stl, mxDetails, 'staff-size', transform=_floatOrIntStr)
                    foundMatch = True
                if stl.staffLines is None:
                    seta(stl, mxDetails, 'staff-lines', transform=int)
                    foundMatch = True

        # no staffLayoutObjects or none that match on number
        # TODO: staff-type (ossia, cue, editorial, regular, alternate)
        # TODO: staff-tuning*
        # TODO: capo
        # TODO: show-frets
        # TODO: print-object
        # TODO: print-spacing
        
        if foundMatch is False:
            stl = self.xmlStaffLayoutFromStaffDetails(mxDetails)
            
            # should this be 0.0 or current offset?
            self.insertCoreAndRef(0.0, mxDetails, stl)
            self.staffLayoutObjects.append(stl)

    def xmlStaffLayoutFromStaffDetails(self, mxDetails):
        '''
        Returns a new StaffLayout object from staff-details.
        '''
        seta = _setAttributeFromTagText
        
        stl = layout.StaffLayout()
        seta(stl, mxDetails, 'staff-size', transform=_floatOrIntStr)
        seta(stl, mxDetails, 'staff-lines', transform=int)
        staffNumber = mxDetails.get('number')
        if staffNumber is not None:
            stl.staffNumber = int(staffNumber)
        staffPrinted = mxDetails.get('print-object')
        if staffPrinted == 'no' or staffPrinted is False:
            stl.hidden = True
        elif staffPrinted == 'yes' or staffPrinted is True:
            stl.hidden = False
        return stl
               

    
    def parseMeasureNumbers(self):
        m = self.stream
        lastMNum = self.parent.lastMeasureNumber
        lastMSuffix = self.parent.lastNumberSuffix
        
        mNumRaw = self.mxMeasure.get('number')
        if mNumRaw is None:
            mNum = None
            mSuffix = None
        else:
            mNum, mSuffix = common.getNumFromStr(mNumRaw)
        
        # assume that measure numbers are integers
        if mNum not in (None, ''):
            m.number = int(mNum)
        if mSuffix not in (None, ''):
            m.numberSuffix = mSuffix
    
        # fix for Finale which calls unnumbered measures X1, X2, etc. which
        # we convert to 1.X, 2.X, etc. without this...
        if lastMNum is not None:
            if m.numberSuffix == 'X' and m.number != lastMNum + 1:
                newSuffix = m.numberSuffix + str(m.number)
                if lastMSuffix is not None:
                    newSuffix = lastMSuffix + newSuffix
                m.number = lastMNum
                m.numberSuffix = newSuffix 
                   
        self.measureNumber = m.number
        self.numberSuffix = m.numberSuffix
        
    def updateVoiceInformation(self):
        mxm = self.mxMeasure
        for mxn in mxm.findall('note'):
            voice = mxn.find('voice')
            if voice is not None and voice.text is not None:
                vIndex = voice.text.strip()
                self.voiceIndices.add(vIndex)
                # it is a set, so no need to check if already there
                # additional time < 1 sec per ten million ops.
        
        if len(self.voiceIndices) > 1:
            for vIndex in sorted(self.voiceIndices):
                v = stream.Voice()
                v.id = vIndex
                self.stream._insertCore(0.0, v)
            self.useVoices = True
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------


class Test(unittest.TestCase):
    pass

    def testParseSimple(self):
        MI = MusicXMLImporter()
        MI.xmlText = r'''<score-timewise />'''
        self.assertRaises(MusicXMLImportException, MI.parseXMLText)

    def EL(self, elText):
        return ET.fromstring(elText)

    def pitchOut(self, listIn):
        '''
        make it so that the tests that look for the old-style pitch.Pitch 
        representation still work.
        '''
        out = "["
        for p in listIn:
            out += str(p) + ', '
        out = out[0:len(out)-2]
        out += "]"
        return out


    def testBarRepeatConversion(self):
        from music21 import corpus
        #a = converter.parse(testPrimitive.simpleRepeat45a)
        # this is a good example with repeats
        s = corpus.parse('k80/movement3')
        for p in s.parts:
            post = p.flat.getElementsByClass('Repeat')
            self.assertEqual(len(post), 6)

        #a = corpus.parse('opus41no1/movement3')
        #s.show()

    def testVoices(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.voiceDouble)
        m1 = s.parts[0].getElementsByClass('Measure')[0]
        self.assertEqual(m1.hasVoices(), True)

        self.assertEqual([v.id for v in m1.voices], [u'1', u'2'])

        self.assertEqual([e.offset for e in m1.voices[0]], [0.0, 1.0, 2.0, 3.0])
        self.assertEqual([e.offset for e in m1.voices['1']], [0.0, 1.0, 2.0, 3.0])

        self.assertEqual([e.offset for e in m1.voices[1]], [0.0, 2.0, 2.5, 3.0, 3.5])
        self.assertEqual([e.offset for e in m1.voices['2']], [0.0, 2.0, 2.5, 3.0, 3.5])
        #s.show()


    def testSlurInputA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.spannersSlurs33c)
        # have 10 spanners
        self.assertEqual(len(s.flat.getElementsByClass('Spanner')), 5)

        # can get the same from a getAll search
        self.assertEqual(len(s.getAllContextsByClass('Spanner')), 5)

        # try to get all spanners from the first note
        self.assertEqual(len(s.flat.notesAndRests[0].getAllContextsByClass('Spanner')), 5)
        #s.show('t')
        #s.show()


    def testMultipleStavesPerPartA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.pianoStaff43a)
        self.assertEqual(len(s.parts), 2)
        #s.show()
        self.assertEqual(len(s.parts[0].flat.getElementsByClass('Note')), 1)
        self.assertEqual(len(s.parts[1].flat.getElementsByClass('Note')), 1)

        self.assertEqual(isinstance(s.parts[0], stream.PartStaff), True)
        self.assertEqual(isinstance(s.parts[1], stream.PartStaff), True)


    def testMultipleStavesPerPartB(self):
        from music21 import converter
        from music21.musicxml import testFiles

        s = converter.parse(testFiles.moussorgskyPromenade) # @UndefinedVariable
        self.assertEqual(len(s.parts), 2)

        self.assertEqual(len(s.parts[0].flat.getElementsByClass('Note')), 19)
        # only chords in the second part
        self.assertEqual(len(s.parts[1].flat.getElementsByClass('Note')), 0)

        self.assertEqual(len(s.parts[0].flat.getElementsByClass('Chord')), 11)
        self.assertEqual(len(s.parts[1].flat.getElementsByClass('Chord')), 11)

        #s.show()


    def testMultipleStavesPerPartC(self):
        from music21 import corpus
        s = corpus.parse('schoenberg/opus19/movement2')
        self.assertEqual(len(s.parts), 2)

        s = corpus.parse('schoenberg/opus19/movement6')
        self.assertEqual(len(s.parts), 2)

        #s.show()


    def testSpannersA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.spanners33a)
        # this number will change as more are being imported
        self.assertEqual(len(s.flat.spanners) >= 2, True)


        #environLocal.printDebug(['pre s.measures(2,3)', 's', s])
        ex = s.measures(2, 3) # this needs to get all spanners too

        # all spanners are referenced over; even ones that may not be relevant
        self.assertEqual(len(ex.flat.spanners), 14)
        #ex.show()

        # slurs are on measures 2, 3
        # crescendos are on measures 4, 5
        # wavy lines on measures 6, 7
        # brackets etc. on measures 10-14
        # glissando on measure 16


    def testTextExpressionsA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.textExpressions)
        #s.show() 
        self.assertEqual(len(s.flat.getElementsByClass('TextExpression')), 3)

        p1 = s.parts[0]
        m1 = p1.getElementsByClass('Measure')[0]
        self.assertEqual(len(m1.getElementsByClass('TextExpression')), 0)
        # all in measure 2
        m2 = p1.getElementsByClass('Measure')[1]
        self.assertEqual(len(m2.getElementsByClass('TextExpression')), 3)

        teStream = m2.getElementsByClass('TextExpression')
        self.assertEqual([te.offset for te in teStream], [1.0, 1.5, 4.0])

        #s.show()


    def testTextExpressionsC(self):
        from music21 import corpus
        s = corpus.parse('bwv66.6')
        p = s.parts[0]
        for m in p.getElementsByClass('Measure'):
            for n in m.flat.notes:
                if n.pitch.name in ['B']:
                    msg = '%s\n%s' % (n.pitch.nameWithOctave, n.duration.quarterLength)
                    te = expressions.TextExpression(msg)
                    te.size = 14
                    te.style = 'bold'
                    te.justify = 'center'
                    te.enclosure = 'rectangle'
                    te.positionVertical = -80
                    m.insert(n.offset, te)
        #p.show()        


    def testTextExpressionsD(self):
        from music21 import corpus
        # test placing text expression in arbitrary locations
        s = corpus.parse('bwv66.6')
        p = s.parts[-1] # get bass
        for m in p.getElementsByClass('Measure')[1:]:
            for pos in [1.5, 2.5]:
                te = expressions.TextExpression(pos)
                te.style = 'bold'
                te.justify = 'center'
                te.enclosure = 'rectangle'
                m.insert(pos, te)
        #p.show()

    def testTextExpressionsE(self):
        import random
        s = stream.Stream()
        for i in range(6):
            m = stream.Measure(number=i + 1)
            m.append(layout.SystemLayout(isNew=True))
            m.append(note.Rest(type='whole'))
            s.append(m)
        for m in s.getElementsByClass('Measure'):
            offsets = [x * .25 for x in range(16)]
            random.shuffle(offsets)
            offsets = offsets[:4]
            for o in offsets:
                te = expressions.TextExpression(o)
                te.style = 'bold'
                te.justify = 'center'
                te.enclosure = 'rectangle'
                m.insert(o, te)
        #s.show()      



    def testImportRepeatExpressionsA(self):
        # test importing from musicxml
        from music21.musicxml import testPrimitive
        from music21 import converter

        # has one segno
        s = converter.parse(testPrimitive.repeatExpressionsA)
        self.assertEqual(len(s.flat.getElementsByClass(repeat.Segno)), 1)
        self.assertEqual(len(s.flat.getElementsByClass(repeat.Fine)), 1)
        self.assertEqual(len(s.flat.getElementsByClass(repeat.DalSegnoAlFine)), 1)

        # has two codas
        s = converter.parse(testPrimitive.repeatExpressionsB)
        self.assertEqual(len(s.flat.getElementsByClass(repeat.Coda)), 2)
        # has one d.c.al coda
        self.assertEqual(len(s.flat.getElementsByClass(repeat.DaCapoAlCoda)), 1)

    def testImportRepeatBracketA(self):
        from music21 import corpus
        # has repeats in it; start with single emasure
        s = corpus.parse('opus74no1', 3)
        # there are 2 for each part, totaling 8
        self.assertEqual(len(s.flat.getElementsByClass('RepeatBracket')), 8)
        # can get for each part as spanners are stored in Part now

        # TODO: need to test getting repeat brackets after measure extraction
        #s.parts[0].show() # 72 through 77
        sSub = s.parts[0].measures(72, 77)
        # 2 repeat brackets are gathered b/c they are stored at the Part by 
        # default
        rbSpanners = sSub.getElementsByClass('RepeatBracket')
        self.assertEqual(len(rbSpanners), 2)


    def testImportVoicesA(self):
        # testing problematic voice imports

        from music21.musicxml import testPrimitive
        from music21 import converter
        # this 2 part segments was importing multiple voices within
        # a measure, even though there was no data in the second voice
        s = converter.parse(testPrimitive.mixedVoices1a)
        #s.show('text')
        self.assertEqual(len(s.parts), 2)
        # there are voices, but they have been removed
        self.assertEqual(len(s.parts[0].getElementsByClass(
            'Measure')[0].voices), 0)

        #s.parts[0].show('t')
        #self.assertEqual(len(s.parts[0].voices), 2)
        s = converter.parse(testPrimitive.mixedVoices1b)
        self.assertEqual(len(s.parts), 2)
        self.assertEqual(len(s.parts[0].getElementsByClass(
            'Measure')[0].voices), 0)
        #s.parts[0].show('t')

        # this case, there were 4, but there should be 2
        s = converter.parse(testPrimitive.mixedVoices2)
        self.assertEqual(len(s.parts), 2)
        self.assertEqual(len(s.parts[0].getElementsByClass(
            'Measure')[0].voices), 2)
        self.assertEqual(len(s.parts[1].getElementsByClass(
            'Measure')[0].voices), 2)

        #s.parts[0].show('t')

#         s = converter.parse(testPrimitive.mixedVoices1b)
#         s = converter.parse(testPrimitive.mixedVoices2)


    def testImportMetronomeMarksA(self):
        from music21.musicxml import testPrimitive
        from music21 import converter
        # has metronome marks defined, not with sound tag
        s = converter.parse(testPrimitive.metronomeMarks31c)
        # get all tempo indications
        mms = s.flat.getElementsByClass('TempoIndication')
        self.assertEqual(len(mms) > 3, True)


    def testImportMetronomeMarksB(self):
        pass
        # TODO: look for files that only have sound tags and create MetronomeMarks
        # need to look for bundling of Words text expressions with tempo

        # has only sound tempo=x tag
        #s = converter.parse(testPrimitive.articulations01)
        #s.show()

    def testImportGraceNotesA(self):
        # test importing from musicxml
        from music21.musicxml import testPrimitive
        from music21 import converter
        unused_s = converter.parse(testPrimitive.graceNotes24a)

        #s.show()

    def testChordalStemDirImport(self):
        #NB: Finale apparently will not display a pitch that is a member of a chord without a stem
        #unless all chord members are without stems.
        from music21.musicxml import m21ToString
        from music21 import converter

        n1 = note.Note('f3')
        n1.notehead = 'diamond'
        n1.stemDirection = 'down'
        n2 = note.Note('c4')
        n2.stemDirection = 'noStem'
        c = chord.Chord([n1, n2])
        c.quarterLength = 2
        
        xml = m21ToString.fromMusic21Object(c)
        #print xml
        #c.show()
        inputStream = converter.parse(xml)
        chordResult = inputStream.flat.notes[0]
#         for n in chordResult:
#             print n.stemDirection       

        self.assertEqual(chordResult.getStemDirection(chordResult.pitches[0]), 'down')
        self.assertEqual(chordResult.getStemDirection(chordResult.pitches[1]), 'noStem')


    def testStaffGroupsA(self):
        from music21.musicxml import testPrimitive
        from music21 import converter

        s = converter.parse(testPrimitive.staffGroupsNested41d)
        staffGroups = s.getElementsByClass('StaffGroup')
        #staffGroups.show()
        self.assertEqual(len(staffGroups), 2)
        sgs = s.getElementsByClass('StaffGroup')

        sg1 = sgs[0]
        self.assertEqual(sg1.symbol, 'line')
        self.assertEqual(sg1.barTogether, True)

        
        sg2 = sgs[1] # Order is right here, was wrong in fromMxObjects
        self.assertEqual(sg2.symbol, 'brace')
        self.assertEqual(sg2.barTogether, True)


        # TODO: more tests about which parts are there...

    def testInstrumentTranspositionA(self):
        from music21.musicxml import testPrimitive
        from music21 import converter

        s = converter.parse(testPrimitive.transposingInstruments72a)
        i1 = s.parts[0].flat.getElementsByClass('Instrument')[0]
        i2 = s.parts[1].flat.getElementsByClass('Instrument')[0]
        unused_i3 = s.parts[2].flat.getElementsByClass('Instrument')[0]

        self.assertEqual(str(i1.transposition), '<music21.interval.Interval M-2>')
        self.assertEqual(str(i2.transposition), '<music21.interval.Interval M-6>')


    def testInstrumentTranspositionB(self):
        from music21.musicxml import testPrimitive
        from music21 import converter

        s = converter.parse(testPrimitive.transposing01)
        # three parts
        # Oboe -> English Horn -> Oboe
        # Cl Bb -> Cl A -> Cl Bb
        # F-horn in F
        # N.B. names dont change just transpositions.
        # all playing A4 in concert pitch.
        
        
        iStream1 = s.parts[0].flat.getElementsByClass('Instrument')
        # three instruments; one initial, and then one for each transposition
        self.assertEqual(len(iStream1), 3)
        # should be 3
        iStream2 = s.parts[1].flat.getElementsByClass('Instrument')
        self.assertEqual(len(iStream2), 3)
        #i2 = iStream2[0]

        iStream3 = s.parts[2].flat.getElementsByClass('Instrument')
        self.assertEqual(len(iStream3), 1)
        i3 = iStream3[0]


        self.assertEqual(str(iStream1[0].transposition), 'None')
        self.assertEqual(str(iStream1[1].transposition), '<music21.interval.Interval P-5>')
        self.assertEqual(str(iStream1[2].transposition), '<music21.interval.Interval P1>')

        self.assertEqual(str(iStream2[0].transposition), '<music21.interval.Interval M-2>')
        self.assertEqual(str(iStream2[1].transposition), '<music21.interval.Interval m3>')

        self.assertEqual(str(i3.transposition), '<music21.interval.Interval P-5>')

        self.assertEqual(self.pitchOut([p for p in s.parts[0].flat.pitches]), '[A4, A4, A4, A4, A4, A4, A4, A4, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, A4, A4, A4, A4]')
        self.assertEqual(self.pitchOut([p for p in s.parts[1].flat.pitches]), '[B4, B4, B4, B4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, B4, B4, B4, B4, B4, B4]')
        self.assertEqual(self.pitchOut([p for p in s.parts[2].flat.pitches]), '[E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5]')

        self.assertFalse(s.parts[0].flat.atSoundingPitch)

        sSounding = s.toSoundingPitch(inPlace=False)

        self.assertEqual(self.pitchOut([p for p in sSounding.parts[0].flat.pitches]), '[A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4]')
        self.assertEqual(self.pitchOut([p for p in sSounding.parts[1].flat.pitches]), '[A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4]')
        self.assertEqual(self.pitchOut([p for p in sSounding.parts[2].flat.pitches]), '[A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4]')

        # chordification by default places notes at sounding pitch
        sChords = s.chordify()
        self.assertEqual(self.pitchOut([p for p in sChords.flat.pitches]), '[A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4]')
        #sChords.show()


    def testInstrumentTranspositionC(self):
        # generate all transpositions on output
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.transposing01)
        instStream = s.flat.getElementsByClass('Instrument')
        #for i in instStream:
        #    print(i.offset, i, i.transposition)
        self.assertEqual(len(instStream), 7)
        #s.show()



    def testHarmonyA(self):
        from music21 import corpus

        s = corpus.parse('leadSheet/berlinAlexandersRagtime.xml')
        self.assertEqual(len(s.flat.getElementsByClass('ChordSymbol')), 19)

        match = [h.chordKind for h in s.flat.getElementsByClass('ChordSymbol')]
        self.assertEqual(match, [u'major', u'dominant', u'major', u'major', u'major', u'major', u'dominant', u'major', u'dominant', u'major', u'dominant', u'major', u'dominant', u'major', u'dominant', u'major', u'dominant', u'major', u'major'])

        match = [str(h.root()) for h in s.flat.getElementsByClass('ChordSymbol')]
        
        self.assertEqual(match, ['F3', 'C3', 'F3', 'B-2', 'F3', 'C3', 'G2', 'C3', 'C3', 'F3', 'C3', 'F3', 'F2', 'B-2', 'F2', 'F3', 'C3', 'F3', 'C3'])

        match = set([str(h.figure) for h in s.flat.getElementsByClass('ChordSymbol')])
        
        self.assertEqual(match, set(['F','F7','B-','C7','G7','C']))


        s = corpus.parse('monteverdi/madrigal.3.12.xml')
        self.assertEqual(len(s.flat.getElementsByClass('ChordSymbol')), 10)

        s = corpus.parse('leadSheet/fosterBrownHair.xml')
        self.assertEqual(len(s.flat.getElementsByClass('ChordSymbol')), 40)

        #s.show()

    def xtestOrnamentandTechnical(self):
        from music21 import converter
        beeth = common.getCorpusFilePath() + '/beethoven/opus133.mxl'
        # TODO: this is way too long... lots of hidden 32nd notes for trills...
        s = converter.parse(beeth, forceSource=True, format='musicxml')
        ex = s.parts[0]
        countTrill = 0
        for n in ex.flat.notes:
            for e in n.expressions:
                if 'Trill' in e.classes:
                    countTrill += 1
        self.assertEqual(countTrill, 54)
        
        # TODO: Get a better test... the single harmonic in the viola part, 
        # m. 482 is probably a mistake for an open string.
        countTechnical = 0
        for n in s.parts[2].flat.notes:
            for a in n.articulations:
                if 'TechnicalIndication' in a.classes:
                    countTechnical += 1
        self.assertEqual(countTechnical, 1)

    def testOrnamentC(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        # has many ornaments
        s = converter.parse(testPrimitive.notations32a)

        #s.flat.show('t')
        self.assertEqual(len(s.flat.getElementsByClass('TremoloSpanner')), 0) # no spanned tremolos
        
        count = 0
        for n in s.flat.notes:
            for e in n.expressions:
                if 'Tremolo' in e.classes:
                    count += 1
        self.assertEqual(count, 1) # One single Tremolo


        count = 0
        for n in s.flat.notes:
            for e in n.expressions:
                if 'Turn' in e.classes:
                    count += 1
        self.assertEqual(count, 4) # include inverted turn

        count = 0
        for n in s.flat.notes:
            for e in n.expressions:
                if 'InvertedTurn' in e.classes:
                    count += 1
        self.assertEqual(count, 1)

        count = 0
        for n in s.flat.notes:
            for e in n.expressions:
                if 'Shake' in e.classes:
                    count += 1
        self.assertEqual(count, 1)

        count = 0
        for n in s.flat.notes:
            for e in n.expressions:
                if 'Schleifer' in e.classes:
                    count += 1
        self.assertEqual(count, 1)

    def testTextBoxA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.textBoxes01)
        tbs = s.flat.getElementsByClass('TextBox')
        self.assertEqual(len(tbs), 5)

        msg = []
        for tb in tbs:
            msg.append(tb.content)
        self.assertEqual(msg, [u'This is a text box!', u'pos 200/300 (lower left)', u'pos 1000/300 (lower right)', u'pos 200/1500 (upper left)', u'pos 1000/1500 (upper right)'])

    def testImportSlursA(self):
        from music21 import corpus
        # this is a good test as this encoding uses staffs, not parts
        # to encode both parts; this requires special spanner handling
        s = corpus.parse('mozart/k545/movement1_exposition')
        sf = s.flat       
        slurs = sf.getElementsByClass(spanner.Slur)
        # TODO: this value should be 2, but due to staff encoding we 
        # have orphaned spanners that are not cleaned up
        self.assertEqual(len(slurs), 4)

        n1, n2 = s.parts[0].flat.notes[3], s.parts[0].flat.notes[5]
        #environLocal.printDebug(['n1', n1, 'id(n1)', id(n1), slurs[0].getSpannedElementIds(), slurs[0].getSpannedElementIds()])
        self.assertEqual(id(n1) == slurs[0].getSpannedElementIds()[0], True)
        self.assertEqual(id(n2) == slurs[0].getSpannedElementIds()[1], True)

        #environLocal.printDebug(['n2', n2, 'id(n2)', id(n2), slurs[0].getSpannedElementIds()])


    def testImportWedgeA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.spanners33a)
        self.assertEqual(len(s.flat.getElementsByClass('Crescendo')), 1)
        self.assertEqual(len(s.flat.getElementsByClass('Diminuendo')), 1)


    def testImportWedgeB(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        # this produces a single component cresc
        s = converter.parse(testPrimitive.directions31a)
        self.assertEqual(len(s.flat.getElementsByClass('Crescendo')), 2)


    def testBracketImportB(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.spanners33a)
        #s.show()
        self.assertEqual(len(s.flat.getElementsByClass('Line')), 6)


    def testTrillExtensionImportA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive
        s = converter.parse(testPrimitive.notations32a)
        #s.show()
        self.assertEqual(len(s.flat.getElementsByClass('TrillExtension')), 2)


    def testGlissandoImportA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive
        s = converter.parse(testPrimitive.spanners33a)
        #s.show()
        self.assertEqual(len(s.flat.getElementsByClass('Glissando')), 1)


    def testImportDashes(self):
        # dashes are imported as Lines (as are brackets)
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.spanners33a, forceSource=True, format='musicxml')
        self.assertEqual(len(s.flat.getElementsByClass('Line')), 6)


    def testImportGraceA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.graceNotes24a)
        #s.show()        
        match = [str(p) for p in s.pitches]
        #print match
        self.assertEqual(match, ['D5', 'C5', 'E5', 'D5', 'C5', 'D5', 'C5', 'D5', 'C5', 'D5', 'C5', 'E5', 'D5', 'C5', 'D5', 'C5', 'D5', 'C5', 'E5', 'E5', 'F4', 'C5', 'D#5', 'C5', 'D-5', 'A-4', 'C5', 'C5'])


    def testBarException(self):
        MP = MeasureParser()
        mxBarline = self.EL('<barline><bar-style>light-heavy</bar-style></barline>')
        #Rasing the BarException
        self.assertRaises(bar.BarException, MP.xmlToRepeat, mxBarline)

        mxBarline = self.EL('<barline><bar-style>light-heavy</bar-style><repeat direction="backward"/></barline>')

        #all fine now, no exceptions here
        MP.xmlToRepeat(mxBarline)

        #Raising the BarException       
        mxBarline = self.EL('<barline><bar-style>wunderbar</bar-style></barline>')
        self.assertRaises(bar.BarException, MP.xmlToRepeat, mxBarline)

    def testStaffLayout(self):
        from music21 import corpus, converter
        c = converter.parse(corpus.getWorkList('demos/layoutTest.xml')[0], format='musicxml', forceSource=True)
        #c = corpus.parse('demos/layoutTest.xml')        
        layouts = c.flat.getElementsByClass('LayoutBase')
        systemLayouts = layouts.getElementsByClass('SystemLayout')
        self.assertEqual(len(systemLayouts), 42)
        staffLayouts = layouts.getElementsByClass('StaffLayout')
#         for i,p in enumerate(c.parts):
#             print(i)
#             for l in p.flat.getElementsByClass('StaffLayout'):
#                 print(l.distance)        
        self.assertEqual(len(staffLayouts), 20)
        pageLayouts = layouts.getElementsByClass('PageLayout')
        self.assertEqual(len(pageLayouts), 10)
        scoreLayouts = layouts.getElementsByClass('ScoreLayout')
        self.assertEqual(len(scoreLayouts), 1)
        #score1 = scoreLayouts[0]
        #for sltemp in score1.staffLayoutList:
        #    print(sltemp, sltemp.distance)
        
        
        self.assertEqual(len(layouts), 73)

        sl0 = systemLayouts[0]
        self.assertEqual(sl0.distance, None)
        self.assertEqual(sl0.topDistance, 211.0)
        self.assertEqual(sl0.leftMargin, 70.0)
        self.assertEqual(sl0.rightMargin, 0.0)

        sizes = []
        for s in staffLayouts:
            if s.staffSize is not None:
                sizes.append(s.staffSize)
        self.assertEqual(sizes, [80.0, 120.0, 80.0])

    def testStaffLayoutMore(self):
        from music21 import corpus, converter
        c = converter.parse(corpus.getWorkList('demos/layoutTestMore.xml')[0], format='musicxml', forceSource=True)
        #c = corpus.parse('demos/layoutTest.xml')        
        layouts = c.flat.getElementsByClass('LayoutBase')
        self.assertEqual(len(layouts), 76)
        systemLayouts = layouts.getElementsByClass('SystemLayout')
        sl0 = systemLayouts[0]
        self.assertEqual(sl0.distance, None)
        self.assertEqual(sl0.topDistance, 211.0)
        self.assertEqual(sl0.leftMargin, 70.0)
        self.assertEqual(sl0.rightMargin, 0.0)
#         for s in layouts:
#             if hasattr(s, 'staffSize'):
#                 print(s, s.staffSize)
                
        staffLayouts = layouts.getElementsByClass('StaffLayout')
        sizes = []
        for s in staffLayouts:
            if s.staffSize is not None:
                sizes.append(s.staffSize)
        self.assertEqual(sizes, [80.0, 120.0, 80.0])
        

    def testCountDynamics(self):
        '''
        good test of both dynamics and a partstaff...
        '''
        from music21 import  corpus, converter
        c = converter.parse(corpus.getWorkList('schoenberg/opus19/movement2.mxl')[0], format='musicxml', forceSource=True)
        dynAll = c.flat.getElementsByClass('Dynamic')
        self.assertEqual(len(dynAll), 6)
        notesOrChords = (note.Note, chord.Chord)
        allNotesOrChords = c.flat.getElementsByClass(notesOrChords)
        self.assertEqual(len(allNotesOrChords), 50)
        allChords = c.flat.getElementsByClass('Chord')
        self.assertEqual(len(allChords), 45)
        pCount = 0
        for cc in allChords:
            pCount += len(cc.pitches)
        self.assertEqual(pCount, 97)
        
    def xtestLucaGloriaSpanners(self):
        '''
        lots of lines, including overlapping here
        
        problem in m. 99 of part 2 -- spanner seems to be in the score
        but not being output to musicxml -- REASON: toMxObjects cannot handle
        spanners on rests! fix...
        '''
        from music21 import  corpus, converter
        c = converter.parse(corpus.getWorkList('luca/gloria.xml')[0], format='musicxml', forceSource=True)
        print(c.parts[1].measure(99).notesAndRests[0].getSpannerSites()[0].idLocal)
        #c.show()
        #c.parts[1].show('t')
        

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
    
    
    
    
    
    
