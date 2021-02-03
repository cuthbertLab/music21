# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         musicxml/xmlToM21.py
# Purpose:      Conversion from MusicXML to Music21
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-2019 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
import copy
import fractions
import io
import math
# import pprint
import re
# import sys
# import traceback
import unittest
from typing import List, Optional, Dict, Tuple

import xml.etree.ElementTree as ET

from music21 import common
from music21 import exceptions21
from music21.musicxml import xmlObjects
from music21.musicxml.xmlObjects import MusicXMLImportException

# modules that import this include converter.py.
# thus, cannot import these here
from music21 import articulations
from music21 import bar
from music21 import base  # for typing
from music21 import beam
from music21 import chord
from music21 import clef
from music21 import defaults
from music21 import duration
from music21 import dynamics
from music21 import editorial
from music21 import expressions
from music21 import harmony  # for chord symbols
from music21 import instrument
from music21 import interval  # for transposing instruments
from music21 import key
from music21 import layout
from music21 import metadata
from music21 import note
from music21 import meter
from music21 import pitch
from music21 import repeat
from music21 import spanner
from music21 import stream
from music21 import style
from music21 import tablature
from music21 import tempo
from music21 import text  # for text boxes
from music21 import tie

from music21 import environment

_MOD = 'musicxml.xmlToM21'
environLocal = environment.Environment(_MOD)

# what goes in a `.staffReference`
StaffReferenceType = Dict[int, List[base.Music21Object]]

# const
NO_STAFF_ASSIGNED = 0


# ------------------------------------------------------------------------------
# Helpers...
def _clean(badStr: Optional[str]) -> Optional[str]:
    # need to remove badly-formed strings
    if badStr is None:
        return None
    badStr = badStr.strip()
    goodStr = badStr.replace('\n', ' ')
    return goodStr


# Durations

def textNotNone(mxObj):
    '''
    returns True is mxObj is not None
    and mxObj.text is not None

    >>> from xml.etree.ElementTree import Element, SubElement
    >>> e = Element('an-element')
    >>> musicxml.xmlToM21.textNotNone(e)
    False
    >>> e.text = 'hello'
    >>> musicxml.xmlToM21.textNotNone(e)
    True
    '''
    if mxObj is None:
        return False
    if not hasattr(mxObj, 'text'):
        return False
    if mxObj.text is None:
        return False
    return True


def textStripValid(mxObj):
    '''
    returns True if textNotNone(mxObj)
    and mxObj.text.strip() is not empty

    >>> from xml.etree.ElementTree import Element, SubElement
    >>> e = Element('an-element')
    >>> musicxml.xmlToM21.textStripValid(e)
    False
    >>> e.text = '    '
    >>> musicxml.xmlToM21.textStripValid(e)
    False
    >>> e.text = 'hello'
    >>> musicxml.xmlToM21.textStripValid(e)
    True
    '''
    if not textNotNone(mxObj):
        return False
    if not mxObj.text.strip():
        return False
    return True


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
    music21.musicxml.xmlObjects.MusicXMLImportException:
        found unknown MusicXML type: None
    '''
    # MusicXML uses long instead of longa
    if value not in duration.typeToDuration:
        if value == 'long':
            return 'longa'
        elif value == '32th':
            return '32nd'
        else:
            raise MusicXMLImportException(f'found unknown MusicXML type: {value}')
    else:
        return value


def _floatOrIntStr(strObj):
    '''
    Convert a string to float or int if possible...

    >>> _f = musicxml.xmlToM21._floatOrIntStr
    >>> _f('20.3')
    20.3
    >>> _f('20.0')
    20
    >>> _f(None) is None
    True
    >>> _f('hi')
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


def _setAttributeFromAttribute(m21El, xmlEl, xmlAttributeName,
                               attributeName=None, transform=None):
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
    value = xmlEl.get(xmlAttributeName)  # find first
    if value is None:
        return

    if transform is not None:
        value = transform(value)

    if attributeName is None:
        attributeName = common.hyphenToCamelCase(xmlAttributeName)
    setattr(m21El, attributeName, value)


def _setAttributeFromTagText(m21El, xmlEl, tag, attributeName=None, *, transform=None):
    '''
    If xmlEl has a at least one element of tag==tag with some text. If
    it does, set the attribute either with the same name (with "foo-bar" changed to
    "fooBar") or with attributeName to the text contents.

    Pass a function or lambda function as `transform` to transform the value before setting it

    >>> from xml.etree.ElementTree import Element, SubElement

    This is essentially `<accidental><alter>-2</alter></accidental>`:

    >>> e = Element('accidental')
    >>> a = SubElement(e, 'alter')
    >>> a.text = '-2'

    >>> seta = musicxml.xmlToM21._setAttributeFromTagText
    >>> acc = pitch.Accidental()

    Transform the alter text to a float.

    >>> seta(acc, e, 'alter', transform=float)
    >>> acc.alter
    -2.0

    >>> e2 = Element('score-partwise')
    >>> a2 = SubElement(e2, 'movement-title')
    >>> a2.text = 'Trout'
    >>> md = metadata.Metadata()
    >>> seta(md, e2, 'movement-title', 'movementName')
    >>> md.movementName
    'Trout'

    set a different attribute

    >>> seta(md, e2, 'movement-title', 'composer')
    >>> md.composer
    'Trout'
    '''
    matchEl = xmlEl.find(tag)  # find first
    if matchEl is None:
        return

    value = matchEl.text
    if value in (None, ''):
        return

    if transform is not None:
        value = transform(value)

    if attributeName is None:
        attributeName = common.hyphenToCamelCase(tag)

    setattr(m21El, attributeName, value)


def _synchronizeIds(element, m21Object):
    '''
    MusicXML 3.1 defines the id attribute
    (%optional-unique-id)
    on many elements which is perfect for setting as .id on
    a music21 element.

    <fermata id="hello"><id>bye</id></fermata>

    >>> from xml.etree.ElementTree import fromstring as El
    >>> e = El('<fermata id="fermata1"/>')
    >>> f = expressions.Fermata()
    >>> musicxml.xmlToM21._synchronizeIds(e, f)
    >>> f.id
    'fermata1'

    Does not change the id if the id is not specified:

    >>> e = El('<fermata />')
    >>> f = expressions.Fermata()
    >>> f.id = 'doNotOverwrite'
    >>> musicxml.xmlToM21._synchronizeIds(e, f)
    >>> f.id
    'doNotOverwrite'
    '''
    newId = element.get('id', None)
    if not newId:
        return
    m21Object.id = newId


# ------------------------------------------------------------------------------
class XMLParserBase:
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

    # style attributes

    def setStyleAttributes(self, mxObject, m21Object, musicXMLNames, m21Names=None):
        # noinspection PyShadowingNames
        '''
        Takes an mxObject, a music21Object, and a list/tuple of musicXML names and
        a list/tuple of m21Names, and assigns each of the mxObject's attributes
        that fits this style name to the corresponding style object's m21Name attribute.

        >>> from xml.etree.ElementTree import fromstring as El
        >>> XP = musicxml.xmlToM21.XMLParserBase()
        >>> mxObj = El('<a x="20.1" y="10.0" z="yes" />')
        >>> m21Obj = base.Music21Object()
        >>> musicXMLNames = ('w', 'x', 'y', 'z')
        >>> m21Names = ('justify', 'absoluteX', 'absoluteY', 'hideObjectOnPrint')

        >>> XP.setStyleAttributes(mxObj, m21Obj, musicXMLNames, m21Names)

        `.justify` requires a TextStyle object.

        >>> m21Obj.style.justify
        Traceback (most recent call last):
        AttributeError: 'Style' object has no attribute 'justify'

        >>> m21Obj.style.absoluteX
        20.1
        >>> m21Obj.style.absoluteY
        10
        >>> m21Obj.style.hideObjectOnPrint
        True
        '''
        if isinstance(m21Object, style.Style):
            stObj = m21Object
        else:
            stObj = None

        if not common.isIterable(musicXMLNames):
            musicXMLNames = [musicXMLNames]

        if m21Names is None:
            m21Names = [common.hyphenToCamelCase(x) for x in musicXMLNames]
        elif not common.isIterable(m21Names):
            m21Names = [m21Names]

        for xmlName, m21Name in zip(musicXMLNames, m21Names):
            mxValue = mxObject.get(xmlName)
            if mxValue is None:
                continue

            if m21Name in xmlObjects.STYLE_ATTRIBUTES_STR_NONE_TO_NONE and mxValue == 'none':
                mxValue = None
            if m21Name in xmlObjects.STYLE_ATTRIBUTES_YES_NO_TO_BOOL:
                mxValue = xmlObjects.yesNoToBoolean(mxValue)

            try:
                if mxValue is not True and mxValue is not False:
                    mxValue = common.numToIntOrFloat(mxValue)
            except (ValueError, TypeError):
                pass

            # only create a style object if we get this far...
            if stObj is None:
                stObj = m21Object.style
            setattr(stObj, m21Name, mxValue)

    def setTextFormatting(self, mxObject, m21Object):
        '''
        sets the justification, print-style-align group, and
        text-decoration, text-rotation,
        letter-spacing, line-height, lang, text-direction, and
        enclosure, on an
        m21Object, which must have style.TextStyle as its Style class,
        and then calls setPrintStyleAlign

        conforms to attr-group %text-formatting in the MusicXML DTD
        '''
        musicXMLNames = ('justify', 'text-decoration', 'text-rotation', 'letter-spacing',
                         'line-height', 'lang', 'text-direction', 'enclosure')
        m21Names = ('justify', 'textDecoration', 'textRotation', 'letterSpacing',
                    'lineHeight', 'language', 'textDirection', 'enclosure')
        self.setStyleAttributes(mxObject, m21Object, musicXMLNames, m21Names)
        self.setPrintStyleAlign(mxObject, m21Object)

    def setLineStyle(self, mxObject, m21Object):
        '''
        Sets four additional elements for line elements, conforms to entity
        %line-shape, %line-type, %dashed-formatting (dash-length and space-length)
        '''
        musicXMLNames = ('line-shape', 'line-type', 'dash-length', 'space-length')

        if hasattr(m21Object, 'lineType'):
            mxLineType = mxObject.get('line-type')
            if mxLineType is not None:
                m21Object.lineType = mxLineType

        self.setStyleAttributes(mxObject, m21Object, musicXMLNames)

    def setPrintObject(self, mxObject, m21Object):
        '''
        convert 'print-object="no"' to m21Object.style.hideObjectOnPrint = True
        '''
        if mxObject.get('print-object') != 'no':
            return

        if hasattr(m21Object, 'style'):
            m21Object.style.hideObjectOnPrint = True
        else:
            try:
                m21Object.hideObjectOnPrint = True
            except AttributeError:  # slotted object
                pass

    def setPrintStyleAlign(self, mxObject, m21Object):
        '''
        runs setPrintStyle and then sets horizontalAlign and verticalAlign, on an
        m21Object, which must have style.TextStyle as its Style class.

        conforms to attr-group %print-style-align in the MusicXML DTD
        '''
        self.setPrintStyle(mxObject, m21Object)
        self.setStyleAttributes(mxObject,
                                m21Object,
                                ('valign', 'halign'),
                                ('alignVertical', 'alignHorizontal'))

    def setPrintStyle(self, mxObject, m21Object):
        '''
        get position, font, and color information from the mxObject
        into the m21Object, which must have style.TextStyle as its Style class.

        conforms to attr-group %print-style in the MusicXML DTD
        '''
        self.setPosition(mxObject, m21Object)
        self.setFont(mxObject, m21Object)
        self.setColor(mxObject, m21Object)

    def setColor(self, mxObject, m21Object):
        '''
        Sets m21Object.style.color to be the same as color...
        '''
        self.setStyleAttributes(mxObject, m21Object, 'color')

    def setFont(self, mxObject, m21Object):
        '''
        sets font-family, font-style, font-size, and font-weight as
        fontFamily (list), fontStyle, fontSize and fontWeight from
        an object into a TextStyle object

        conforms to attr-group %font in the MusicXML DTD

        >>> from xml.etree.ElementTree import fromstring as El
        >>> XP = musicxml.xmlToM21.XMLParserBase()
        >>> mxObj = El('<text font-family="Courier,monospaced" font-style="italic" '
        ...            + 'font-size="24" font-weight="bold" />')

        >>> te = expressions.TextExpression('hi!')
        >>> XP.setFont(mxObj, te)
        >>> te.style.fontFamily
        ['Courier', 'monospaced']
        >>> te.style.fontStyle
        'italic'
        >>> te.style.fontSize
        24
        >>> te.style.fontWeight
        'bold'
        '''
        musicXMLNames = ('font-family', 'font-style', 'font-size', 'font-weight')
        m21Names = ('fontFamily', 'fontStyle', 'fontSize', 'fontWeight')
        self.setStyleAttributes(mxObject, m21Object, musicXMLNames, m21Names)

    def setPosition(self, mxObject, m21Object):
        '''
        get positioning information for an object from
        default-x, default-y, relative-x, relative-y into
        the .style attribute's absoluteX, relativeX, etc. attributes'

        conforms to attr-group %position in the MusicXML DTD
        '''
        musicXMLNames = ('default-x', 'default-y', 'relative-x', 'relative-y')
        m21Names = ('absoluteX', 'absoluteY', 'relativeX', 'relativeY')
        self.setStyleAttributes(mxObject, m21Object, musicXMLNames, m21Names)

    def setPlacement(self, mxObject, m21Object):
        '''
        Sets the placement for objects that have a .placement attribute
        (most but not all spanners) and sets the style.placement for those
        that don't.
        '''
        placement = mxObject.get('placement')
        if placement is None:
            return

        if hasattr(m21Object, 'placement'):
            m21Object.placement = placement
        else:
            m21Object.style.placement = placement

    def setEditorial(self, mxObj, m21Obj):
        # noinspection PyShadowingNames
        '''
        Set editorial information from an mxObj

        >>> from xml.etree.ElementTree import fromstring as El
        >>> XP = musicxml.xmlToM21.XMLParserBase()
        >>> mxObj = El('<a/>')
        >>> n = note.Note('C#4')

        Most common case:

        >>> XP.setEditorial(mxObj, n)
        >>> n.hasEditorialInformation
        False

        >>> mxObj = El('<note><footnote>Sharp is conjectural</footnote>'
        ...            + '<level reference="yes">2</level></note>')
        >>> XP.setEditorial(mxObj, n)
        >>> n.hasEditorialInformation
        True
        >>> len(n.editorial.footnotes)
        1
        >>> fn = n.editorial.footnotes[0]
        >>> fn
        <music21.editorial.Comment 'Sharp is conjectu...'>
        >>> fn.isFootnote
        True
        >>> fn.levelInformation
        '2'
        >>> fn.isReference
        True

        If no <footnote> tag exists, the editorial information will be found in
        comments:

        >>> mxObj = El('<note><level reference="no">ed</level></note>')
        >>> n = note.Note('C#4')
        >>> XP.setEditorial(mxObj, n)
        >>> len(n.editorial.footnotes)
        0
        >>> len(n.editorial.comments)
        1
        >>> com = n.editorial.comments[0]
        >>> com.isReference
        False
        >>> com.text is None
        True
        >>> com.levelInformation
        'ed'
        '''
        mxFootnote = mxObj.find('footnote')
        mxLevel = mxObj.find('level')

        if mxFootnote is None and mxLevel is None:
            # most common case
            return

        c = editorial.Comment()

        if mxFootnote is not None:
            c.text = mxFootnote.text
            c.isFootnote = True
            self.setTextFormatting(mxFootnote, c)

        if mxLevel is not None:
            c.levelInformation = mxLevel.text
            referenceAttribute = mxLevel.get('reference')
            if referenceAttribute == 'yes':
                c.isReference = True
            # TODO: attr: level-display: bracket, parentheses...

        if c.isFootnote:
            m21Obj.editorial.footnotes.append(c)
        else:
            m21Obj.editorial.comments.append(c)

    def xmlPrintToPageLayout(self, mxPrint, inputM21=None):
        # noinspection PyShadowingNames
        '''
        Given an mxPrint object, set object data for
        the print section of a layout.PageLayout object


        >>> from xml.etree.ElementTree import fromstring as El
        >>> MP = musicxml.xmlToM21.MeasureParser()


        >>> mxPrint = El('<print new-page="yes" page-number="5">'
        ...    + '    <page-layout><page-height>4000</page-height>'
        ...    + '        <page-margins><left-margin>20</left-margin>'
        ...    + '                 <right-margin>30.25</right-margin></page-margins>'
        ...    + '</page-layout></print>')

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

        # TODO -- record even, odd, both margins
        mxPageMargins = mxPageLayout.find('page-margins')
        if mxPageMargins is not None:
            for direction in ('top', 'bottom', 'left', 'right'):
                seta(pageLayout, mxPageMargins, direction + '-margin',
                     transform=_floatOrIntStr)

        if inputM21 is None:
            return pageLayout

    def xmlPrintToSystemLayout(self, mxPrint, inputM21=None):
        # noinspection PyShadowingNames
        '''
        Given an mxPrint object, set object data

        >>> from xml.etree.ElementTree import fromstring as El
        >>> MP = musicxml.xmlToM21.MeasureParser()

        >>> mxPrint = El('<print new-system="yes">'
        ...    + '    <system-layout><system-distance>55</system-distance>'
        ...    + '        <system-margins><left-margin>20</left-margin>'
        ...    + '                 <right-margin>30.25</right-margin></system-margins>'
        ...    + '</system-layout></print>')
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

        # mxSystemLayout = mxPrint.get('systemLayout')
        mxSystemLayout = mxPrint.find('system-layout')  # blank

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

        # TODO -- record even, odd, both margins
        mxSystemMargins = mxSystemLayout.find('system-margins')
        if mxSystemMargins is not None:
            for direction in ('top', 'bottom', 'left', 'right'):
                seta(systemLayout, mxSystemMargins, direction + '-margin',
                     transform=_floatOrIntStr)

        seta(systemLayout, mxSystemLayout, 'system-distance', 'distance',
             transform=_floatOrIntStr)
        seta(systemLayout, mxSystemLayout, 'top-system-distance', 'topDistance',
             transform=_floatOrIntStr)

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
        seta(staffLayout, mxStaffLayout,
             'staff-distance', 'distance', transform=_floatOrIntStr)
        # ET.dump(mxStaffLayout)

        staffNumber = mxStaffLayout.get('number')
        if staffNumber is not None:
            staffNumber = int(staffNumber)
            staffLayout.staffNumber = staffNumber

        if hasattr(self, 'staffLayoutObjects') and hasattr(self, 'offsetMeasureNote'):
            staffLayoutKey = ((staffNumber or 1), self.offsetMeasureNote)
            self.staffLayoutObjects[staffLayoutKey] = staffLayout

        if inputM21 is None:
            return staffLayout


class PartGroup:
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
        '''
        Add a partGroupId to self.partGroupIds
        '''
        self.partGroupIds.append(partGroupId)


# ------------------------------------------------------------------------------

class MusicXMLImporter(XMLParserBase):
    '''
    Object for importing .xml, .mxl, .musicxml, MusicXML files into music21.
    '''

    def __init__(self):
        super().__init__()
        self.xmlText = None
        self.xmlFilename = None
        self.xmlRoot = None
        self.stream = stream.Score()

        self.definesExplicitSystemBreaks = False
        self.definesExplicitPageBreaks = False

        self.spannerBundle = self.stream.spannerBundle
        self.mxScorePartDict = {}
        self.m21PartObjectsById = {}
        self.partGroupList = []
        self.parts = []

        self.musicXmlVersion = '3.0'

    def scoreFromFile(self, filename):
        '''
        main program: opens a file given by filename and returns a complete
        music21 Score from it.
        '''
        # load filename into text
        self.readFile(filename)
        # self.parseXMLText()
        return self.stream

    def readFile(self, filename):
        etree = ET.parse(filename)
        self.xmlRoot = etree.getroot()
        if self.xmlRoot.tag != 'score-partwise':
            raise MusicXMLImportException('Cannot parse MusicXML files not in score-partwise. '
                                          + f"Root tag was '{self.xmlRoot.tag}'")
        self.xmlRootToScore(self.xmlRoot, self.stream)

    def parseXMLText(self):
        # pylint: disable=undefined-variable
        if isinstance(self.xmlText, bytes):
            self.xmlText = self.xmlText.decode('utf-8')
        sio = io.StringIO(self.xmlText)
        try:
            etree = ET.parse(sio)
            self.xmlRoot = etree.getroot()
        except ET.ParseError:
            self.xmlRoot = ET.XML(self.xmlText)
            # might still raise an ET.ParseError

        if self.xmlRoot.tag != 'score-partwise':
            raise MusicXMLImportException('Cannot parse MusicXML files not in score-partwise. '
                                          + f"Root tag was '{self.xmlRoot.tag}'")
        self.xmlRootToScore(self.xmlRoot, self.stream)

    def xmlRootToScore(self, mxScore, inputM21=None):
        '''
        parse an xml file into a Score() object.
        '''
        if inputM21 is None:
            s = stream.Score()
        else:
            s = inputM21

        mxVersion = mxScore.get('version')
        if mxVersion is not None:
            self.musicXmlVersion = mxVersion

        md = self.xmlMetadata(mxScore)
        s.coreInsert(0, md)

        mxDefaults = mxScore.find('defaults')
        if mxDefaults is not None:
            scoreLayout = self.xmlDefaultsToScoreLayout(mxDefaults)
            s.coreInsert(0, scoreLayout)

        for mxCredit in mxScore.findall('credit'):
            credit = self.xmlCreditToTextBox(mxCredit)
            s.coreInsert(0, credit)

        self.parsePartList(mxScore)
        for p in mxScore.findall('part'):
            partId = p.get('id')
            if partId is None:  # pragma: no cover
                partId = list(self.mxScorePartDict.keys())[0]
                # Lilypond Test Suite allows for parsing w/o a part ID for one part...
            try:
                mxScorePart = self.mxScorePartDict[partId]
            except KeyError:  # pragma: no cover
                environLocal.printDebug(f'Cannot find info for part with name {partId}'
                                        + ', skipping the part')
                continue

            part = self.xmlPartToPart(p, mxScorePart)

            if part is not None:  # for instance, in partStreams
                s.coreInsert(0.0, part)
                self.m21PartObjectsById[partId] = part

        self.partGroups()

        # copy spanners that are complete into the Score.
        # basically just the StaffGroups for now.
        rm = []
        for sp in self.spannerBundle.getByCompleteStatus(True):
            self.stream.coreInsert(0, sp)
            rm.append(sp)
        # remove from original spanner bundle
        for sp in rm:
            self.spannerBundle.remove(sp)

        s.coreElementsChanged()
        s.definesExplicitSystemBreaks = self.definesExplicitSystemBreaks
        s.definesExplicitPageBreaks = self.definesExplicitPageBreaks
        for p in s.parts:
            p.definesExplicitSystemBreaks = self.definesExplicitSystemBreaks
            p.definesExplicitPageBreaks = self.definesExplicitPageBreaks

        s.sort()  # do this now so that if the file is cached, we can cache that it's sorted.
        if inputM21 is None:
            return s

    def xmlPartToPart(self, mxPart, mxScorePart):
        '''
        Given a <part> object and the <score-part> object, parse a complete part.
        '''
        parser = PartParser(mxPart, mxScorePart=mxScorePart, parent=self)
        parser.parse()
        if parser.appendToScoreAfterParse is True:
            return parser.stream
        else:
            return None

    def parsePartList(self, mxScore):
        '''
        Parses the <part-list> tag and adds
        <score-part> entries into self.mxScorePartDict[partId]
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
                self.mxScorePartDict[partId] = partListElement
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
        # noinspection PyShadowingNames
        '''Convert a MusicXML credit to a music21 TextBox

        >>> import xml.etree.ElementTree as ET
        >>> credit = ET.fromstring(
        ...               '<credit page="2"><credit-words>Testing</credit-words></credit>')

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
        <music21.text.TextBox ''>
        '''
        tb = text.TextBox()
        # center and middle these are good defaults for new textboxes
        # but not for musicxml import
        tb.style.alignHorizontal = None
        tb.style.alignVertical = None

        pageNum = mxCredit.get('page')
        if pageNum is None:
            pageNum = 1
        else:
            pageNum = int(pageNum)
        tb.page = pageNum
        content = []
        for cw in mxCredit.findall('credit-words'):
            if cw.text not in (None, ''):
                content.append(cw.text)
        if not content:  # no text defined
            tb.content = ''
            return tb  # capella generates empty credit-words
            # raise MusicXMLImportException('no credit words defined for a credit tag')
        tb.content = '\n'.join(content)  # join with \n

        cw1 = mxCredit.find('credit-words')
        # take formatting from the first, no matter if multiple are defined
        self.setPrintStyleAlign(cw1, tb)
        tb.style.justify = cw1.get('justify')
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
            seta(scoreLayout, mxScaling, 'millimeters', 'scalingMillimeters',
                 transform=_floatOrIntStr)
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

        self.styleFromXmlDefaults(mxDefaults)

        return scoreLayout

    def styleFromXmlDefaults(self, mxDefaults):
        # noinspection PyShadowingNames
        '''
        Set the appearance and font information from mxDefault
        <appearance>, <music-font>, <word-font>, <lyric-font> (multiple),
        and <lyric-language> tags.

        Here the demo does not include the <appearance> tag since that is
        documented in `xmlAppearanceToStyle`

        >>> import xml.etree.ElementTree as ET
        >>> defaults = ET.fromstring('<defaults>'
        ...          + '<music-font font-family="Maestro, Opus" font-weight="bold" />'
        ...          + '<word-font font-family="Garamond" font-style="italic" />'
        ...          + '<lyric-font name="verse" font-size="12" />'
        ...          + '<lyric-font name="chorus" font-size="14" />'
        ...          + '<lyric-language name="verse" xml:lang="fr" />'
        ...          + '<lyric-language name="chorus" xml:lang="en" />'
        ...          + '</defaults>')

        >>> MI = musicxml.xmlToM21.MusicXMLImporter()
        >>> MI.styleFromXmlDefaults(defaults)
        >>> st = MI.stream.style
        >>> st.musicFont
        <music21.style.TextStyle object at 0x10535c0f0>
        >>> st.musicFont.fontFamily
        ['Maestro', 'Opus']
        >>> st.musicFont.fontWeight
        'bold'
        >>> st.wordFont.fontFamily
        ['Garamond']
        >>> st.wordFont.fontStyle
        'italic'
        >>> len(st.lyricFonts)
        2
        >>> st.lyricFonts[0]
        ('verse', <music21.style.TextStyle object at 0x10535d438>)
        >>> st.lyricFonts[0][1].fontSize
        12
        >>> st.lyricLanguages
        [('verse', 'fr'), ('chorus', 'en')]
        '''
        mxAppearance = mxDefaults.find('appearance')
        if mxAppearance is not None:
            self.xmlAppearanceToStyle(mxAppearance)

        mxMusicFont = mxDefaults.find('music-font')
        if mxMusicFont is not None:
            st = style.TextStyle()
            self.setFont(mxMusicFont, st)
            self.stream.style.musicFont = st

        mxWordFont = mxDefaults.find('word-font')
        if mxWordFont is not None:
            st = style.TextStyle()
            self.setFont(mxWordFont, st)
            self.stream.style.wordFont = st

        for mxLyricFont in mxDefaults.findall('lyric-font'):
            st = style.TextStyle()
            self.setFont(mxLyricFont, st)
            lyricName = mxLyricFont.get('name')
            styleTuple = (lyricName, st)
            self.stream.style.lyricFonts.append(styleTuple)

        for mxLyricLanguage in mxDefaults.findall('lyric-language'):
            lyricLanguage = 'en'
            lyricName = mxLyricLanguage.get('name')
            for aKey, value in mxLyricLanguage.attrib.items():
                # {http://www.w3.org/XML/1998/namespace}lang
                if aKey.endswith('}lang'):
                    lyricLanguage = value
                    break
            lyricTuple = lyricName, lyricLanguage
            self.stream.style.lyricLanguages.append(lyricTuple)

    def xmlAppearanceToStyle(self, mxAppearance):
        # noinspection PyShadowingNames
        '''
        Parse the appearance tag for information about line widths and note sizes

        >>> import xml.etree.ElementTree as ET
        >>> appear = ET.fromstring('<appearance>'
        ...          + '<line-width type="beam">5</line-width>'
        ...          + '<line-width type="ledger">1.5625</line-width>'
        ...          + '<note-size type="grace">60</note-size>'
        ...          + '<distance type="hyphen">0.5</distance>'
        ...          + '<other-appearance type="sharps">dotted</other-appearance>'
        ...          + '</appearance>')

        >>> MI = musicxml.xmlToM21.MusicXMLImporter()
        >>> MI.xmlAppearanceToStyle(appear)
        >>> st = MI.stream.style

        >>> st.lineWidths
        [('beam', 5), ('ledger', 1.5625)]

        >>> st.noteSizes
        [('grace', 60)]

        >>> st.distances
        [('hyphen', 0.5)]

        >>> st.otherAppearances
        [('sharps', 'dotted')]
        '''
        for mxLineWidth in mxAppearance.findall('line-width'):
            lineWidthType = mxLineWidth.get('type')  # required
            lineWidthValue = common.numToIntOrFloat(mxLineWidth.text)
            lineWidthInfo = (lineWidthType, lineWidthValue)
            self.stream.style.lineWidths.append(lineWidthInfo)

        for mxNoteSize in mxAppearance.findall('note-size'):
            noteSizeType = mxNoteSize.get('type')  # required
            noteSizeValue = common.numToIntOrFloat(mxNoteSize.text)
            noteSizeInfo = (noteSizeType, noteSizeValue)
            self.stream.style.noteSizes.append(noteSizeInfo)

        for mxDistance in mxAppearance.findall('distance'):
            distanceType = mxDistance.get('type')  # required
            distanceValue = common.numToIntOrFloat(mxDistance.text)
            distanceInfo = (distanceType, distanceValue)
            self.stream.style.distances.append(distanceInfo)

        for mxOther in mxAppearance.findall('other-appearance'):
            otherType = mxOther.get('type')  # required
            otherValue = mxOther.text  # value can be anything
            otherInfo = (otherType, otherValue)
            self.stream.style.otherAppearances.append(otherInfo)

    def partGroups(self):
        '''
        set StaffGroup objects from the <part-group> tags.
        '''
        seta = _setAttributeFromTagText
        for pgObj in self.partGroupList:
            staffGroup = layout.StaffGroup()
            for partId in pgObj.partGroupIds:
                # get music21 part from mxScorePartDictionary
                try:
                    staffGroup.addSpannedElements(self.m21PartObjectsById[partId])
                except KeyError as ke:
                    foundOne = False
                    for partIdTest in sorted(self.m21PartObjectsById):
                        if partIdTest.startswith(partId + '-Staff'):
                            staffGroup.addSpannedElements(self.m21PartObjectsById[partIdTest])
                            foundOne = True

                    if foundOne is False:
                        raise MusicXMLImportException(
                            'Cannot find part in m21PartObjectsById dictionary by Id:'
                            + f' {ke} \n   Full Dict:\n   {self.m21PartObjectsById!r} ')
            mxPartGroup = pgObj.mxPartGroup
            seta(staffGroup, mxPartGroup, 'group-name', 'name')
            # TODO: group-name-display
            seta(staffGroup, mxPartGroup, 'group-abbreviation', 'abbreviation')
            # TODO: group-abbreviation-display
            mxGroupSymbol = mxPartGroup.find('group-symbol')
            if mxGroupSymbol is not None:
                seta(staffGroup, mxPartGroup, 'group-symbol', 'symbol')
                self.setPosition(mxGroupSymbol, staffGroup)
                self.setColor(mxGroupSymbol, staffGroup)
            else:
                staffGroup.symbol = 'brace'  # MusicXML default

            seta(staffGroup, mxPartGroup, 'group-barline', 'barTogether')

            # TODO: group-time
            self.setEditorial(mxPartGroup, staffGroup)
            staffGroup.completeStatus = True
            self.spannerBundle.append(staffGroup)
            # self.stream.coreInsert(0, staffGroup)

    def xmlMetadata(self, el=None, inputM21=None):
        '''
        Converts part of the root element into a metadata object

        Supported: work-title, work-number, opus, movement-number,
        movement-title, identification
        '''
        if el is None:
            el = self.root

        if inputM21 is None:
            md = metadata.Metadata()
        else:
            md = inputM21

        seta = _setAttributeFromTagText
        # work
        work = el.find('work')
        if work is not None:
            seta(md, work, 'work-title', 'title')
            seta(md, work, 'work-number', 'number')
            seta(md, work, 'opus', 'opusNumber')

        seta(md, el, 'movement-number')
        seta(md, el, 'movement-title', 'movementName')

        identification = el.find('identification')
        if identification is not None:
            self.identificationToMetadata(identification, md)

        if inputM21 is None:
            return md

    def identificationToMetadata(self, identification, inputM21=None):
        '''
        Converter an <identification> tag, containing <creator> tags, <rights> tags, and
        <miscellaneous> tag.

        Not supported: source, relation

        Only the first <rights> tag is supported

        Encoding only parses "supports" and that only has
        new-system (definesExplicitSystemBreaks) and
        new-page (definesExplicitPageBreaks)
        '''
        if inputM21 is not None:
            md = inputM21
        else:
            md = metadata.Metadata()

        for creator in identification.findall('creator'):
            c = self.creatorToContributor(creator)
            md.addContributor(c)

        for rights in identification.findall('rights'):
            c = self.rightsToCopyright(rights)
            md.copyright = c
            break

        encoding = identification.find('encoding')
        if encoding is not None:
            # TODO: encoder (text + type = role) multiple
            # TODO: encoding date multiple
            # TODO: encoding-description (string) multiple
            for software in encoding.findall('software'):
                if textStripValid(software):
                    md.software.append(software.text.strip())

            for supports in encoding.findall('supports'):
                # todo: element: required
                # todo: type: required -- not sure of the difference between this and value
                #         though type is yes-no while value is string
                attr = supports.get('attribute')
                value = supports.get('value')
                if value is None:
                    value = supports.get('type')

                # found in wild: element=accidental type="no" -- No accidentals are indicated
                # found in wild: transpose
                # found in wild: beam
                # found in wild: stem
                if (attr, value) == ('new-system', 'yes'):
                    self.definesExplicitSystemBreaks = True
                elif (attr, value) == ('new-page', 'yes'):
                    self.definesExplicitPageBreaks = True

        # TODO: source
        # TODO: relation
        miscellaneous = identification.find('miscellaneous')
        if miscellaneous is not None:
            for mxMiscField in miscellaneous.findall('miscellaneous-field'):
                miscFieldName = mxMiscField.get('name')
                if miscFieldName is None:
                    continue  # it is required, so technically can raise an exception
                miscFieldValue = mxMiscField.text
                if miscFieldValue is None:
                    continue  # it is required, so technically can raise an exception
                try:
                    setattr(md, miscFieldName, miscFieldValue)
                except Exception as e:  # pylint: disable=broad-except
                    environLocal.warn('Could not set metadata: {} to {}: {}'.format(
                        miscFieldName, miscFieldValue, e
                    ))

        if inputM21 is None:
            return md

    def creatorToContributor(self, creator, inputM21=None):
        # noinspection PyShadowingNames
        '''
        Given an <creator> tag, fill the necessary parameters of a Contributor.

        >>> import xml.etree.ElementTree as ET
        >>> creator = ET.fromstring('<creator type="composer">Beethoven, Ludwig van</creator>')

        >>> MI = musicxml.xmlToM21.MusicXMLImporter()
        >>> c = MI.creatorToContributor(creator)
        >>> c
        <music21.metadata.primitives.Contributor composer:Beethoven, Ludwig van>
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
        if (creatorType is not None
                and creatorType in metadata.Contributor.roleNames):
            c.role = creatorType

        creatorText = creator.text
        if creatorText is not None:
            c.name = creatorText.strip()
        if inputM21 is None:
            return c

    def rightsToCopyright(self, rights):
        # noinspection PyShadowingNames
        '''
        Given an <rights> tag, fill the necessary parameters of a
        :class:`~music21.metadata.primitives.Copyright` object.

        >>> import xml.etree.ElementTree as ET
        >>> rights = ET.fromstring('<rights type="owner">CC-SA-BY</rights>')

        >>> MI = musicxml.xmlToM21.MusicXMLImporter()
        >>> c = MI.rightsToCopyright(rights)
        >>> c
        <music21.metadata.primitives.Copyright CC-SA-BY>
        >>> c.role
        'owner'
        >>> str(c)
        'CC-SA-BY'
        '''
        rt = rights.text
        if rt is not None:
            rt = rt.strip()

        c = metadata.Copyright(rt)

        copyrightType = rights.get('type')
        if copyrightType is not None:
            c.role = copyrightType

        return c


# -----------------------------------------------------------------------------
class PartParser(XMLParserBase):
    '''
    parser to work with a single <part> tag.

    called out for multiprocessing potential in future
    '''

    def __init__(self, mxPart=None, mxScorePart=None, parent=None):
        super().__init__()
        self.mxPart = mxPart
        self.mxScorePart = mxScorePart

        if mxPart is not None:
            self.partId = mxPart.get('id')
            if self.partId is None and parent is not None:
                self.partId = list(parent.mxScorePartDict.keys())[0]
        else:
            self.partId = ''
        self._parent = common.wrapWeakref(parent)
        if parent is not None:
            self.spannerBundle = parent.spannerBundle
        else:
            self.spannerBundle = spanner.SpannerBundle()

        self.stream: stream.Part = stream.Part()
        if self.mxPart is not None:
            for mxStaves in self.mxPart.findall('measure/attributes/staves'):
                if int(mxStaves.text) > 1:
                    self.stream = stream.PartStaff()  # PartStaff inherits from Part, so okay.
                    break

        self.atSoundingPitch = True

        self.staffReferenceList: List[StaffReferenceType] = []

        self.lastTimeSignature = None
        self.lastMeasureWasShort = False
        self.lastMeasureOffset = 0.0

        # a dict of clefs per staff number
        self.lastClefs: Dict[int, Optional[clef.Clef]] = {NO_STAFF_ASSIGNED: clef.TrebleClef()}
        self.activeTuplets: List[Optional[duration.Tuplet]] = [None] * 7

        self.maxStaves = 1  # will be changed in measure parsing...

        self.lastMeasureNumber = 0
        self.lastNumberSuffix = None

        self.multiMeasureRestsToCapture = 0
        self.activeMultiMeasureRestSpanner = None

        self.activeInstrument = None
        self.firstMeasureParsed = False  # has the first measure been parsed yet?
        self.activeAttributes = None  # divisions, clef, etc.
        self.lastDivisions = defaults.divisionsPerQuarter  # give a default value for testing

        self.appendToScoreAfterParse = True
        self.lastMeasureParser = None

    @property
    def parent(self):
        return common.unwrapWeakref(self._parent)

    def parse(self):
        '''
        Run the parser on a single part
        '''
        self.parseXmlScorePart()
        self.parseMeasures()
        self.stream.atSoundingPitch = self.atSoundingPitch

        # TODO: this does not work with voices; there, Spanners
        # will be copied into the Score

        # copy spanners that are complete into the part, as this is the
        # highest level container that needs them
        rm = []
        for sp in self.spannerBundle.getByCompleteStatus(True):
            self.stream.coreInsert(0, sp)
            rm.append(sp)
        # remove from original spanner bundle
        for sp in rm:
            self.spannerBundle.remove(sp)
        # s is the score; adding the part to the score
        self.stream.coreElementsChanged()

        if self.maxStaves > 1:
            self.separateOutPartStaves()
        else:
            self.stream.addGroupForElements(self.partId)  # set group for components
            self.stream.groups.append(self.partId)  # set group for stream itself

    def parseXmlScorePart(self):
        '''
        The <score-part> tag contains a lot of information about the
        Part itself.  It was found in the <part-list> in the ScoreParser but
        was not parsed and instead passed into the PartParser as .mxScorePart.

        Sets the stream.partName, stream.partAbbreviation, self.activeInstrument,
        and inserts an instrument at the beginning of the stream.

        The instrumentObj being configured comes from self.getDefaultInstrument.
        '''
        part = self.stream
        mxScorePart = self.mxScorePart

        seta = _setAttributeFromTagText
        # put part info into the Part object and retrieve it later...
        seta(part, mxScorePart, 'part-name', transform=_clean)
        mxPartName = mxScorePart.find('part-name')
        if mxPartName is not None:
            printObject = mxPartName.get('print-object')
            if printObject == 'no':
                part.style.printPartName = False

        # This will later be put in the default instrument object also also...

        # TODO: partNameDisplay
        seta(part, mxScorePart, 'part-abbreviation', transform=_clean)
        mxPartAbbrev = mxScorePart.find('part-abbreviation')
        if mxPartAbbrev is not None:
            printObject = mxPartAbbrev.get('print-object')
            if printObject == 'no':
                part.style.printPartAbbreviation = False
        # This will later be put in instrument.partAbbreviation also...

        # TODO: partAbbreviationDisplay

        instrumentObj = self.getDefaultInstrument()
        # self.firstInstrumentObject = instrumentObj  # not used.
        if instrumentObj.bestName() is not None:
            part.id = instrumentObj.bestName()
        self.activeInstrument = instrumentObj

        part.partName = instrumentObj.partName
        part.partAbbreviation = instrumentObj.partAbbreviation
        part.coreInsert(0.0, instrumentObj)  # add instrument at zero offset

    def getDefaultInstrument(self, mxScorePart=None):
        # noinspection PyShadowingNames
        r'''
        >>> scorePart = ('<score-part id="P4"><part-name>Bass</part-name>'
        ...     + '<part-abbreviation>B.</part-abbreviation>'
        ...     + '<score-instrument id="P4-I4">'
        ...     + '    <instrument-name>Instrument 4</instrument-name>'
        ...     + '</score-instrument>'
        ...     + '<midi-instrument id="P4-I4">'
        ...     + '   <midi-channel>4</midi-channel>'
        ...     + '<midi-program>1</midi-program>'
        ...     + '</midi-instrument>'
        ...     + '</score-part>')
        >>> from xml.etree.ElementTree import fromstring as EL
        >>> PP = musicxml.xmlToM21.PartParser()

        >>> mxScorePart = EL(scorePart)
        >>> i = PP.getDefaultInstrument(mxScorePart)
        >>> i.instrumentName
        'Instrument 4'
        '''
        if mxScorePart is None:
            mxScorePart = self.mxScorePart

        def _adjustMidiData(mc):
            return int(mc) - 1

        seta = _setAttributeFromTagText

        # print(ET.tostring(mxScorePart, encoding='unicode'))
        i = instrument.Instrument()
        i.partId = self.partId
        i.groups.append(self.partId)
        i.partName = self.stream.partName
        i.partAbbreviation = self.stream.partAbbreviation
        # TODO: groups

        # for now, just get first instrument
        # TODO: get all instruments!
        mxScoreInstrument = mxScorePart.find('score-instrument')
        if mxScoreInstrument is not None:
            seta(i, mxScoreInstrument, 'instrument-name', transform=_clean)
            seta(i, mxScoreInstrument, 'instrument-abbreviation', transform=_clean)
            seta(i, mxScoreInstrument, 'instrument-sound')
        # TODO: solo / ensemble
        # TODO: virtual-instrument
        # TODO: store id attribute somewhere

        # for now, just get first midi instrument
        # TODO: get all
        # TODO: midi-device
        mxMIDIInstrument = mxScorePart.find('midi-instrument')
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

    def parseMeasures(self):
        '''
        Parse each <measure> tag using self.xmlMeasureToMeasure
        '''
        part = self.stream
        for mxMeasure in self.mxPart.iterfind('measure'):
            self.xmlMeasureToMeasure(mxMeasure)

        # self.removeEndForwardRest()
        part.coreElementsChanged()

    #     def removeEndForwardRest(self):
    #         '''
    #         If the last measure ended with a forward tag, as happens
    #         in some pieces that end with incomplete measures,
    #         remove the rest there (for backwards compatibility, esp.
    #         since bwv66.6 uses it)
    #         '''
    #         if self.lastMeasureParser is None:
    #             return
    #         lmp = self.lastMeasureParser
    #         self.lastMeasureParser = None  # clean memory
    #
    #         if lmp.endedWithForwardTag is None:
    #             return
    #         endedForwardRest = lmp.endedWithForwardTag
    #         if lmp.stream.recurse().notesAndRests[-1] is endedForwardRest:
    #             lmp.stream.remove(endedForwardRest, recurse=True)

    def separateOutPartStaves(self):
        '''
        Take a `Part` with multiple staves and make them a set of `PartStaff` objects.
        '''
        # Elements in these classes appear only on the staff to which they are assigned.
        # All other classes appear on every staff, except for spanners, which remain on the first.
        STAFF_SPECIFIC_CLASSES = [
            'Clef',
            'Dynamic',
            'Expression',
            'GeneralNote',
            'StaffLayout',
        ]

        def separateOneStaff(streamPartStaff: stream.PartStaff, staffNumber: int):
            partStaffId = f'{self.partId}-Staff{staffNumber}'
            streamPartStaff.id = partStaffId

            # remove all elements that are not part of this staff
            mStream = list(streamPartStaff.getElementsByClass('Measure'))
            for i, staffReference in enumerate(self.staffReferenceList):
                staffExclude = self._getStaffExclude(staffReference, staffNumber)
                if not staffExclude:
                    continue

                m = mStream[i]
                for eRemove in staffExclude:
                    m.remove(eRemove, recurse=True)
                # after adjusting voices see if voices can be reduced or
                # removed
                # environLocal.printDebug(['calling flattenUnnecessaryVoices: voices before:',
                #     len(m.voices)])
                m.flattenUnnecessaryVoices(force=False, inPlace=True)
                # environLocal.printDebug(['calling flattenUnnecessaryVoices: voices after:',
                #    len(m.voices)])

            streamPartStaff.addGroupForElements(partStaffId)
            streamPartStaff.groups.append(partStaffId)
            self.parent.stream.insert(0, streamPartStaff)
            self.parent.m21PartObjectsById[partStaffId] = streamPartStaff

        uniqueStaffKeys = self._getUniqueStaffKeys()
        templates = []
        for unused_key in uniqueStaffKeys[1:]:
            # Add Spanner to the list of removeClasses; leave them in first staff only
            template = self.stream.template(
                removeClasses=STAFF_SPECIFIC_CLASSES + ['Spanner'], fillWithRests=False)
            templates.append(template)

            # Populate elements from source into copy (template)
            for sourceMeasure, copyMeasure in zip(
                self.stream.getElementsByClass('Measure'),
                template.getElementsByClass('Measure')
            ):
                for elem in sourceMeasure.getElementsByClass(STAFF_SPECIFIC_CLASSES):
                    copyMeasure.insert(elem.offset, elem)
                for sourceVoice, copyVoice in zip(sourceMeasure.voices, copyMeasure.voices):
                    for elem in sourceVoice.getElementsByClass(STAFF_SPECIFIC_CLASSES):
                        copyVoice.insert(elem.offset, elem)

        modelAndCopies = [self.stream] + templates
        for staff, outerStaffNumber in zip(modelAndCopies, uniqueStaffKeys):
            separateOneStaff(staff, outerStaffNumber)

        staffGroup = layout.StaffGroup(modelAndCopies, name=self.stream.partName, symbol='brace')
        staffGroup.style.hideObjectOnPrint = True  # in truth, hide the name, not the brace
        self.parent.stream.insert(0, staffGroup)

        self.appendToScoreAfterParse = False

    def _getStaffExclude(
        self,
        staffReference: StaffReferenceType,
        targetKey: int
    ) -> List[base.Music21Object]:
        '''
        Given a staff reference dictionary, remove and combine in a list all elements that
        are NOT part of the given key. Thus, return a list of all entries to remove.
        It keeps those elements under staff key None (common to all) and
        those under given key. This then is the list of all elements that should be deleted.

        If targetKey is NO_STAFF_ASSIGNED (0) then returns an empty list
        '''
        if targetKey == NO_STAFF_ASSIGNED:
            return []

        post = []
        for k in staffReference:
            if k == NO_STAFF_ASSIGNED:
                continue
            elif k == targetKey:
                continue
            post += staffReference[k]
        return post

    def _getUniqueStaffKeys(self) -> List[int]:
        '''
        Given a list of staffReference dictionaries,
        collect and return a list of all unique keys except NO_STAFF_ASSIGNED (0)
        '''
        post = []
        for staffReference in self.staffReferenceList:
            for k in staffReference:
                if k != NO_STAFF_ASSIGNED and k not in post:
                    post.append(k)
        post.sort()
        return post

    def xmlMeasureToMeasure(self, mxMeasure):
        # noinspection PyShadowingNames
        '''
        Convert a measure element to a Measure, using
        :class:`~music21.musicxml.xmlToM21.MeasureParser`

        >>> from xml.etree.ElementTree import fromstring as EL

        Testing full measure rest parsing:

        Here is a measure with a rest that lasts 4 beats but we will put it in a 3/4 context.

        >>> scoreMeasure = '<measure><note><rest/><duration>40320</duration></note></measure>'
        >>> mxMeasure = EL(scoreMeasure)
        >>> pp = musicxml.xmlToM21.PartParser()
        >>> pp.lastDivisions
        10080
        >>> 40320 / 10080
        4.0
        >>> pp.lastTimeSignature = meter.TimeSignature('3/4')
        >>> m = pp.xmlMeasureToMeasure(mxMeasure)

        Test that the rest lasts three, not four beats:

        >>> measureRest = m.notesAndRests[0]
        >>> measureRest
        <music21.note.Rest rest>
        >>> measureRest.duration.type
        'half'
        >>> measureRest.duration.quarterLength
        3.0
        '''
        measureParser = MeasureParser(mxMeasure, parent=self)
        try:
            measureParser.parse()
        except MusicXMLImportException as e:
            e.measureNumber = measureParser.measureNumber
            e.partName = self.stream.partName
            raise e
        self.lastMeasureParser = measureParser

        if measureParser.staves > self.maxStaves:
            self.maxStaves = measureParser.staves

        if measureParser.transposition is not None:
            self.updateTransposition(measureParser.transposition)

        self.firstMeasureParsed = True
        self.staffReferenceList.append(measureParser.staffReference)

        m = measureParser.stream
        self.setLastMeasureInfo(m)
        # TODO: move this into the measure parsing,
        #     because it should happen on a voice level.
        if measureParser.fullMeasureRest is True:
            # recurse is necessary because it could be in voices...
            r1 = m.recurse().getElementsByClass('Rest')[0]
            lastTSQl = self.lastTimeSignature.barDuration.quarterLength
            if (r1.fullMeasure is True  # set by xml measure='yes'
                                    or (r1.duration.quarterLength != lastTSQl
                                        and r1.duration.type in ('whole', 'breve')
                                        and r1.duration.dots == 0
                                        and not r1.duration.tuplets)):
                r1.duration.quarterLength = lastTSQl
                r1.fullMeasure = True

        self.stream.coreInsert(self.lastMeasureOffset, m)
        self.adjustTimeAttributesFromMeasure(m)

        return m

    def updateTransposition(self, newTransposition):
        '''
        As you might expect, a measureParser that reveals a change
        in transposition is going to have an effect on the
        Part's instrument list.  This (totally undocumented) method
        deals with it.

        If measureParser.transposition is None, does nothing.
        If measureParser.transposition is not None, but

        NOTE: Need to test a change of instrument w/o a change of
        transposition such as: Bb clarinet to Bb Soprano Sax to Eb clarinet?
        '''
        # STEP 1: determine whether this  new transposition
        # requires creating a new instrument.

        if self.activeInstrument is not None:
            if (self.activeInstrument.transposition is None
                    and self.firstMeasureParsed is False):
                # We already created an instrument (activeInstrument) from the
                # PartInfo. We haven't done anything with it yet, so
                # no need for a change of instrument
                pass
                # environLocal.warn('Put trans on active instrument')
            else:
                # We have an activeInstrument, so this change of transposition
                # requires us to create a new one (think of physical instruments
                # such as Bb clarinet to A clarinet.
                newInst = copy.deepcopy(self.activeInstrument)
                # environLocal.warn('Put trans on new instrument')
                self.activeInstrument = newInst
                self.stream.coreInsert(self.lastMeasureOffset, newInst)
        else:
            # There is no activeInstrument and we're not at the beginning
            # of the piece... this shouldn't happen, but let's send a warning
            # and create a Generic Instrument object rather than dying.
            environLocal.warn('Received a transposition tag, but instrument to put it on!')
            fakeInst = instrument.Instrument()
            self.activeInstrument = fakeInst
            self.stream.coreInsert(self.lastMeasureOffset, fakeInst)

        # STEP 2:
        # Actually change the transposition of the instrument
        # and note that the score is definitely NOT all at sounding pitch
        self.activeInstrument.transposition = newTransposition
        self.atSoundingPitch = False

    def setLastMeasureInfo(self, m):
        # noinspection PyShadowingNames
        '''
        Sets self.lastMeasureNumber and self.lastMeasureSuffix from the measure,
        which is used in fixing Finale unnumbered measure issues.

        Also sets self.lastTimeSignature from the timeSignature found in
        the measure, if any.

        >>> PP = musicxml.xmlToM21.PartParser()

        Here are the defaults:

        >>> PP.lastMeasureNumber
        0
        >>> PP.lastNumberSuffix is None
        True
        >>> PP.lastTimeSignature is None
        True

        After setLastMeasureInfo:

        >>> m = stream.Measure(number=4)
        >>> m.numberSuffix = 'b'
        >>> ts38 = meter.TimeSignature('3/8')
        >>> m.timeSignature = ts38
        >>> PP.setLastMeasureInfo(m)

        >>> PP.lastMeasureNumber
        4
        >>> PP.lastNumberSuffix
        'b'
        >>> PP.lastTimeSignature
        <music21.meter.TimeSignature 3/8>
        >>> PP.lastTimeSignature is ts38
        True

        Note that if there was no timeSignature defined in m,
        and no lastTimeSignature exists,
        the PartParser gets a default of 4/4, because
        after the first measure there's going to be routines
        that need some sort of time signature:

        >>> PP2 = musicxml.xmlToM21.PartParser()
        >>> m2 = stream.Measure(number=2)
        >>> PP2.setLastMeasureInfo(m2)
        >>> PP2.lastTimeSignature
        <music21.meter.TimeSignature 4/4>


        For obscure reasons relating to how Finale gives suffixes
        to unnumbered measures, if a measure has the same number
        as lastMeasureNumber, the lastNumberSuffix is not updated:

        >>> PP3 = musicxml.xmlToM21.PartParser()
        >>> PP3.lastMeasureNumber = 10
        >>> PP3.lastNumberSuffix = 'X1'

        >>> m10 = stream.Measure(number=10)
        >>> m10.numberSuffix = 'X2'
        >>> PP3.setLastMeasureInfo(m10)
        >>> PP3.lastNumberSuffix
        'X1'
        '''
        if m.number == self.lastMeasureNumber:
            pass
            # we do this check so that we do not compound suffixes, i.e.:
            # 23, 23.X1, 23.X1X2, 23.X1X2X3
            # and instead just do:
            # 23, 23.X1, 23.X2, etc.
        else:
            self.lastMeasureNumber = m.number
            self.lastNumberSuffix = m.numberSuffix

        if m.timeSignature is not None:
            self.lastTimeSignature = m.timeSignature
        elif self.lastTimeSignature is None:
            # if no time signature is defined, need to get a default
            ts = meter.TimeSignature('4/4')
            self.lastTimeSignature = ts

    def adjustTimeAttributesFromMeasure(self, m):
        '''
        Adds padAsAnacrusis to pickup measures and other measures that
        do not fill the whole tile, if the first measure of the piece, or
        immediately follows an incomplete measure (such as a repeat sign mid-measure
        in a piece where each phrase begins with a pickup and ends with an
        incomplete measure).

        Fills an empty measure with a measure of rest (bug in PDFtoMusic and
        other MusicXML writers).

        sets self.lastMeasureWasShort to True or False if it is an incomplete measure
        that is not a pickup.
        '''
        # note: we cannot assume that the time signature properly
        # describes the offsets w/n this bar. need to look at
        # offsets within measure; if the .highestTime value is greater
        # use this as the next offset

        mHighestTime = m.highestTime
        # environLocal.warn([self.lastTimeSignature])
        # environLocal.warn([self.lastTimeSignature.barDuration])

        lastTimeSignatureQuarterLength = self.lastTimeSignature.barDuration.quarterLength

        if mHighestTime >= lastTimeSignatureQuarterLength:
            mOffsetShift = mHighestTime

        elif mHighestTime == 0.0 and not m.recurse().notesAndRests:
            # this routine fixes a bug in PDFtoMusic and other MusicXML writers
            # that omit empty rests in a Measure.  It is a very quick test if
            # the measure has any notes.  Slower if it does not.
            r = note.Rest()
            r.duration.quarterLength = lastTimeSignatureQuarterLength
            m.insert(0.0, r)
            mOffsetShift = lastTimeSignatureQuarterLength

        else:  # use time signature
            # for the first measure, this may be a pickup
            # must detect this when writing, as next measures offsets will be
            # incorrect
            if self.lastMeasureOffset == 0.0:
                # cannot get bar duration proportion if cannot get a ts
                if m.barDurationProportion() < 1.0:
                    m.padAsAnacrusis()
                    # environLocal.printDebug(['incompletely filled Measure found on musicxml
                    #    import; interpreting as a anacrusis:', 'paddingLeft:', m.paddingLeft])
                mOffsetShift = mHighestTime

            else:
                mOffsetShift = mHighestTime  # lastTimeSignatureQuarterLength
                if self.lastMeasureWasShort is True:
                    if m.barDurationProportion() < 1.0:
                        m.padAsAnacrusis()  # probably a pickup after a repeat or phrase boundary
                        # or something
                        self.lastMeasureWasShort = False
                else:
                    if mHighestTime < lastTimeSignatureQuarterLength:
                        self.lastMeasureWasShort = True
                    else:
                        self.lastMeasureWasShort = False

        self.lastMeasureOffset += mOffsetShift

    def applyMultiMeasureRest(self, r):
        '''
        If there is an active MultiMeasureRestSpanner, add the Rest, r, to it:

        >>> PP = musicxml.xmlToM21.PartParser()
        >>> mmrSpanner = spanner.MultiMeasureRest()
        >>> mmrSpanner
        <music21.spanner.MultiMeasureRest 0 measures>

        >>> PP.activeMultiMeasureRestSpanner = mmrSpanner
        >>> PP.multiMeasureRestsToCapture = 2
        >>> r1 = note.Rest(type='whole', id='r1')
        >>> PP.applyMultiMeasureRest(r1)
        >>> PP.multiMeasureRestsToCapture
        1
        >>> PP.activeMultiMeasureRestSpanner
        <music21.spanner.MultiMeasureRest 1 measure>

        >>> PP.activeMultiMeasureRestSpanner is mmrSpanner
        True
        >>> PP.stream.show('text')  # Nothing...

        >>> r2 = note.Rest(type='whole', id='r2')
        >>> PP.applyMultiMeasureRest(r2)
        >>> PP.multiMeasureRestsToCapture
        0
        >>> PP.activeMultiMeasureRestSpanner is None
        True

        # spanner added to stream

        >>> PP.stream.show('text')
        {0.0} <music21.spanner.MultiMeasureRest 2 measures>

        >>> r3 = note.Rest(type='whole', id='r3')
        >>> PP.applyMultiMeasureRest(r3)
        >>> PP.stream.show('text')
        {0.0} <music21.spanner.MultiMeasureRest 2 measures>

        '''
        if self.activeMultiMeasureRestSpanner is None:
            return
        self.activeMultiMeasureRestSpanner.addSpannedElements(r)
        self.multiMeasureRestsToCapture -= 1
        if self.multiMeasureRestsToCapture == 0:
            self.stream.insert(0, self.activeMultiMeasureRestSpanner)
            self.activeMultiMeasureRestSpanner = None


# -----------------------------------------------------------------------------
class MeasureParser(XMLParserBase):
    '''
    parser to work with a single <measure> tag.

    called out for simplicity.

    >>> from xml.etree.ElementTree import fromstring as EL

    >>> scoreMeasure = '<measure><note><rest/><duration>40320</duration></note></measure>'
    >>> mxMeasure = EL(scoreMeasure)
    >>> mp = musicxml.xmlToM21.MeasureParser(mxMeasure)
    >>> mp.parse()
    >>> mp.restAndNoteCount['rest']
    1
    >>> mp.restAndNoteCount['note']
    0

    >>> mp.fullMeasureRest
    True
    '''
    attributeTagsToMethods = {
        'time': 'handleTimeSignature',
        'clef': 'handleClef',
        'key': 'handleKeySignature',
        'staff-details': 'handleStaffDetails',
        'measure-style': 'handleMeasureStyle',
    }
    musicDataMethods = {
        'note': 'xmlToNote',
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
        # Note: <print> is handled separately...
    }

    # TODO: editorial, i.e., footnote and level
    # staves: see separateOutPartStaves()
    # TODO: part-symbol
    # not to be done: directive DEPRECATED since MusicXML 2.0
    def __init__(self, mxMeasure=None, parent=None):
        super().__init__()

        self.mxMeasure = mxMeasure
        self.mxMeasureElements = []

        self.parent = parent  # PartParser

        self.transposition = None
        if parent is not None:
            self.spannerBundle = parent.spannerBundle
        else:
            self.spannerBundle = spanner.SpannerBundle()

        self.staffReference: StaffReferenceType = {}
        if parent is not None:
            # list of current tuplets or Nones
            self.activeTuplets: List[Optional[duration.Tuplet]] = parent.activeTuplets
        else:
            self.activeTuplets: List[Optional[duration.Tuplet]] = [None] * 7

        self.useVoices = False
        self.voicesById = {}
        self.voiceIndices = set()
        self.staves = 1

        self.activeAttributes = None
        self.attributesAreInternal = True

        self.measureNumber = None
        self.numberSuffix = None

        if parent is not None:
            self.divisions = parent.lastDivisions
        else:
            self.divisions = defaults.divisionsPerQuarter

        # key is a tuple of the
        #     staff number (or None) and offsetMeasureNote, and the value is a
        #     StaffLayout object.
        self.staffLayoutObjects: Dict[Tuple[Optional[int], float], layout.StaffLayout] = {}
        self.stream = stream.Measure()

        self.mxNoteList = []  # for accumulating notes in chords
        self.mxLyricList = []  # for accumulating lyrics assigned to chords
        self.nLast = None  # for adding notes to spanners.

        # Sibelius 7.1 only puts a <voice> tag on the
        # first note of a chord, so we need to make sure
        # that we keep track of the last voice...
        self.chordVoice = None
        self.fullMeasureRest = False

        # for keeping track of full-measureRests.
        self.restAndNoteCount = {'rest': 0, 'note': 0}
        if parent is not None:
            # share dict
            self.lastClefs: Dict[int, Optional[clef.Clef]] = self.parent.lastClefs

        else:
            # a dict of clefs for staffIndexes:
            self.lastClefs: Dict[int, Optional[clef.Clef]] = {NO_STAFF_ASSIGNED: None}
        self.parseIndex = 0

        # what is the offset in the measure of the current note position?
        self.offsetMeasureNote = 0.0

        # # keep track of the last rest that was added with a forward tag.
        # # there are many pieces that end with incomplete measures that
        # # older versions of Finale put a forward tag at the end, but this
        # # disguises the incomplete last measure.  The PartParser will
        # # pick this up from the last measure.
        # self.endedWithForwardTag = None

    @staticmethod
    def getStaffNumber(mxObjectOrNumber) -> int:
        '''
        gets a int representing a staff number, or 0 (representing no staff assigned)
        from an mxObject or a number...

        >>> mp = musicxml.xmlToM21.MeasureParser()
        >>> from xml.etree.ElementTree import fromstring as EL

        >>> gsn = mp.getStaffNumber
        >>> gsn(1)
        1
        >>> gsn('2')
        2

        <note> tags store their staff numbers in a <staff> tag's text...

        >>> gsn(EL('<note><staff>2</staff></note>'))
        2

        ...or not at all.

        >>> el = EL('<note><pitch><step>C</step><octave>4</octave></pitch></note>')
        >>> gsn(el) == musicxml.xmlToM21.NO_STAFF_ASSIGNED
        True

        Clefs, however, store theirs in a `number` attribute.

        >>> gsn(EL('<clef number="2"/>'))
        2
        >>> gsn(None) == musicxml.xmlToM21.NO_STAFF_ASSIGNED
        True
        '''
        if isinstance(mxObjectOrNumber, int):
            return mxObjectOrNumber
        elif isinstance(mxObjectOrNumber, str):
            return int(mxObjectOrNumber)
        elif mxObjectOrNumber is None:
            return NO_STAFF_ASSIGNED
        mxObject = mxObjectOrNumber

        # find objects that use a "staff" element
        # harmony, forward, note, direction
        if mxObject.tag in ('harmony', 'forward', 'note', 'direction'):
            try:
                staffObject = mxObject.find('staff')
                if staffObject is not None:
                    try:
                        k = staffObject.text.strip()
                        return int(k)
                    except TypeError:
                        return NO_STAFF_ASSIGNED
                    except AttributeError:
                        pass
            except AttributeError:
                pass
            return NO_STAFF_ASSIGNED
        elif mxObject.tag in ('staff-layout',
                              'staff-details',
                              'measure-style',
                              'clef',
                              'key',
                              'time',
                              'transpose'):
            # these objects store staff assignment simply as an attribute called number.
            try:
                k = mxObject.get('number')
                # this must be a positive integer as string
                return int(k)
            except TypeError:
                pass
            except AttributeError:  # a normal number
                pass
            return NO_STAFF_ASSIGNED
        else:
            return NO_STAFF_ASSIGNED
            # TODO: handle part-symbol (attributes: top-staff, bottom-staff)
            # separately

    def addToStaffReference(self, mxObjectOrNumber, m21Object):
        '''
        Utility routine for importing musicXML objects;
        here, we store a reference to the music21 object in a dictionary,
        where keys are the staff values. Staff values may be None, 1, 2, etc.

        >>> MP = musicxml.xmlToM21.MeasureParser()
        >>> MP.addToStaffReference(1, note.Note('C5'))
        >>> MP.addToStaffReference(2, note.Note('D3'))
        >>> MP.addToStaffReference(2, note.Note('E3'))
        >>> len(MP.staffReference)
        2
        >>> list(sorted(MP.staffReference.keys()))
        [1, 2]
        >>> MP.staffReference[1]
        [<music21.note.Note C>]
        >>> MP.staffReference[2]
        [<music21.note.Note D>, <music21.note.Note E>]

        >>> from xml.etree.ElementTree import fromstring as EL
        >>> mxNote = EL('<note><staff>1</staff></note>')
        >>> MP.addToStaffReference(mxNote, note.Note('F5'))
        >>> MP.staffReference[1]
        [<music21.note.Note C>, <music21.note.Note F>]

        No staff reference.

        >>> mxNote = EL('<note />')
        >>> MP.addToStaffReference(mxNote, note.Note('G4'))
        >>> len(MP.staffReference)
        3
        >>> MP.staffReference[0]
        [<music21.note.Note G>]
        '''
        staffReference = self.staffReference
        staffKey = self.getStaffNumber(mxObjectOrNumber)  # an int, including 0 = NO_STAFF_ASSIGNED
        if staffKey not in staffReference:
            staffReference[staffKey] = []
        staffReference[staffKey].append(m21Object)

    def insertCoreAndRef(self, offset, mxObjectOrNumber, m21Object):
        '''
        runs addToStaffReference and then insertCore.

        >>> from xml.etree.ElementTree import fromstring as EL
        >>> mxNote = EL('<note><staff>1</staff></note>')

        >>> MP = musicxml.xmlToM21.MeasureParser()
        >>> MP.insertCoreAndRef(1.0, mxNote, note.Note('F5'))

        This routine leaves MP.stream in an unusable state, because
        it runs insertCore.  Thus before querying the stream we need to run at end:

        >>> MP.stream.coreElementsChanged()
        >>> MP.stream.show('text')
        {1.0} <music21.note.Note F>
        '''
        self.addToStaffReference(mxObjectOrNumber, m21Object)
        self.stream.coreInsert(offset, m21Object)

    def parse(self):
        # handle <print> before anything else, because it can affect
        # attributes!
        for mxPrint in self.mxMeasure.findall('print'):
            self.xmlPrint(mxPrint)

        # these are the attributes of the <measure> tag, not the <attributes> tag
        self.parseMeasureAttributes()
        self.updateVoiceInformation()
        self.mxMeasureElements = list(self.mxMeasure)  # for grabbing next note
        for i, mxObj in enumerate(self.mxMeasureElements):
            self.parseIndex = i  # for grabbing next note
            if mxObj.tag in self.musicDataMethods:
                methName = self.musicDataMethods[mxObj.tag]
                if methName is not None:
                    meth = getattr(self, methName)
                    meth(mxObj)

        if self.useVoices is True:
            for v in self.stream.iter.voices:
                if v:  # do not bother with empty voices
                    # the musicDataMethods use insertCore, thus the voices need to run
                    # coreElementsChanged
                    v.coreElementsChanged()
                    # Fill mid-measure gaps, and find end of measure gaps by ref to measure stream
                    # https://github.com/cuthbertlab/music21/issues/444
                    v.makeRests(refStreamOrTimeRange=self.stream,
                                fillGaps=True,
                                inPlace=True,
                                hideRests=True)
        self.stream.coreElementsChanged()

        if (self.restAndNoteCount['rest'] == 1
                and self.restAndNoteCount['note'] == 0):
            # TODO: do this on a per voice basis.
            self.fullMeasureRest = True
            # it might already be True because a rest had a "measure='yes'" attribute

    def xmlBackup(self, mxObj):
        '''
        parse a backup tag by changing .offsetMeasureNote
        '''
        try:
            change = float(mxObj.find('duration').text.strip()) / self.divisions
            self.offsetMeasureNote -= change
        except AttributeError:
            pass

    def xmlForward(self, mxObj):
        '''
        parse a forward tag by changing .offsetMeasureNote
        '''
        change = float(mxObj.find('duration').text.strip()) / self.divisions
        self.offsetMeasureNote += change

    def xmlPrint(self, mxPrint):
        '''
        <print> handles changes in pages, numbering, layout,
        etc. so can generate PageLayout, SystemLayout, or StaffLayout
        objects.

        Should also be able to set measure attributes on self.stream
        '''
        def hasPageLayout():
            if mxPrint.get('new-page') not in (None, 'no'):
                return True
            if mxPrint.get('page-number') is not None:
                return True
            if mxPrint.find('page-layout') is not None:
                return True
            return False

        def hasSystemLayout():
            if mxPrint.get('new-system') not in (None, 'no'):
                return True
            if mxPrint.find('system-layout') is not None:
                return True
            return False

        addPageLayout = hasPageLayout()
        addSystemLayout = hasSystemLayout()
        addStaffLayout = not (mxPrint.find('staff-layout') is None)

        # --- now we know what we need to add, add em
        m = self.stream
        if addPageLayout is True:
            pl = self.xmlPrintToPageLayout(mxPrint)
            m.insert(0.0, pl)  # should this be parserOffset?
        if addSystemLayout is True or addPageLayout is False:
            sl = self.xmlPrintToSystemLayout(mxPrint)
            m.insert(0.0, sl)
        if addStaffLayout is True:
            # assumes addStaffLayout is there...
            slFunc = self.xmlStaffLayoutToStaffLayout
            stlList = [slFunc(mx) for mx in mxPrint.iterfind('staff-layout')]
            # If bugs incorporate Ariza additional checks, but
            # I think that we don't want to add to an existing staffLayoutObject
            # so that staff distance can change.
            for stl in stlList:
                if stl is None or stl.staffNumber is None:
                    continue  # sibelius likes to give empty staff layouts!
                self.insertCoreAndRef(0.0, str(stl.staffNumber), stl)
            self.stream.coreElementsChanged()
        # TODO: measure-layout -- affect self.stream
        mxMeasureNumbering = mxPrint.find('measure-numbering')
        if mxMeasureNumbering is not None:
            m.style.measureNumbering = mxMeasureNumbering.text
            st = style.TextStyle()
            self.setPrintStyleAlign(mxMeasureNumbering, st)
            m.style.measureNumberingStyle = st
        # TODO: measure-numbering
        # TODO: part-name-display
        # TODO: part-abbreviation display
        # TODO: print-attributes: staff-spacing, blank-page; skip deprecated staff-spacing

    def xmlToNote(self, mxNote):
        '''
        Handles everything for creating a Note or Rest or Chord

        Does not actually return the note, but sets self.nLast to the note.

        This routine uses coreInserts for speed, so it can leave either
        `self.stream` or a `Voice` object within `self.stream` in an unstable state.
        '''
        try:
            mxObjNext = self.mxMeasureElements[self.parseIndex + 1]
            if mxObjNext.tag == 'note' and mxObjNext.find('chord') is not None:
                nextNoteIsChord = True
            else:
                nextNoteIsChord = False
        except IndexError:  # last note in measure
            nextNoteIsChord = False

        # TODO: Cue notes (no sounding tie)

        # the first note of a chord is not identified directly; only
        # by looking at the next note can we tell if we have the first
        # note of a chord
        isChord = False
        isRest = False
        # TODO: Unpitched

        offsetIncrement = 0.0

        if mxNote.find('rest') is not None:  # it is a Rest
            isRest = True
        if mxNote.find('chord') is not None:
            isChord = True

        # do not count extra pitches in chord as note.
        # it might be the first note of the chord...
        if nextNoteIsChord:
            isChord = True  # first note of chord is not identified.
            voiceOfChord = mxNote.find('voice')
            if voiceOfChord is not None:
                vIndex = voiceOfChord.text
                try:
                    vIndex = int(vIndex)
                except ValueError:
                    pass
                self.chordVoice = vIndex

        if isChord is True:  # and isRest is False...?
            n = None  # fo linting
            self.mxNoteList.append(mxNote)
            # store lyrics for latter processing
            for mxLyric in mxNote.findall('lyric'):
                self.mxLyricList.append(mxLyric)
        elif isChord is False and isRest is False:  # normal note...
            self.restAndNoteCount['note'] += 1
            n = self.xmlToSimpleNote(mxNote)
        else:  # it's a rest
            self.restAndNoteCount['rest'] += 1
            n = self.xmlToRest(mxNote)

        if isChord is False:  # normal note or rest...
            self.updateLyricsFromList(n, mxNote.findall('lyric'))
            self.addToStaffReference(mxNote, n)
            self.insertInMeasureOrVoice(mxNote, n)
            offsetIncrement = n.duration.quarterLength
            self.nLast = n  # update

        # if we we have notes in the note list and the next
        # note either does not exist or is not a chord, we
        # have a complete chord
        if self.mxNoteList and nextNoteIsChord is False:
            c = self.xmlToChord(self.mxNoteList)
            # add any accumulated lyrics
            self.updateLyricsFromList(c, self.mxLyricList)
            self.addToStaffReference(self.mxNoteList[0], c)
            for thisMxNote in self.mxNoteList:
                # voice might be in a previous note; in fact, often in first <note>
                if thisMxNote.find('voice') is not None:
                    self.insertInMeasureOrVoice(thisMxNote, c)
                    break
            else:
                self.insertInMeasureOrVoice(mxNote, c)

            self.mxNoteList = []  # clear for next chord
            self.mxLyricList = []

            offsetIncrement = c.quarterLength
            self.nLast = c  # update

        # only increment Chords after completion
        self.offsetMeasureNote += offsetIncrement

    def xmlToChord(self, mxNoteList):
        # noinspection PyShadowingNames
        '''
        Given an a list of mxNotes, fill the necessary parameters

        >>> from xml.etree.ElementTree import fromstring as EL
        >>> MP = musicxml.xmlToM21.MeasureParser()
        >>> MP.divisions = 10080

        >>> qnDuration = r'<duration>7560</duration><type>quarter</type>'

        >>> a = EL(r'<note><pitch><step>A</step><octave>3</octave></pitch>'
        ...          + qnDuration + '</note>')
        >>> b = EL(r'<note><chord/><pitch><step>B</step><octave>3</octave></pitch>'
        ...          + qnDuration + '</note>')

        >>> c = MP.xmlToChord([a, b])
        >>> len(c.pitches)
        2
        >>> c.pitches[0]
        <music21.pitch.Pitch A3>
        >>> c.pitches[1]
        <music21.pitch.Pitch B3>

        >>> a = EL('<note><pitch><step>A</step><octave>3</octave></pitch>'
        ...        + qnDuration
        ...        + '<notehead>diamond</notehead></note>')
        >>> c = MP.xmlToChord([a, b])
        >>> c.getNotehead(c.pitches[0])
        'diamond'
        '''
        notes = []
        for mxNote in mxNoteList:
            notes.append(self.xmlToSimpleNote(mxNote, freeSpanners=False))
        c = chord.Chord(notes)

        # move beams from first note (TODO: confirm style moved already?)
        if notes:
            c.beams = notes[0].beams
            notes[0].beams = beam.Beams()

        # move spanners, expressions, articulations from first note to Chord.
        # See slur in m2 of schoenberg/op19 #2
        # but move only one of each class
        # Is there anything else that should be moved???

        seenArticulations = set()
        seenExpressions = set()

        for n in sorted(notes, key=lambda x: x.pitch.ps):
            ss = n.getSpannerSites()
            # transfer all spanners from the notes to the chord.
            for sp in ss:
                sp.replaceSpannedElement(n, c)
            for art in n.articulations:
                if type(art) in seenArticulations:  # pylint: disable=unidiomatic-typecheck
                    pass
                c.articulations.append(art)
                seenArticulations.add(type(art))
            for exp in n.expressions:
                if type(exp) in seenExpressions:  # pylint: disable=unidiomatic-typecheck
                    pass
                c.expressions.append(exp)
                seenExpressions.add(type(exp))

            n.articulations = []
            n.expressions = []

        self.spannerBundle.freePendingSpannedElementAssignment(c)
        return c

    def xmlToSimpleNote(self, mxNote, freeSpanners=True):
        # noinspection PyShadowingNames
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

        >>> mxNote = EL('<note pizzicato="yes"><pitch><step>D</step>'
        ...             + '<alter>-1</alter><octave>6</octave></pitch>'
        ...             + '<duration>7560</duration>'
        ...             + '<type>eighth</type><dot/></note>')

        >>> n = MP.xmlToSimpleNote(mxNote)
        >>> n
        <music21.note.Note D->
        >>> n.octave
        6
        >>> n.duration
        <music21.duration.Duration 0.75>
        >>> n.articulations
        [<music21.articulations.Pizzicato>]


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

        # TODO: beams over rests?
        '''
        n = note.Note()

        # send whole note since accidental display not in <pitch>
        self.xmlToPitch(mxNote, n.pitch)

        beamList = mxNote.findall('beam')
        if beamList:
            n.beams = self.xmlToBeams(beamList)

        mxStem = mxNote.find('stem')
        if mxStem is not None:
            try:
                n.stemDirection = mxStem.text.strip()
            except AttributeError:
                pass

            if mxStem.attrib:
                stemStyle = style.Style()
                self.setColor(mxStem, stemStyle)
                self.setPosition(mxStem, stemStyle)
                n.style.stemStyle = stemStyle

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
        # noinspection PyShadowingNames
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
        music21.musicxml.xmlObjects.MusicXMLImportException:
             unexpected beam type encountered (crazy)
        '''
        if inputM21 is None:
            beamOut = beam.Beam()
        else:
            beamOut = inputM21

        # TODO: get number to preserve
        # not to-do: repeater; is deprecated.
        self.setColor(mxBeam, beamOut)
        self.setStyleAttributes(mxBeam, beamOut, 'fan')

        try:
            mxType = mxBeam.text.strip()
        except AttributeError:
            mxType = 'begin'

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
            raise MusicXMLImportException(f'unexpected beam type encountered ({mxType})')

        if inputM21 is None:
            return beamOut

    def xmlToBeams(self, mxBeamList, inputM21=None):
        # noinspection PyShadowingNames
        '''
        given a list of mxBeam objects, sets the beamsList

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
        # noinspection PyShadowingNames
        '''
        Set notehead information from the mxNotehead object

        >>> from xml.etree.ElementTree import fromstring as EL
        >>> MP = musicxml.xmlToM21.MeasureParser()

        >>> n = note.Note()
        >>> nh = EL('<notehead color="#FF0000" filled="no" parentheses="yes">'
        ...         + 'diamond</notehead>')

        >>> MP.xmlNotehead(n, nh)
        >>> n.notehead
        'diamond'
        >>> n.noteheadFill
        False
        >>> n.noteheadParenthesis
        True
        >>> n.style.color
        '#FF0000'
        '''
        if mxNotehead.text not in ('', None):
            n.notehead = mxNotehead.text
        nhf = mxNotehead.get('filled')
        if nhf is not None:
            n.noteheadFill = xmlObjects.yesNoToBoolean(nhf)

        if mxNotehead.get('color') is not None:
            n.style.color = mxNotehead.get('color')
        # TODO font

        nhp = mxNotehead.get('parentheses')
        if nhp is not None:
            n.noteheadParenthesis = xmlObjects.yesNoToBoolean(nhp)

    def xmlToPitch(self, mxNote, inputM21=None):
        '''
        Given a MusicXML Note object, set this Pitch object to its values.

        >>> from xml.etree.ElementTree import fromstring as EL
        >>> MP = musicxml.xmlToM21.MeasureParser()

        >>> b = EL('<note><pitch><step>E</step><alter>-1</alter>'
        ...        + '<octave>3</octave></pitch></note>')
        >>> a = MP.xmlToPitch(b)
        >>> print(a)
        E-3

        Conflicting alter and accidental -- alter is still stored, but name is :

        >>> b = EL('<note><pitch><step>E</step><alter>-1</alter><octave>3</octave></pitch>'
        ...              + '<accidental>sharp</accidental></note>')
        >>> a = MP.xmlToPitch(b)
        >>> print(a)
        E#3
        >>> a.fullName
        'E-sharp in octave 3'

        >>> a.accidental.alter
        -1.0

        >>> a.accidental.name
        'sharp'

        >>> a.accidental.modifier
        '#'
        '''
        seta = _setAttributeFromTagText
        if inputM21 is None:
            p = pitch.Pitch()
        else:
            p = inputM21

        if mxNote.tag == 'pitch':
            mxPitch = mxNote
        else:
            mxPitch = mxNote.find('pitch')
            if mxPitch is None:  # whoops!!!!
                return p

        seta(p, mxPitch, 'step')
        seta(p, mxPitch, 'octave', transform=int)
        mxAlter = mxPitch.find('alter')
        accAlter = None
        if textStripValid(mxAlter):
            accAlter = float(mxAlter.text.strip())

        mxAccidental = mxNote.find('accidental')
        mxAccidentalName = None
        if textStripValid(mxAccidental):
            # MuseScore 0.9 made empty accidental tags for notes that did not
            # need an accidental display.
            mxAccidentalName = mxAccidental.text.strip()

        if mxAccidentalName is not None:
            try:
                accObj = self.xmlToAccidental(mxAccidental)
                p.accidental = accObj
                p.accidental.displayStatus = True

                if accAlter is not None and accAlter != accObj.alter:
                    accObj.setAttributeIndependently('alter', float(accAlter))

            except pitch.AccidentalException:
                # MuseScore 0.9.6 generates Accidentals with empty objects
                pass
        elif accAlter is not None:
            try:
                p.accidental = pitch.Accidental(accAlter)
            except pitch.AccidentalException:
                raise MusicXMLImportException(
                    f'incorrect accidental {accAlter} for pitch {p}')
            # TODO: check supports for accidentals!
            p.accidental.displayStatus = False

        return p

    def xmlToAccidental(self, mxAccidental, inputM21=None):
        '''
        >>> from xml.etree.ElementTree import fromstring as EL
        >>> MP = musicxml.xmlToM21.MeasureParser()

        >>> a = EL('<accidental>half-flat</accidental>')
        >>> b = pitch.Accidental()
        >>> MP.xmlToAccidental(a, b)
        >>> b.name
        'half-flat'
        >>> b.alter
        -0.5

        >>> a = EL('<accidental parentheses="yes">sharp</accidental>')
        >>> b = MP.xmlToAccidental(a)
        >>> b.displayStyle
        'parentheses'

        >>> a = EL('<accidental bracket="yes">sharp</accidental>')
        >>> b = MP.xmlToAccidental(a)
        >>> b.displayStyle
        'bracket'

        >>> a = EL('<accidental bracket="yes" parentheses="yes">sharp</accidental>')
        >>> b = MP.xmlToAccidental(a)
        >>> b.displayStyle
        'both'
        '''
        if inputM21 is None:
            acc = pitch.Accidental()
        else:
            acc = inputM21

        try:
            mxName = mxAccidental.text.strip().lower()
        except AttributeError:
            return acc

        if mxName in self.mxAccidentalNameToM21:
            name = self.mxAccidentalNameToM21[mxName]
        else:
            name = mxName

        # need to use set here to get all attributes up to date
        acc.set(name, allowNonStandardValue=True)
        self.setPrintStyle(mxAccidental, acc)

        # level display...
        parentheses = mxAccidental.get('parentheses')
        bracket = mxAccidental.get('bracket')
        if parentheses == 'yes' and bracket == 'yes':
            acc.displayStyle = 'both'
        elif parentheses == 'yes':
            acc.displayStyle = 'parentheses'
        elif bracket == 'yes':
            acc.displayStyle = 'bracket'
        # TODO: attr: size

        # TODO: attr: cautionary
        self.setEditorial(mxAccidental, acc)

        if inputM21 is None:
            return acc

    def xmlToRest(self, mxRest):
        # noinspection PyShadowingNames
        '''
        Takes a <note> tag that has been shown to have a <rest> tag in it
        and return a rest.

        >>> from xml.etree.ElementTree import fromstring as EL
        >>> MP = musicxml.xmlToM21.MeasureParser()

        >>> mxr = EL('<note><rest/><duration>5040</duration><type>eighth</type></note>')
        >>> r = MP.xmlToRest(mxr)
        >>> r
        <music21.note.Rest rest>
        >>> r.duration.quarterLength
        0.5

        >>> mxr = EL('<note><rest><display-step>G</display-step>' +
        ...              '<display-octave>4</display-octave>' +
        ...              '</rest><duration>5040</duration><type>eighth</type></note>')
        >>> r = MP.xmlToRest(mxr)
        >>> r
        <music21.note.Rest rest>

        A rest normally lies at B4 in treble clef, but here we have put it at
        G4, so we'll shift it down two steps.

        >>> r.stepShift
        -2

        Clef context matters, here we will set it for notes that don't specify a staff:

        >>> MP.lastClefs[musicxml.xmlToM21.NO_STAFF_ASSIGNED] = clef.BassClef()
        >>> r = MP.xmlToRest(mxr)

        Now this is a high rest:

        >>> r.stepShift
        10

        Test full measure rest.

        >>> mxr = EL('<note><rest measure="yes"/><duration>40320</duration></note>')
        >>> r = MP.xmlToRest(mxr)
        >>> MP.fullMeasureRest
        True

        Note that we do NOT set `r`'s `.fullMeasure` to True or always, but keep it as
        "auto" so that changes in time signature, etc. will affect output.
        '''
        r = note.Rest()
        mxRestTag = mxRest.find('rest')
        if mxRestTag is None:
            raise MusicXMLImportException('do not call xmlToRest on a <note> unless it '
                                          + 'contains a rest tag.')
        isFullMeasure = mxRestTag.get('measure')
        if isFullMeasure == 'yes':
            self.fullMeasureRest = True  # force full measure rest...
            r.measureRest = True
            # this attribute is not 100% necessary to get a multi-measure rest spanner

        if self.parent:  # will apply if active
            self.parent.applyMultiMeasureRest(r)

        ds = mxRestTag.find('display-step')
        if textStripValid(ds):
            ds_text = ds.text.strip()
            do = mxRestTag.find('display-octave')
            if textStripValid(do):
                ds_text += do.text.strip()

            tempP = pitch.Pitch(ds_text)
            # musicxml records rest display as a pitch in the current
            # clef.  Music21 records it as an offset (in steps) from the
            # middle line.  So we need clef context.
            restStaff = self.getStaffNumber(mxRest)
            try:
                cc = self.lastClefs[restStaff]
                if cc is None:
                    ccMidLine = 35  # assume TrebleClef
                else:
                    ccMidLine = cc.lowestLine + 4
            except KeyError:
                # assume treble clef
                ccMidLine = 35
            r.stepShift = tempP.diatonicNoteNum - ccMidLine

        return self.xmlNoteToGeneralNoteHelper(r, mxRest)

    def xmlNoteToGeneralNoteHelper(self, n, mxNote, freeSpanners=True):
        '''
        Combined function to work on all <note> tags, where n can be
        a Note or Rest
        '''
        spannerBundle = self.spannerBundle
        if freeSpanners is True:
            spannerBundle.freePendingSpannedElementAssignment(n)

        # attributes
        self.setPrintStyle(mxNote, n)
        # print object == 'no' and grace notes may have a type but not
        # a duration. they may be filtered out at the level of Stream
        # processing
        self.setPrintObject(mxNote, n)

        # attr dynamics -- MIDI Note On velocity with 90 = 100, but unbounded on the top
        dynamPercentage = mxNote.get('dynamics')
        if dynamPercentage is not None and not n.isRest:
            dynamFloat = float(dynamPercentage) * (90 / 12700)
            n.volume.velocityScalar = dynamFloat

        # TODO: attr end-dynamics -- MIDI Note Off velocity
        # TODO: attr attack -- alter starting time of the note
        # TODO: attr release -- alter the release time of the note
        # TODO: attr-group time-only
        if mxNote.get('pizzicato') == 'yes':
            n.articulations.append(articulations.Pizzicato())

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

        # type styles
        mxType = mxNote.find('type')
        if mxType is not None:
            self.setStyleAttributes(mxType, n, 'size', 'noteSize')

        self.setColor(mxNote, n)
        self.setPosition(mxNote, n)

        if mxNote.find('tie') is not None:
            n.tie = self.xmlToTie(mxNote)
            # provide all because of tied...
            # TODO: find tied if tie is not found... (cue notes)

        # translate if necessary, otherwise leaves unchanged
        if isGrace is True:
            n = self.xmlGraceToGrace(mxGrace, n)
        # this must be before notations, to get the slurs, etc.
        # attached to the grace notes...

        mxNotations = mxNote.findall('notations')
        for mxN in mxNotations:
            self.xmlNotations(mxN, n)

        self.setEditorial(mxNote, n)

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
        # TODO: instrument

    def xmlToDuration(self, mxNote, inputM21=None):
        # noinspection PyShadowingNames
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
        numDots = 0
        tuplets = ()

        if inputM21 is None:
            d = None
        else:
            d = inputM21

        divisions = self.divisions
        mxDuration = mxNote.find('duration')
        if mxDuration is not None:
            noteDivisions = float(mxDuration.text.strip())
            qLen = noteDivisions / divisions
        else:
            qLen = 0.0

        mxType = mxNote.find('type')
        if textStripValid(mxType):
            typeStr = mxType.text.strip()
            durationType = musicXMLTypeToType(typeStr)
            forceRaw = False

            # TODO: dot as print object with print-style and placement.
            numDots = len(mxNote.findall('dot'))
            # divide mxNote duration count by divisions to get qL
            # mxNotations = mxNote.get('notationsObj')
            mxTimeModification = mxNote.find('time-modification')

            if mxTimeModification is not None:
                tuplets = self.xmlToTuplets(mxNote)
                # get all necessary config from mxNote
            else:
                tuplets = ()

        else:  # some rests do not define type, and only define duration
            durationType = None  # no type to get, must use raw
            forceRaw = True
            # TODO: empty-placement

        # two ways to create durations, raw (from qLen) and cooked (from type, time-mod, dots)
        if forceRaw:
            if d is not None:
                # environLocal.printDebug(['forced to use raw duration', durRaw])
                durRaw = duration.Duration()  # raw just uses qLen
                # the qLen set here may not be computable, but is not immediately
                # computed until setting components
                durRaw.quarterLength = qLen
                try:
                    d.components = durRaw.components
                except duration.DurationException:  # TODO: Test
                    if qLen:
                        qLenRounded = 2.0 ** round(math.log2(qLen))
                    else:
                        qLenRounded = 0.0
                    environLocal.printDebug(
                        ['mxToDuration',
                         f'rounding duration to {qLenRounded} as type is not'
                         + 'defined and raw quarterLength '
                         + f'({qLen}) is not a computable duration'])
                    # environLocal.printDebug(['mxToDuration', 'raw qLen', qLen, durationType,
                    #                         'mxNote:',
                    #                         ET.tostring(mxNote, encoding='unicode'),
                    #                         'last mxDivisions:', divisions])
                    durRaw.quarterLength = qLenRounded
            else:
                d = duration.Duration(quarterLength=qLen)
        else:  # a cooked version builds up from pieces
            dt = duration.durationTupleFromTypeDots(durationType, numDots)
            if d is not None:
                d.clear()
                d.addDurationTuple(dt)
            else:
                d = duration.Duration(durationTuple=dt)

            for tup in tuplets:
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

        try:
            post.duration.stealTimePrevious = int(mxGrace.get('steal-time-previous')) / 100
        except TypeError:
            pass

        try:
            post.duration.stealTimeFollowing = int(mxGrace.get('steal-time-following')) / 100
        except TypeError:
            pass

        # TODO: make-time -- maybe; or this is something totally different.

        return post

    def xmlNotations(self, mxNotations, n):
        # noinspection PyShadowingNames
        '''
        >>> from xml.etree.ElementTree import fromstring as EL
        >>> MP = musicxml.xmlToM21.MeasureParser()

        >>> mxNotations = EL('<notations>' +
        ...     '<fermata type="upright">angled</fermata>' +
        ...     '</notations>')
        >>> n = note.Note()
        >>> MP.xmlNotations(mxNotations, n)
        >>> n.expressions
        [<music21.expressions.Fermata>]
        >>> n.expressions[0].type
        'upright'
        >>> n.expressions[0].shape
        'angled'
        '''
        # attr: print-object -- applies to all
        printObjectValue = mxNotations.get('print-object')
        if printObjectValue == 'no':
            hideObject = True
        else:
            hideObject = False

        def optionalHideObject(obj):
            if not hideObject:
                return
            obj.style.hideObjectOnPrint = True

        # tied is handled with tie
        # tuplet is handled with time-modification.

        # TODO: dynamics
        # TODO: arpeggiate
        # TODO: non-arpeggiate
        # TODO: accidental-mark
        # TODO: other-notation

        def flatten(mx, name):
            findall = mx.findall(name)
            return common.flattenList(findall)

        for mxObj in flatten(mxNotations, 'technical'):
            technicalObj = self.xmlTechnicalToArticulation(mxObj)
            optionalHideObject(technicalObj)
            if technicalObj is not None:
                n.articulations.append(technicalObj)

        for mxObj in flatten(mxNotations, 'articulations'):
            articulationObj = self.xmlToArticulation(mxObj)
            optionalHideObject(articulationObj)
            if articulationObj is not None:
                n.articulations.append(articulationObj)

        # get any fermatas, store on expressions
        for mxObj in mxNotations.findall('fermata'):
            fermata = expressions.Fermata()
            optionalHideObject(fermata)
            self.setEditorial(mxNotations, fermata)

            fermataType = mxObj.get('type')
            if fermataType is not None:
                fermata.type = fermataType
            if textStripValid(mxObj):
                fermata.shape = mxObj.text.strip()
            n.expressions.append(fermata)

        for mxObj in flatten(mxNotations, 'ornaments'):
            if mxObj.tag in xmlObjects.ORNAMENT_MARKS:
                post = self.xmlOrnamentToExpression(mxObj)
                optionalHideObject(post)
                self.setEditorial(mxNotations, post)
                if post is not None:
                    n.expressions.append(post)
                # environLocal.printDebug(['adding to expressions', post])
            elif mxObj.tag == 'wavy-line':
                trillExtObj = self.xmlOneSpanner(mxObj, n, expressions.TrillExtension)
                optionalHideObject(trillExtObj)
                self.setEditorial(mxNotations, trillExtObj)

            elif mxObj.tag == 'tremolo':
                trem = self.xmlToTremolo(mxObj, n)
                optionalHideObject(trem)
                self.setEditorial(mxNotations, trem)

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

        Fingering might have substitution or alternate

        >>> mxTech = EL('<fingering substitution="yes">5</fingering>')
        >>> f = MP.xmlTechnicalToArticulation(mxTech)
        >>> f
        <music21.articulations.Fingering 5>
        >>> f.substitution
        True
        >>> f.alternate
        False

        FingerNumbers get converted to ints if possible

        >>> f.fingerNumber
        5


        >>> mxTech = EL('<fingering alternate="yes">4-3</fingering>')
        >>> f = MP.xmlTechnicalToArticulation(mxTech)
        >>>
        <music21.articulations.Fingering 4-3>
        >>> f.alternate
        True
        >>> f.fingerNumber
        '4-3'
        '''
        tag = mxObj.tag
        if tag in xmlObjects.TECHNICAL_MARKS:
            tech = xmlObjects.TECHNICAL_MARKS[tag]()
            _synchronizeIds(mxObj, tech)
            if tag == 'fingering':
                self.handleFingering(tech, mxObj)
            if tag in ('handbell', 'other-technical') and textStripValid(mxObj):
                #     The handbell element represents notation for various
                #     techniques used in handbell and handchime music. Valid
                #     values are belltree [v3.1], damp, echo, gyro, hand martellato,
                #     mallet lift, mallet table, martellato, martellato lift,
                #     muted martellato, pluck lift, and swing.
                tech.displayText = mxObj.text
            if tag in ('fret', 'string'):
                try:
                    tech.number = int(mxObj.text)
                except (ValueError, TypeError) as unused_err:
                    pass
            if tag == 'harmonic':
                self.setHarmonic(mxObj, tech)
            if tag in ('heel', 'toe'):
                if mxObj.get('substitution') is not None:
                    tech.substitution = xmlObjects.yesNoToBoolean(mxObj.get('substitution'))

            self.setPlacement(mxObj, tech)
            return tech
        else:
            environLocal.printDebug(f'Cannot translate {tag} in {mxObj}.')
            return None

    @staticmethod
    def setHarmonic(mxh, harm):
        '''
        From the artificial or natural tag (or no tag) and
        zero or one of base-pitch, sounding-pitch, touching-pitch,
        sets .harmonicType and .pitchType on a articulations.Harmonic object

        Called from xmlTechnicalToArticulation

        >>> from xml.etree.ElementTree import fromstring as EL
        >>> MP = musicxml.xmlToM21.MeasureParser()

        >>> mxTech = EL('<harmonic><artificial/><sounding-pitch/></harmonic>')
        >>> a = MP.xmlTechnicalToArticulation(mxTech)
        >>> a
        <music21.articulations.StringHarmonic>

        >>> a.harmonicType
        'artificial'
        >>> a.pitchType
        'sounding'
        '''
        if mxh.find('artificial') is not None:
            harm.harmonicType = 'artificial'
        elif mxh.find('natural') is not None:
            harm.harmonicType = 'natural'

        if mxh.find('base-pitch') is not None:
            harm.pitchType = 'base'
        elif mxh.find('sounding-pitch') is not None:
            harm.pitchType = 'sounding'
        elif mxh.find('touching-pitch') is not None:
            harm.pitchType = 'touching'

    def handleFingering(self, tech, mxObj):
        '''
        A few specialized functions for dealing with fingering objects
        '''
        tech.fingerNumber = mxObj.text
        try:
            tech.fingerNumber = int(tech.fingerNumber)
        except (ValueError, TypeError) as unused_err:
            pass
        if mxObj.get('substitution') is not None:
            tech.substitution = xmlObjects.yesNoToBoolean(mxObj.get('substitution'))
        if mxObj.get('alternate') is not None:
            tech.alternate = xmlObjects.yesNoToBoolean(mxObj.get('alternate'))

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

        >>> mxArt = EL('<doit dash-length="2" default-x="5" default-y="2" '
        ...            + 'line-shape="curved" line-type="dashed" space-length="1" />')
        >>> a = MP.xmlToArticulation(mxArt)
        >>> a
        <music21.articulations.Doit>
        >>> a.placement is None
        True
        >>> a.style.dashLength
        2
        >>> a.style.absoluteX
        5
        >>> a.style.lineShape
        'curved'
        '''
        tag = mxObj.tag
        if tag in xmlObjects.ARTICULATION_MARKS:
            articulationObj = xmlObjects.ARTICULATION_MARKS[tag]()
            _synchronizeIds(mxObj, articulationObj)

            self.setPrintStyle(mxObj, articulationObj)
            self.setPlacement(mxObj, articulationObj)

            # particular articulations have extra information.
            if tag == 'strong-accent':
                pointDirection = mxObj.get('type')
                if pointDirection is not None:
                    articulationObj.pointDirection = pointDirection
            if tag in ('doit', 'falloff', 'plop', 'scoop'):
                self.setLineStyle(mxObj, articulationObj)
            if tag == 'breath-mark' and textStripValid(mxObj):
                articulationObj.symbol = mxObj.text
            if tag == 'other-articulation' and textStripValid(mxObj):
                articulationObj.displayText = mxObj.text

            return articulationObj
        else:
            environLocal.printDebug(f'Cannot translate {tag} in {mxObj}.')
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

        >>> mxOrn = EL('<inverted-turn placement="above" font-size="24"/>')
        >>> a = MP.xmlOrnamentToExpression(mxOrn)
        >>> a
        <music21.expressions.InvertedTurn>
        >>> a.placement
        'above'
        >>> a.style.fontSize
        24

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
        except KeyError:  # should already be checked...
            return None
        self.setPrintStyle(mxObj, orn)
        # trill-sound?
        self.setPlacement(mxObj, orn)
        return orn

    def xmlDirectionTypeToSpanners(self, mxObj):
        # noinspection PyShadowingNames
        '''
        Some spanners, such as MusicXML wedge, bracket, and dashes,
        are encoded as MusicXML directions.

        >>> from xml.etree.ElementTree import fromstring as EL
        >>> MP = musicxml.xmlToM21.MeasureParser()
        >>> n1 = note.Note('D4')
        >>> MP.nLast = n1

        >>> len(MP.spannerBundle)
        0
        >>> mxDirectionType = EL('<wedge type="crescendo" number="2"/>')
        >>> retList = MP.xmlDirectionTypeToSpanners(mxDirectionType)
        >>> retList
        [<music21.dynamics.Crescendo>]

        >>> len(MP.spannerBundle)
        1
        >>> sp = MP.spannerBundle[0]
        >>> sp
        <music21.dynamics.Crescendo>

        >>> mxDirectionType2 = EL('<wedge type="stop" number="2"/>')
        >>> retList = MP.xmlDirectionTypeToSpanners(mxDirectionType2)

        retList is empty because nothing new has been added.

        >>> retList
        []

        >>> len(MP.spannerBundle)
        1
        >>> sp = MP.spannerBundle[0]
        >>> sp
        <music21.dynamics.Crescendo <music21.note.Note D>>
        '''
        targetLast = self.nLast
        returnList = []

        if mxObj.tag == 'wedge':
            mType = mxObj.get('type')
            if mType == 'crescendo':
                spClass = dynamics.Crescendo
            elif mType == 'diminuendo':
                spClass = dynamics.Diminuendo
            elif mType == 'stop':
                spClass = dynamics.DynamicWedge  # parent of Cresc/Dim
            else:
                raise MusicXMLImportException(f'Unknown type, {mType}.')

            if mType != 'stop':
                sp = self.xmlOneSpanner(mxObj, None, spClass, allowDuplicateIds=True)
                returnList.append(sp)
                self.spannerBundle.setPendingSpannedElementAssignment(sp, 'GeneralNote')
            else:
                idFound = mxObj.get('number')
                spb = self.spannerBundle.getByClassIdLocalComplete(
                    'DynamicWedge', idFound, False)  # get first
                try:
                    sp = spb[0]
                except IndexError:
                    raise MusicXMLImportException('Error in getting DynamicWedges')
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
                    height = mxObj.get('end-length')
                    if height is not None:
                        sp.startHeight = float(height)
                    sp.startTick = mxObj.get('line-end')
                    sp.lineType = mxObj.get('line-type')

                self.spannerBundle.append(sp)
                returnList.append(sp)
                # define this spanner as needing component assignment from
                # the next general note
                self.spannerBundle.setPendingSpannedElementAssignment(sp, 'GeneralNote')
            elif mxType == 'stop':
                # need to retrieve an existing spanner
                # try to get base class of both Crescendo and Decrescendo
                try:
                    sp = self.spannerBundle.getByClassIdLocalComplete(
                        'Line', idFound, False)[0]
                    # get first
                except IndexError:
                    environLocal.warn('Line <' + mxObj.tag + '> stop without start')
                    return []
                sp.completeStatus = True

                if mxObj.tag == 'dashes':
                    sp.endTick = 'none'
                    sp.lineType = 'dashed'
                else:
                    sp.endTick = mxObj.get('line-end')
                    height = mxObj.get('end-length')
                    if height is not None:
                        sp.endHeight = float(height)
                    sp.lineType = mxObj.get('line-type')

                # will only have a target if this follows the note
                if targetLast is not None:
                    sp.addSpannedElements(targetLast)
            else:
                raise MusicXMLImportException(f'unidentified mxType of mxBracket: {mxType}')
        return returnList

    def xmlNotationsToSpanners(self, mxNotations, n):
        # TODO: mxNotations attr: print-object

        for mxObj in mxNotations.findall('slur'):
            slur = self.xmlOneSpanner(mxObj, n, spanner.Slur)
            self.setLineStyle(mxObj, slur)
            self.setPosition(mxObj, slur)
            self.setPlacement(mxObj, slur)
            # TODO: attr orientation
            self.setStyleAttributes(mxObj,
                                    slur,
                                    ('bezier-offset', 'bezier-offset2',
                                     'bezier-x', 'bezier-y',
                                     'bezier-x2', 'bezier-y2')
                                    )
            self.setColor(mxObj, slur)

        for tagSearch in ('glissando', 'slide'):
            for mxObj in mxNotations.findall(tagSearch):
                gliss = self.xmlOneSpanner(mxObj, n, spanner.Glissando)
                if tagSearch == 'slide':
                    gliss.slideType = 'continuous'
                self.setLineStyle(mxObj, gliss)
                if not mxObj.get('line-type') and tagSearch == 'slide':
                    gliss.lineType = 'solid'
                    gliss.style.lineType = 'solid'

                # TODO: attr bend-sound on <slide> only
                self.setPrintStyle(mxObj, gliss)
                _synchronizeIds(mxObj, gliss)

    def xmlToTremolo(self, mxTremolo, n):
        '''
        Converts an mxTremolo to either an expression to be added to n.expressions
        or to a spanner, returning either.
        '''
        # tremolo is tricky -- can be either an
        # expression or spanner...
        tremoloType = mxTremolo.get('type')
        isSingle = True
        if tremoloType in ('start', 'stop'):
            isSingle = False

        try:
            numMarks = int(mxTremolo.text.strip())
        except (ValueError, AttributeError):
            # environLocal.warn('could not convert ', dir(mxObj))
            numMarks = 3
        if isSingle is True:
            ts = expressions.Tremolo()
            ts.numberOfMarks = numMarks
            n.expressions.append(ts)
            return ts
        else:
            tremSpan = self.xmlOneSpanner(mxTremolo, n, expressions.TremoloSpanner)
            tremSpan.numberOfMarks = numMarks
            return tremSpan

    def xmlOneSpanner(self, mxObj, target, spannerClass, *, allowDuplicateIds=False):
        '''
        Some spanner types do not have an id necessarily, we allow duplicates of them
        if allowDuplicateIds is True. Wedges are one.

        Returns the new spanner created.
        '''
        idFound = mxObj.get('number')

        # returns a new spanner bundle with just the result of the search
        sb = self.spannerBundle.getByClassIdLocalComplete(spannerClass, idFound, False)
        if sb and allowDuplicateIds is False:
            # if we already have a spanner matching
            # environLocal.printDebug(['found a match in SpannerBundle'])
            su = sb[0]  # get the first
        else:  # create a new slur
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
        # environLocal.printDebug(['adding n', n, id(n), 'su.getSpannedElements',
        #     su.getSpannedElements(), su.getSpannedElementIds()])
        if mxObj.get('type') == 'stop':
            su.completeStatus = True
            # only add after complete
        elif mxObj.get('type') == 'start':
            _synchronizeIds(mxObj, su)

        return su

    def xmlToTie(self, mxNote):
        # noinspection PyShadowingNames
        '''
        Translate a MusicXML <note> with <tie> SubElements
        :class:`~music21.tie.Tie` object

        >>> import xml.etree.ElementTree as ET
        >>> MP = musicxml.xmlToM21.MeasureParser()

        Create the incomplete part of a Note.

        >>> mxNote = ET.fromstring('<note><tie type="start" />'
        ...            + '<notations>'
        ...            + '<tied line-type="dotted" placement="below" type="start" />'
        ...            + '</notations></note>')
        >>> t = MP.xmlToTie(mxNote)
        >>> t.type
        'start'
        >>> t.style
        'dotted'
        >>> t.placement
        'below'

        Same thing but with orientation instead of placement, which both get mapped to
        placement in Tie objects

        >>> mxNote = ET.fromstring('<note><tie type="start" />'
        ...            + '<notations>'
        ...            + '<tied line-type="dotted" orientation="over" type="start" />'
        ...            + '</notations></note>')
        >>> t = MP.xmlToTie(mxNote)
        >>> t.placement
        'above'
        '''
        t = tie.Tie()
        allTies = mxNote.findall('tie')
        if not allTies:
            return None

        typesFound = []
        for mxTie in allTies:
            foundType = mxTie.get('type')
            if foundType is not None:
                typesFound.append(foundType)
            else:
                environLocal.printDebug('found tie element without required type')

        if len(typesFound) == 1:
            t.type = typesFound[0]
        elif 'stop' in typesFound and 'start' in typesFound:
            t.type = 'continue'
        else:
            environLocal.printDebug(
                ['found unexpected arrangement of multiple tie types when '
                 + 'importing from musicxml:', typesFound])

        # TODO: get everything else from <tied>
        #     besides line-style, placement, and orientation. such as bezier
        #     blocking on redoing tie.Tie to not use "style"
        mxNotations = mxNote.find('notations')
        if mxNotations is not None:
            mxTiedList = mxNotations.findall('tied')
            if mxTiedList:
                firstTied = mxTiedList[0]
                _synchronizeIds(firstTied, t)

                tieStyle = firstTied.get('line-type')
                if tieStyle is not None and tieStyle != 'wavy':  # do not support wavy...
                    t.style = tieStyle
                placement = firstTied.get('placement')
                if placement is not None:
                    t.placement = placement
                else:
                    orientation = mxTiedList[0].get('orientation')
                    if orientation == 'over':
                        t.placement = 'above'
                    elif orientation == 'under':
                        t.placement = 'below'
        return t

    def xmlToTuplets(self, mxNote):
        # noinspection PyShadowingNames
        '''
        Given an mxNote, based on mxTimeModification
        and mxTuplet objects, return a list of Tuplet objects

        >>> import xml.etree.ElementTree as ET
        >>> MP = musicxml.xmlToM21.MeasureParser()

        >>> mxNote = ET.fromstring('<note><type>16th</type>' +
        ...    '<time-modification><actual-notes>5</actual-notes>' +
        ...    '<normal-notes>4</normal-notes></time-modification></note>')
        >>> t = MP.xmlToTuplets(mxNote)
        >>> t
        [<music21.duration.Tuplet 5/4/16th>]

        >>> mxNote = ET.fromstring('<note><type>eighth</type>' +
        ...    '<time-modification><actual-notes>5</actual-notes>' +
        ...    '<normal-notes>3</normal-notes>' +
        ...    '<normal-type>16th</normal-type><normal-dot /><normal-dot />' +
        ...    '</time-modification></note>')
        >>> t = MP.xmlToTuplets(mxNote)
        >>> t
        [<music21.duration.Tuplet 5/3/16th>]
        >>> t[0].durationNormal
        DurationTuple(type='16th', dots=2, quarterLength=0.4375)
        '''
        t = duration.Tuplet()
        mxTimeModification = mxNote.find('time-modification')
        # environLocal.printDebug(['got mxTimeModification', mxTimeModification])

        # This should only be a backup in case there are no tuplet definitions
        # in the tuplet tag.
        seta = _setAttributeFromTagText
        seta(t, mxTimeModification, 'actual-notes', 'numberNotesActual', transform=int)
        seta(t, mxTimeModification, 'normal-notes', 'numberNotesNormal', transform=int)

        mxNormalType = mxTimeModification.find('normal-type')
        if textStripValid(mxNormalType):
            musicXMLNormalType = mxNormalType.text.strip()
        else:
            musicXMLNormalType = mxNote.find('type').text.strip()

        durationNormalType = musicXMLTypeToType(musicXMLNormalType)
        numDots = len(mxTimeModification.findall('normal-dot'))

        t.setDurationType(durationNormalType, numDots)

        mxNotations = mxNote.find('notations')
        if mxNotations is None:
            self.activeTuplets[0] = t
        # environLocal.printDebug(['got mxNotations', mxNotations])

        remainingTupletAmountToAccountFor = t.tupletMultiplier()
        timeModTup = t

        returnTuplets = [None] * 8  # type: List[Optional['music21.duration.Tuplet']]
        removeFromActiveTuplets = set()

        # a set of tuplets to set to stop...
        tupletsToStop = set()

        if mxNotations is not None:
            mxTuplets = mxNotations.findall('tuplet')
            for mxTuplet in mxTuplets:
                # TODO: combine start + stop into startStop.
                t.type = mxTuplet.get('type')  # required
                tupletNumberStr = mxTuplet.get('number')  # str '1' to '6' or None
                # no tuplet number is equal to 1
                tupletIndex = int(tupletNumberStr) if tupletNumberStr is not None else 1

                if t.type == 'stop':
                    if self.activeTuplets[tupletIndex] is not None:
                        activeT = self.activeTuplets[tupletIndex]
                        if activeT in returnTuplets:
                            activeT.type = 'startStop'
                        removeFromActiveTuplets.add(tupletIndex)
                        tupletsToStop.add(tupletIndex)

                    continue

                mxTupletActual = mxTuplet.find('tuplet-actual')
                mxTupletNormal = mxTuplet.find('tuplet-normal')
                if mxTupletActual is None or mxTupletNormal is None:
                    # in theory either can be absent, but so far I have only seen both present
                    # or both absent
                    t = copy.deepcopy(timeModTup)
                else:
                    t = duration.Tuplet()
                    seta(t, mxTupletActual,
                         'tuplet-number', 'numberNotesActual', transform=int)
                    seta(t, mxTupletNormal,
                         'tuplet-number', 'numberNotesNormal', transform=int)

                    mxActualType = mxTupletActual.find('tuplet-type')
                    if mxActualType is not None:
                        xmlActualType = mxActualType.text.strip()
                        durType = musicXMLTypeToType(xmlActualType)
                        dots = len(mxActualType.findall('tuplet-dot'))
                        t.durationActual = duration.durationTupleFromTypeDots(durType, dots)

                    mxNormalType = mxTupletNormal.find('tuplet-type')
                    if mxNormalType is not None:
                        xmlNormalType = mxNormalType.text.strip()
                        durType = musicXMLTypeToType(xmlNormalType)
                        dots = len(mxNormalType.findall('tuplet-dot'))
                        t.durationNormal = duration.durationTupleFromTypeDots(durType, dots)

                bracketMaybe = mxTuplet.get('bracket')
                if bracketMaybe is not None:
                    t.bracket = xmlObjects.yesNoToBoolean(bracketMaybe)
                # environLocal.printDebug(['got bracket', self.bracket])
                showNumber = mxTuplet.get('show-number')
                if showNumber is not None and showNumber == 'none':
                    t.tupletActualShow = None
                    if bracketMaybe is None:
                        t.bracket = False
                elif showNumber is not None and showNumber == 'both':
                    t.tupletNormalShow = 'number'

                showType = mxTuplet.get('show-type')
                if showType is not None and showType == 'actual':
                    t.tupletActualShow = 'both' if t.tupletActualShow is not None else 'type'
                elif showNumber is not None and showNumber == 'both':
                    t.tupletActualShow = 'both' if t.tupletActualShow is not None else 'type'
                    t.tupletNormalShow = 'both' if t.tupletNormalShow is not None else 'type'

                lineShape = mxTuplet.get('line-shape')
                if lineShape is not None and lineShape == 'curved':
                    t.bracket = 'slur'
                # TODO: default-x, default-y, relative-x, relative-y
                t.placement = mxTuplet.get('placement')
                returnTuplets[tupletIndex] = t
                remainingTupletAmountToAccountFor /= t.tupletMultiplier()
                self.activeTuplets[tupletIndex] = t

        # find all activeTuplets that haven't been accounted for.
        for i in range(1, len(self.activeTuplets)):
            thisActive = self.activeTuplets[i]
            if thisActive is None:
                continue
            if thisActive in returnTuplets:
                continue
            thisActiveCopy = copy.deepcopy(thisActive)
            if i in tupletsToStop:
                thisActiveCopy.type = 'stop'
            else:
                thisActiveCopy.type = None
            remainingTupletAmountToAccountFor /= thisActiveCopy.tupletMultiplier()
            returnTuplets[i] = thisActiveCopy

        # if there is anything left to
        if remainingTupletAmountToAccountFor != 1:
            remainderFraction = fractions.Fraction(remainingTupletAmountToAccountFor)
            remainderTuplet = duration.Tuplet(remainderFraction.denominator,
                                              remainderFraction.numerator)
            remainderTuplet.durationNormal = timeModTup.durationNormal
            remainderTuplet.durationActual = timeModTup.durationActual
            returnTuplets[-1] = remainderTuplet

        # now we can remove stops for future notes.
        for tupletIndexToRemove in removeFromActiveTuplets:
            # set to stop before removing
            self.activeTuplets[tupletIndexToRemove] = None

        returnTuplets = [t for t in returnTuplets if t is not None]

        return returnTuplets

    def updateLyricsFromList(self, n, lyricList):
        # noinspection PyShadowingNames
        '''
        Takes a list of <lyric> elements and update the
        note's lyrics from that list.

        >>> import xml.etree.ElementTree as ET
        >>> MP = musicxml.xmlToM21.MeasureParser()

        >>> mxLyric1 = ET.fromstring('<lyric><text>Hi</text><elision/><text>There</text></lyric>')
        >>> mxLyric2 = ET.fromstring('<lyric><text>Bye</text></lyric>')
        >>> n = note.Note()
        >>> MP.updateLyricsFromList(n, [mxLyric1, mxLyric2])
        >>> n.lyrics
        [<music21.note.Lyric number=1 syllabic=composite text='Hi There'>,
         <music21.note.Lyric number=2 text='Bye'>]
        '''
        currentLyricNumber = 1
        for mxLyric in lyricList:
            lyricObj = self.xmlToLyric(mxLyric)
            if lyricObj is None:
                continue
            if lyricObj.number == 0:
                lyricObj.number = currentLyricNumber
            n.lyrics.append(lyricObj)
            currentLyricNumber += 1

    def xmlToLyric(self, mxLyric, inputM21=None) -> Optional[note.Lyric]:
        # noinspection PyShadowingNames
        '''
        Translate a MusicXML <lyric> tag to a
        music21 :class:`~music21.note.Lyric` object or return None if no Lyric object
        should be created (empty lyric tags, for instance)

        If inputM21 is a :class:`~music21.note.Lyric` object, then the values of the
        mxLyric are transferred there and nothing returned.

        Otherwise, a new `Lyric` object is created and returned.

        >>> import xml.etree.ElementTree as ET
        >>> MP = musicxml.xmlToM21.MeasureParser()

        >>> mxLyric = ET.fromstring('<lyric number="4" color="red">'
        ...                         + '<syllabic>single</syllabic>'
        ...                         + '<text>word</text></lyric>')
        >>> lyricObj = note.Lyric()
        >>> MP.xmlToLyric(mxLyric, lyricObj)
        >>> lyricObj
        <music21.note.Lyric number=4 syllabic=single text='word'>
        >>> lyricObj.style.color
        'red'

        Non-numeric MusicXML lyric "number"s are converted to identifiers:

        >>> mxLyric.set('number', 'part2verse1')
        >>> l2 = MP.xmlToLyric(mxLyric)
        >>> l2
        <music21.note.Lyric number=0 identifier='part2verse1' syllabic=single text='word'>


        Multiple texts can be created and result in composite lyrics

        >>> mxBianco = ET.fromstring('<lyric>'
        ...                         + '<syllabic>end</syllabic>'
        ...                         + '<text>co</text>'
        ...                         + '<elision>_</elision>'
        ...                         + '<syllabic>single</syllabic>'
        ...                         + '<text>e</text>'
        ...                         + '</lyric>')
        >>> bianco = MP.xmlToLyric(mxBianco)
        >>> bianco
        <music21.note.Lyric number=0 syllabic=composite text='co_e'>
        >>> bianco.components
        [<music21.note.Lyric number=1 syllabic=end text='co'>,
         <music21.note.Lyric number=1 syllabic=single text='e'>]
        '''
        if inputM21 is None:
            ly = note.Lyric()
        else:
            ly = inputM21

        # TODO: extend
        # TODO: humming
        # TODO: laughing
        # TODO: end-line
        # TODO: end-paragraph
        # TODO: footnote
        # TODO: level

        # when lyrics get ids, we should get that ID
        text_elements = mxLyric.findall('text')
        syllabic_elements = mxLyric.findall('syllabic')
        elision_elements = mxLyric.findall('elision')

        if not text_elements:
            # sometimes there are empty lyrics
            if inputM21 is None:
                return ly
            return None

        if len(text_elements) == 1:
            # standard case -- a lyric has a single text.
            element_text = text_elements[0].text
            if element_text is not None:
                ly.text = element_text.strip()
            try:
                ly.syllabic = syllabic_elements[0].text.strip()
            except (ValueError, IndexError):
                pass  # syllabic is optional.
        else:
            # composite lyric, like "co" "e" in "Il bianco_e dolce"
            ly.components = []
            for i, mxText in enumerate(text_elements):
                component = note.Lyric()
                ly.components.append(component)
                if mxText.text is not None:
                    component.text = mxText.text.strip()  # there are empty text tags

                try:
                    # Note that this is not entirely accurate.  There
                    # could be omitted syllabic tags in the middle of a text
                    # stream, and this will shift them over.  But anyone using
                    # multiple text tags with omitted syllabic tags is asking
                    # for difficulties
                    mxSyllabic = syllabic_elements[i]
                    component.syllabic = mxSyllabic.text.strip()

                    if i >= 1:
                        mxElision = elision_elements[i - 1]

                        # only gets to here if no index error.
                        elision_text = mxElision.text  # do not strip -- space is important4
                        if elision_text is None:
                            elision_text = ''
                        component.elisionBefore = elision_text
                except (IndexError, ValueError, AttributeError):
                    pass

        # This is new to account for identifiers
        number = mxLyric.get('number')

        try:
            number = int(number)
            ly.number = number
        except (TypeError, ValueError):
            # If musicXML lyric number is not a number, set it to 0.
            # This tells the caller of mxToLyric that a new number needs
            # to be given based on the lyric's context amongst other lyrics.
            ly.number = 0
            if number is not None:
                ly.identifier = number

        identifier = mxLyric.get('name')
        if identifier is not None:
            ly.identifier = identifier

        self.setStyleAttributes(mxLyric, ly,
                                ('justify', 'placement', 'print-object'),
                                ('justify', 'placement', 'hideObjectOnPrint'))
        self.setColor(mxLyric, ly)
        self.setPosition(mxLyric, ly)

        if inputM21 is None:
            return ly

    def insertInMeasureOrVoice(self, mxElement, el):
        '''
        Adds an object to a measure or a voice.  Needs a note element (obviously)
        but also mxNote to get the voice.  Uses coreInsert and thus leaves insertStream
        on the inner voice in an unusable state.
        '''
        insertStream = self.stream
        if not self.useVoices:
            insertStream.coreInsert(self.offsetMeasureNote, el)
            return

        mxVoice = mxElement.find('voice')
        thisVoice = self.findM21VoiceFromXmlVoice(mxVoice)
        if thisVoice is not None:
            insertStream = thisVoice
        insertStream.coreInsert(self.offsetMeasureNote, el)

    def findM21VoiceFromXmlVoice(self, mxVoice=None):
        '''
        Find the stream.Voice object from a <voice> tag or None.
        '''
        m = self.stream
        if not textStripValid(mxVoice):
            useVoice = self.chordVoice
            if useVoice is None:
                environLocal.warn('Cannot put in an element with a missing voice tag when '
                                  + 'no previous voice tag was given.  Assuming voice 1... '
                                  )
                useVoice = 1
        else:
            useVoice = mxVoice.text.strip()

        thisVoice = None
        if useVoice in self.voicesById:
            thisVoice = self.voicesById[useVoice]
        elif int(useVoice) in self.voicesById:
            thisVoice = self.voicesById[int(useVoice)]
        elif str(useVoice) in self.voicesById:
            thisVoice = self.voicesById[str(useVoice)]
        else:
            environLocal.warn(f'Cannot find voice {useVoice!r}; putting outside of voices.')
            environLocal.warn(f'Current voiceIds: {list(self.voicesById)}')
            environLocal.warn(f'Current voices: {m.voices}')

        return thisVoice

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
            # environLocal.printDebug(['found mxEndingObj', mxEndingObj, 'm', m])
            # get all incomplete spanners of the appropriate class that are
            # not complete

            # TODO: this should also filter by number (in theory.)
            rbSpanners = self.spannerBundle.getByClass('RepeatBracket').getByCompleteStatus(False)
            # if we have no complete bracket objects, must start a new one
            if not rbSpanners:
                # create with this measure as the object
                rb = spanner.RepeatBracket(m)
                self.spannerBundle.append(rb)
            # if we have any incomplete, this must be the end
            else:
                # environLocal.printDebug(['matching RepeatBracket spanner',
                #    'len(rbSpanners)', len(rbSpanners)])
                rb = rbSpanners[0]  # get RepeatBracket
                # try to add this measure; may be the same
                rb.addSpannedElements(m)

            if mxEndingObj.get('type') == 'start':
                mxNumber = mxEndingObj.get('number')
                # RepeatBracket handles comma-separated values, such as "1,2"
                try:
                    rb.number = mxNumber
                except spanner.SpannerException:
                    rb.number = 1

                # however, if the content is different, use that.
                # for instance, Finale often uses <ending number="1">2.</ending> for
                # second endings, since the first ending number has already been closed.
                endingNumberText = mxEndingObj.text
                if endingNumberText is not None:
                    rb.overrideDisplay = endingNumberText
                    overrideNumber = re.match(r'^(\d+)\.?$', endingNumberText)  # very cautious
                    if overrideNumber:
                        rb.number = int(overrideNumber.group(1))

            # there may just be an ending marker, and no start
            # this implies just one measure
            if mxEndingObj.get('type') in ('stop', 'discontinue'):
                rb.completeStatus = True

            # set number; '' or None is interpreted as 1

        if barline.location == 'left':
            # environLocal.printDebug(['setting left barline', barline])
            m.leftBarline = barline
        elif barline.location == 'right':
            # environLocal.printDebug(['setting right barline', barline])
            m.rightBarline = barline
        else:  # middle barline
            m.coreElementsChanged()
            m.append(barline)

    def xmlToRepeat(self, mxBarline, inputM21=None):
        # noinspection PyShadowingNames
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

        Test that the music21 type for a backwards repeat is called "final"
        (because it resembles a final barline) even though the musicxml style
        is called light-heavy.

        >>> r.type
        'final'
        >>> r.direction
        'end'
        '''
        if inputM21 is None:
            r = bar.Repeat()
        else:
            r = inputM21

        seta = _setAttributeFromTagText
        seta(r, mxBarline, 'bar-style', 'type')
        self.setEditorial(mxBarline, r)
        # TODO: wavy-line
        # TODO: segno, coda, fermata,
        # TODO: winged
        location = mxBarline.get('location')
        if location is not None:
            r.location = location
        else:
            r.location = 'right'  # default in musicxml 3.0

        mxRepeat = mxBarline.find('repeat')
        if mxRepeat is None:
            raise bar.BarException('attempting to create a Repeat from an MusicXML '
                                   + 'bar that does not define a repeat')

        mxDirection = mxRepeat.get('direction')
        # environLocal.printDebug(['mxRepeat', mxRepeat, mxRepeat._attr])
        if mxDirection is None:
            raise MusicXMLImportException('Repeat sign direction is required')

        if mxDirection.lower() == 'forward':
            r.direction = 'start'
        elif mxDirection.lower() == 'backward':
            r.direction = 'end'
        else:
            raise bar.BarException('cannot handle mx direction format:', mxDirection)

        if mxRepeat.get('times') is not None:
            # make into a number
            r.times = int(mxRepeat.get('times'))

        if inputM21 is None:
            return r

    def xmlToBarline(self, mxBarline, inputM21=None):
        # noinspection PyShadowingNames
        '''
        Given an mxBarline, fill the necessary parameters

        >>> import xml.etree.ElementTree as ET
        >>> MP = musicxml.xmlToM21.MeasureParser()

        >>> mxBarline = ET.fromstring(
        ...    '<barline location="right"><bar-style>light-light</bar-style></barline>')
        >>> b = MP.xmlToBarline(mxBarline)
        >>> b
        <music21.bar.Barline type=double>
        >>> b.type  # music21.type is different than musicxml.style
        'double'
        >>> b.location
        'right'
        '''
        if inputM21 is None:
            b = bar.Barline()
        else:
            b = inputM21

        seta = _setAttributeFromTagText
        seta(b, mxBarline, 'bar-style', 'type')
        location = mxBarline.get('location')
        if location is not None:
            b.location = location
        else:
            b.location = 'right'  # default in musicxml 3.0

        if inputM21 is None:
            return b

    def xmlHarmony(self, mxHarmony):
        '''
        Create a ChordSymbol object and insert it to the core and staff reference.
        '''
        h = self.xmlToChordSymbol(mxHarmony)
        chordOffset = self.xmlToOffset(mxHarmony)
        self.insertCoreAndRef(self.offsetMeasureNote + chordOffset,
                              mxHarmony, h)

    def xmlToChordSymbol(self, mxHarmony):
        # noinspection PyShadowingNames
        '''
        Convert a <harmony> tag to a harmony.ChordSymbol object:

        >>> from xml.etree.ElementTree import fromstring as EL
        >>> MP = musicxml.xmlToM21.MeasureParser()

        >>> elStr = '<harmony><root><root-step>D</root-step><root-alter>-1</root-alter>'
        >>> elStr += '</root><kind>major-seventh</kind></harmony>'
        >>> mxHarmony = EL(elStr)

        >>> cs = MP.xmlToChordSymbol(mxHarmony)
        >>> cs
        <music21.harmony.ChordSymbol D-maj7>

        >>> cs.figure
        'D-maj7'

        >>> cs.pitches
        (<music21.pitch.Pitch D-3>,
         <music21.pitch.Pitch F3>,
         <music21.pitch.Pitch A-3>,
         <music21.pitch.Pitch C4>)

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
        (<music21.pitch.Pitch D-3>, <music21.pitch.Pitch F3>,
         <music21.pitch.Pitch A-3>, <music21.pitch.Pitch B-3>)

        >>> cs.root()
        <music21.pitch.Pitch D-3>
        '''
        # TODO: offset
        # staff is covered by insertCoreAndReference
        r = None  # protect against undefined.

        mxKind = mxHarmony.find('kind')
        if textStripValid(mxKind):
            kindText = mxKind.text.strip()
        else:
            kindText = None
        mxFrame = mxHarmony.find('frame')

        # environLocal.printDebug(['mxToChordSymbol():', mxHarmony])
        if mxFrame is not None:
            cs = tablature.ChordWithFretBoard()
        elif kindText == 'none':
            cs = harmony.NoChord()
        else:
            cs = harmony.ChordSymbol()

        self.setEditorial(mxHarmony, cs)
        self.setPrintStyle(mxHarmony, cs)
        self.setPrintObject(mxHarmony, cs)
        # TODO: attr: print-frame
        # TODO: attrGroup: placement

        seta = _setAttributeFromTagText

        # TODO: root vs. function;  see group "harmony-chord")
        mxRoot = mxHarmony.find('root')
        if mxRoot is not None:  # choice: <root> or <function>
            mxRS = mxRoot.find('root-step')
            rootText = mxRS.text
            if rootText in (None, ''):
                rootText = mxRS.get('text')  # two ways to do it... this should do display even
                # if content is supported.
            r = pitch.Pitch(rootText)
            mxRootAlter = mxRoot.find('root-alter')
            if mxRootAlter is not None:
                # can provide integer or float to create accidental on pitch
                r.accidental = pitch.Accidental(float(mxRootAlter.text))
            # set Pitch object on Harmony
            cs.root(r)
        else:
            # function instead
            seta(cs, mxHarmony, 'function', 'romanNumeral')

        if kindText is not None:  # two ways of doing it...
            cs.chordKind = mxKind.text.strip()
            # Get m21 chord kind from dict of musicxml aliases ("dominant" -> "dominant-seventh")
            if cs.chordKind in harmony.CHORD_ALIASES:
                cs.chordKind = harmony.CHORD_ALIASES[cs.chordKind]
            mxKindText = mxKind.get('text')  # attribute
            if mxKindText is not None:
                if not ('NoChord' in cs.classes and mxKindText == ''):
                    cs.chordKindStr = mxKindText
        # TODO: attr: use-symbols
        # TODO: attr: stack-degrees
        # TODO: attr: parentheses-degrees
        # TODO: attr: bracket-degrees
        # TODO: attrGroup: print-style
        # TODO: attrGroup: halign
        # TODO: attrGroup: valign

        mxInversion = mxHarmony.find('inversion')
        if textStripValid(mxInversion):
            try:
                # must be an int
                cs.inversion(int(mxInversion.text.strip()), transposeOnSet=False)
            except ValueError:
                pass
        # TODO: print-style

        clearBassOverride: bool = False
        mxBass = mxHarmony.find('bass')
        if mxBass is not None:
            # required
            b = pitch.Pitch(mxBass.find('bass-step').text)
            # optional
            mxBassAlter = mxBass.find('bass-alter')
            if mxBassAlter is not None:
                # can provide integer or float to create accidental on pitch
                b.accidental = pitch.Accidental(float(mxBassAlter.text))
            # set Pitch object on Harmony
            cs.bass(b)
        else:
            cs.bass(r)  # set the bass to the root if root is none
            # only for the purpose of getting _updatePitches() to run
            # then, we will need to get rid of this untruthful override
            # since there may be an inversion!
            clearBassOverride = True

        mxDegrees = mxHarmony.findall('degree')

        for mxDegree in mxDegrees:  # a list of components
            hd = harmony.ChordStepModification()
            seta(hd, mxDegree, 'degree-value', 'degree', transform=int)
            if hd.degree is None:
                raise MusicXMLImportException('degree-value missing')
            # TODO: - should allow float, but meaningless to allow microtones in this context.
            seta(hd, mxDegree, 'degree-alter', 'interval', transform=int)
            seta(hd, mxDegree, 'degree-type', 'modType')
            cs.addChordStepModification(hd, updatePitches=False)

        if cs.chordKind != 'none':
            cs._updatePitches()
            # environLocal.printDebug(['xmlToChordSymbol(): Harmony object', h])
            if cs.root().name != r.name:
                cs.root(r)

        if clearBassOverride and cs.inversion() is not None:
            # 0 inversion = step 1; 2nd inversion = step 5; 4th inversion = step 9, etc.
            wantedStep = (cs.inversion() * 2) + 1
            cs.bass(cs.getChordStep(wantedStep))
            cs._updatePitches()

        # TODO: frame
        if mxFrame is not None:
            pass
            # TODO: Luke: Uncomment this next line when method is ready...
            # self.xmlFrameToFretBoard(mxFrame, cs)

        return cs

    def xmlDirection(self, mxDirection):
        '''
        convert a <direction> tag to one or more expressions, metronome marks, etc.
        and them to the core and staffReference.
        '''
        offsetDirection = self.xmlToOffset(mxDirection)
        totalOffset = offsetDirection + self.offsetMeasureNote

        # staffKey is the staff that this direction applies to. not
        # found in mxDir but in mxDirection itself.
        staffKey = self.getStaffNumber(mxDirection)
        # TODO: sound
        for mxDirType in mxDirection.findall('direction-type'):
            for mxDir in mxDirType:
                self.setDirectionInDirectionType(mxDir, mxDirection, staffKey, totalOffset)

    def setDirectionInDirectionType(self, mxDir, mxDirection, staffKey, totalOffset):
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
        if tag == 'dynamics':  # fp, mf, etc., each as a tag
            # in rare cases there may be more than one dynamic in the same
            # direction, so we iterate
            for dyn in mxDir:
                m21DynamicText = dyn.tag
                if dyn.tag == 'other-dynamic':
                    m21DynamicText = dyn.text.strip()

                d = dynamics.Dynamic(m21DynamicText)

                _synchronizeIds(dyn, d)
                _setAttributeFromAttribute(d, mxDirection,
                                           'placement', 'positionPlacement')

                self.insertCoreAndRef(totalOffset, staffKey, d)
                self.setEditorial(mxDirection, d)

        elif tag in ('wedge', 'bracket', 'dashes'):
            try:
                spannerList = self.xmlDirectionTypeToSpanners(mxDir)
            except MusicXMLImportException as excep:
                environLocal.warn(f'Could not import {tag}: {excep}')
                spannerList = []

            for sp in spannerList:
                self.setEditorial(mxDirection, sp)

        elif tag in ('coda', 'segno'):
            if tag == 'segno':
                rm = repeat.Segno()
            else:
                rm = repeat.Coda()

            _synchronizeIds(mxDir, rm)
            dX = mxDir.get('default-x')
            if dX is not None:
                rm.style.absoluteX = common.numToIntOrFloat(dX)
            dY = mxDir.get('default-y')
            if dY is not None:
                rm.style.absoluteY = common.numToIntOrFloat(dY)
            self.insertCoreAndRef(totalOffset, staffKey, rm)
            self.setEditorial(mxDirection, rm)

        elif tag == 'metronome':
            mm = self.xmlToTempoIndication(mxDir)
            # SAX was offsetMeasureNote; bug? should be totalOffset???
            self.insertCoreAndRef(totalOffset, staffKey, mm)
            self.setEditorial(mxDirection, mm)

        elif tag == 'rehearsal':
            rm = self.xmlToRehearsalMark(mxDir)
            self.setStyleAttributes(mxDirection, rm, 'placement')
            self.insertCoreAndRef(totalOffset, staffKey, rm)
            self.setEditorial(mxDirection, rm)

        elif tag == 'words':
            textExpression = self.xmlToTextExpression(mxDir)
            # environLocal.printDebug(['got TextExpression object', repr(te)])
            # offset here is a combination of the current position
            # (offsetMeasureNote) and and the direction's offset
            _setAttributeFromAttribute(textExpression, mxDirection,
                                       'placement', 'positionPlacement')

            repeatExpression = textExpression.getRepeatExpression()
            if repeatExpression is not None:
                # the repeat expression stores a copy of the text
                # expression within it; replace it here on insertion
                self.insertCoreAndRef(totalOffset, staffKey, repeatExpression)
                self.setEditorial(mxDirection, repeatExpression)

            else:
                self.insertCoreAndRef(totalOffset, staffKey, textExpression)
                self.setEditorial(mxDirection, textExpression)

    def xmlToTextExpression(self, mxWords):
        '''
        Given an mxDirection, create a textExpression
        '''
        # TODO: switch to using the setPrintAlign, etc.

        # environLocal.printDebug(['mxToTextExpression()', mxWords, mxWords.charData])

        # content can be passed with creation argument
        if textStripValid(mxWords):
            wordText = mxWords.text.strip()
        else:
            wordText = ''
        te = expressions.TextExpression(wordText)
        self.setTextFormatting(mxWords, te)
        self.setPosition(mxWords, te)
        return te

    def xmlToRehearsalMark(self, mxRehearsal):
        '''
        Return a rehearsal mark from a rehearsal tag.
        '''
        if textStripValid(mxRehearsal):
            rehearsalText = mxRehearsal.text.strip()
        else:
            rehearsalText = ''
        rm = expressions.RehearsalMark(rehearsalText)
        self.setTextFormatting(mxRehearsal, rm)
        return rm

    def xmlToTempoIndication(self, mxMetronome, mxWords=None):
        '''
        Given an mxMetronome, convert to either a TempoIndication subclass,
        either a tempo.MetronomeMark or tempo.MetricModulation.

        >>> from xml.etree.ElementTree import fromstring as EL
        >>> MP = musicxml.xmlToM21.MeasureParser()

        >>> m = EL(r'<metronome><per-minute>125</per-minute>' +
        ...         '<beat-unit>half</beat-unit></metronome>')
        >>> MP.xmlToTempoIndication(m)
        <music21.tempo.MetronomeMark Half=125.0>

        Metric modulation:

        >>> m = EL(r'<metronome><beat-unit>long</beat-unit><beat-unit>32nd</beat-unit>' +
        ...         '<beat-unit-dot/></metronome>')
        >>> MP.xmlToTempoIndication(m)
        <music21.tempo.MetricModulation
         <music21.tempo.MetronomeMark Imperfect Longa=None>=<music21.tempo.MetronomeMark
                   Dotted 32nd=None>>
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
                dActive.dots += 1  # add one dot each time these are encountered
            # should come last
            elif tag == 'per-minute':
                # environLocal.printDebug(['found PerMinute', mxObj])
                # store as a number
                perMin = mxObj.text
                if perMin is not None and perMin.strip() != '':
                    try:
                        numbers.append(float(perMin))
                    except ValueError:
                        pass  # TODO: accept text per minute
        # TODO: metronome-relation -- specifies how to relate multiple beat units
        # metronomeRelations = mxMetronome.find('metronome-relation')
        if len(durations) > 1:  # Metric Modulation!
            mm = tempo.MetricModulation()
            # environLocal.printDebug(['found metric modulation:', 'durations', durations])
            if len(durations) < 2:
                raise MusicXMLImportException(
                    'found incompletely specified musicxml metric modulation: '
                    + 'fewer than two durations defined')
            # all we have are referents, no values are defined in musicxml
            # will need to update context after adding to Stream
            mm.oldReferent = durations[0]
            mm.newReferent = durations[1]
        else:
            # environLocal.printDebug(['found metronome mark:', 'numbers', numbers])
            mm = tempo.MetronomeMark()
            if numbers:
                mm.number = numbers[0]
            if durations:
                mm.referent = durations[0]
            # TODO: set text if defined in words
            if mxWords is not None:
                pass

        paren = mxMetronome.get('parentheses')
        if paren is not None:
            if paren == 'yes':
                mm.parentheses = True

        _synchronizeIds(mxMetronome, mm)
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

        Returns a float, not fraction.

        >>> MP.divisions = 30
        >>> off = EL(r'<direction><offset>10</offset></direction>')
        >>> MP.xmlToOffset(off)
        0.33333...

        '''

        try:
            offset = float(mxObj.find('offset').text.strip())
        except (ValueError, AttributeError):
            return 0.0
        return offset / self.divisions

    def parseMeasureAttributes(self):
        '''
        parses the attributes of the <measure> tag.  Not the
        <attributes> tag inside the measure tag.

        calls parseMeasureNumbers(), and gets the width from the width tag.

        # TODO: implicit
        # TODO: non-controlling
        # may need to do a format/unit conversion?
        '''
        self.parseMeasureNumbers()
        width = self.mxMeasure.get('width')
        if width is not None:
            width = _floatOrIntStr(width)
            self.stream.layoutWidth = width

    def parseAttributesTag(self, mxAttributes):
        '''
        Parses a single attributes tag (mxAttributes) and sets

        self.attributesAreInternal to False,
        self.activeAttributes to mxAttributes,
        self.parent.activeAttributes to mxAttributes
        and then runs the appropriate attributeTagsToMethods for
        the attribute.

        Also sets self.divisions for the current divisions
        (along with self.parent.lastDivisions)
        and self.transposition and
        to the current transpose.
        '''
        self.attributesAreInternal = False
        self.activeAttributes = mxAttributes
        for mxSub in mxAttributes:
            tag = mxSub.tag
            meth = None
            # key, clef, time, details
            if tag in self.attributeTagsToMethods:
                meth = getattr(self, self.attributeTagsToMethods[tag])

            if meth is not None:
                meth(mxSub)
            elif tag == 'staves':
                self.staves = int(mxSub.text)
            elif tag == 'divisions':
                self.divisions = common.opFrac(float(mxSub.text))
            elif tag == 'transpose':
                self.transposition = self.xmlTransposeToInterval(mxSub)
                # environLocal.warn('Got a transposition of ', str(self.transposition) )

        if self.parent is not None:
            self.parent.lastDivisions = self.divisions
            self.parent.activeAttributes = self.activeAttributes

    def xmlTransposeToInterval(self, mxTranspose):
        # noinspection PyShadowingNames
        '''
        Convert a MusicXML Transpose object to a music21 Interval object.

        >>> import xml.etree.ElementTree as ET
        >>> MP = musicxml.xmlToM21.MeasureParser()

        >>> t = ET.fromstring('<transpose><diatonic>-1</diatonic>'
        ...                   + '<chromatic>-2</chromatic></transpose>')
        >>> MP.xmlTransposeToInterval(t)
        <music21.interval.Interval M-2>

        >>> t = ET.fromstring('<transpose><diatonic>-5</diatonic>'
        ...                   + '<chromatic>-9</chromatic></transpose>')
        >>> MP.xmlTransposeToInterval(t)
        <music21.interval.Interval M-6>


        Not mentioned in MusicXML XSD but supported in (Finale; MuseScore): octave-change
        refers to both diatonic and chromatic, so we will deal...

        >>> t = ET.fromstring('<transpose id="x"><diatonic>-1</diatonic><chromatic>-2</chromatic>'
        ...         + '<octave-change>-1</octave-change></transpose>')
        >>> inv = MP.xmlTransposeToInterval(t)
        >>> inv
        <music21.interval.Interval M-9>
        >>> inv.id
        'x'
        '''
        diatonicStep = None

        mxDiatonic = mxTranspose.find('diatonic')
        if mxDiatonic is not None:
            diatonicStep = int(mxDiatonic.text)

        chromaticStep = None
        mxChromatic = mxTranspose.find('chromatic')
        if mxChromatic is not None:
            chromaticStep = int(mxChromatic.text)

        octaveChange = 0
        mxOctaveChange = mxTranspose.find('octave-change')
        if mxOctaveChange is not None:
            octaveChange = int(mxOctaveChange.text) * 12
            diatonicStep += 7 * int(mxOctaveChange.text)
        # TODO: presently not dealing with <double>
        # doubled one octave down from what is currently written
        # (as is the case for mixed cello / bass parts in orchestral literature)
        # environLocal.printDebug(['ds', diatonicStep, 'cs', chromaticStep, 'oc', oc])
        if diatonicStep and chromaticStep:
            # diatonic step can be used as a generic specifier here if
            # shifted 1 away from zero
            if diatonicStep < 0:
                diatonicActual = diatonicStep - 1
            else:
                diatonicActual = diatonicStep + 1

            try:
                post = interval.intervalFromGenericAndChromatic(diatonicActual,
                                                                chromaticStep + octaveChange)
            except interval.IntervalException:
                # some people might use -8 for diatonic for down a 9th, assuming
                # even if there is an octave change because schema is ambiguous.  So try again.
                if diatonicStep < 0:
                    diatonicActual = (diatonicStep - int(octaveChange * 7 / 12)) - 1
                else:
                    diatonicActual = (diatonicStep - int(octaveChange * 7 / 12)) + 1

                post = interval.intervalFromGenericAndChromatic(diatonicActual,
                                                                chromaticStep + octaveChange)

        elif chromaticStep is not None:
            post = interval.Interval(chromaticStep + octaveChange)
        elif diatonicStep is not None:
            post = interval.GenericInterval(diatonicStep)
        else:
            post = interval.Interval('P1')  # guaranteed to return an interval object.

        _synchronizeIds(mxTranspose, post)

        return post

    def handleTimeSignature(self, mxTime):
        '''
        Creates a TimeSignature using xmlToTimeSignature and inserts it into
        the stream if it is appropriate to do so (now always yes.)
        '''
        ts = self.xmlToTimeSignature(mxTime)
        if ts is not None:
            self.insertCoreAndRef(self.offsetMeasureNote, mxTime, ts)

    def xmlToTimeSignature(self, mxTime):
        # noinspection PyShadowingNames
        '''
        Returns a TimeSignature or SenzaMisuraTimeSignature (for senza-misura)
        from a <time> block.

        >>> import xml.etree.ElementTree as ET
        >>> MP = musicxml.xmlToM21.MeasureParser()

        >>> mxTime = ET.fromstring('<time><beats>3</beats><beat-type>8</beat-type></time>')
        >>> MP.xmlToTimeSignature(mxTime)
        <music21.meter.TimeSignature 3/8>

        >>> mxTime = ET.fromstring('<time symbol="common"><beats>4</beats>' +
        ...                                              '<beat-type>4</beat-type></time>')
        >>> MP.xmlToTimeSignature(mxTime).symbol
        'common'

        Multiple times:

        >>> mxTime = ET.fromstring('<time><beats>3</beats><beat-type>8</beat-type>' +
        ...                              '<beats>4</beats><beat-type>4</beat-type></time>')
        >>> MP.xmlToTimeSignature(mxTime)
        <music21.meter.TimeSignature 3/8+4/4>

        >>> mxTime = ET.fromstring('<time><beats>3+2</beats><beat-type>8</beat-type></time>')
        >>> ts32 = MP.xmlToTimeSignature(mxTime)
        >>> ts32
        <music21.meter.TimeSignature 3/8+2/8>

        Senza Misura

        >>> mxSenza = ET.fromstring('<time><senza-misura>0</senza-misura></time>')
        >>> MP.xmlToTimeSignature(mxSenza)
        <music21.meter.SenzaMisuraTimeSignature 0>


        Small Duration Time Signatures

        >>> mxTime = ET.fromstring('<time><beats>3</beats><beat-type>32</beat-type></time>')
        >>> MP.xmlToTimeSignature(mxTime)
        <music21.meter.TimeSignature 3/32>

        >>> mxTime = ET.fromstring('<time><beats>3</beats><beat-type>64</beat-type></time>')
        >>> MP.xmlToTimeSignature(mxTime)
        <music21.meter.TimeSignature 3/64>

        >>> mxTime = ET.fromstring('<time><beats>3</beats><beat-type>128</beat-type></time>')
        >>> MP.xmlToTimeSignature(mxTime)
        <music21.meter.TimeSignature 3/128>
        '''
        isSenzaMisura = mxTime.find('senza-misura')
        if isSenzaMisura is not None:
            return meter.SenzaMisuraTimeSignature(isSenzaMisura.text)

        numerators = []
        denominators = []
        for beatOrType in mxTime:
            if beatOrType.tag == 'beats':
                numerators.append(beatOrType.text.strip())  # may be 3+2
            elif beatOrType.tag == 'beat-type':
                denominators.append(beatOrType.text.strip())
            elif beatOrType.tag == 'interchangeable':
                break  # interchangeable comes after all beat/beat-type sequences

        # convert into a string
        msg = []
        for i in range(len(numerators)):
            msg.append(f'{numerators[i]}/{denominators[i]}')

        # environLocal.warn(['loading meter string:', '+'.join(msg)])
        if len(msg) == 1:  # normal
            try:
                ts = meter.TimeSignature(msg[0])
            except meter.MeterException:
                raise MusicXMLImportException(
                    f'Cannot process time signature {msg[0]}')
        else:
            ts = meter.TimeSignature()
            ts.load('+'.join(msg))
        # TODO: interchangeable

        self.setPrintStyleAlign(mxTime, ts)
        self.setPrintObject(mxTime, ts)

        # TODO: attr: separator

        # attr: symbol
        symbol = mxTime.get('symbol')
        if symbol:
            if symbol in ('common', 'cut', 'single-number', 'normal'):
                ts.symbol = symbol
            elif symbol == 'note':
                ts.symbolizeDenominator = True
            elif symbol == 'dotted-note':
                pass
                # TODO: support, but not as musicxml style -- reduces by 1/3 the numerator...
                # this should be done by changing the displaySequence directly.
        # TODO: attr: number (which staff... is this done?)

        return ts

    def handleClef(self, mxClef):
        # noinspection PyShadowingNames
        '''
        Handles a clef object, appending it to the core, and
        setting self.lastClefs for the staff number.

        >>> import xml.etree.ElementTree as ET
        >>> mxClef = ET.fromstring('<clef><sign>G</sign><line>2</line></clef>')

        >>> MP = musicxml.xmlToM21.MeasureParser()
        >>> MP.handleClef(mxClef)
        >>> MP.lastClefs
        {0: <music21.clef.TrebleClef>}

        >>> mxClefBC = ET.fromstring('<clef number="2"><sign>F</sign><line>4</line></clef>')
        >>> MP.handleClef(mxClefBC)
        >>> MP.lastClefs[2]
        <music21.clef.BassClef>
        >>> MP.lastClefs[0]
        <music21.clef.TrebleClef>
        '''
        clefObj = self.xmlToClef(mxClef)
        self.insertCoreAndRef(self.offsetMeasureNote, mxClef, clefObj)

        # Update the list of lastClefs -- needed for rest display.
        staffNumberStrOrNone = self.getStaffNumber(mxClef)
        self.lastClefs[staffNumberStrOrNone] = clefObj

    def xmlToClef(self, mxClef):
        # noinspection PyShadowingNames
        '''
        Returns a music21 Clef object from an mxClef element.

        >>> import xml.etree.ElementTree as ET
        >>> mxClef = ET.fromstring('<clef><sign>G</sign><line>2</line></clef>')

        >>> MP = musicxml.xmlToM21.MeasureParser()
        >>> MP.xmlToClef(mxClef)
        <music21.clef.TrebleClef>

        >>> mxClef = ET.fromstring('<clef><sign>G</sign><line>2</line>'
        ...                        + '<clef-octave-change>-1</clef-octave-change></clef>')
        >>> MP.xmlToClef(mxClef)
        <music21.clef.Treble8vbClef>

        >>> mxClef = ET.fromstring('<clef><sign>TAB</sign></clef>')
        >>> MP.xmlToClef(mxClef)
        <music21.clef.TabClef>
        '''
        sign = mxClef.find('sign').text.strip()
        if sign.lower() in ('tab', 'percussion', 'none', 'jianpu'):
            clefObj = clef.clefFromString(sign)
        else:
            mxLine = mxClef.find('line')
            if mxLine is not None:
                line = mxLine.text.strip()
            elif sign == 'G':
                line = '2'
            else:
                line = '4'
            mxOctaveChange = mxClef.find('clef-octave-change')
            if mxOctaveChange is not None:
                try:
                    octaveChange = int(mxOctaveChange.text)
                except ValueError:
                    octaveChange = 0
            else:
                octaveChange = 0
            clefObj = clef.clefFromString(sign + line, octaveChange)

        # number is taken care of by insertCoreAndReference

        # TODO: additional -- is this clef an additional clef to ignore...
        # TODO: size
        # TODO: after-barline -- particular style to clef.
        self.setPrintStyle(mxClef, clefObj)
        self.setPrintObject(mxClef, clefObj)

        return clefObj

    def handleKeySignature(self, mxKey):
        '''
        convert mxKey to a Key or KeySignature and run insertCoreAndRef on it
        '''
        keySig = self.xmlToKeySignature(mxKey)
        self.insertCoreAndRef(self.offsetMeasureNote, mxKey, keySig)

    def xmlToKeySignature(self, mxKey):
        # noinspection PyShadowingNames
        '''
        Returns either a KeySignature (traditional or non-traditional)
        or a Key object based on whether fifths and mode is present.

        >>> import xml.etree.ElementTree as ET
        >>> mxKey = ET.fromstring('<key><fifths>-4</fifths></key>')

        >>> MP = musicxml.xmlToM21.MeasureParser()
        >>> MP.xmlToKeySignature(mxKey)
        <music21.key.KeySignature of 4 flats>


        >>> mxKey = ET.fromstring('<key><fifths>-4</fifths><mode>minor</mode></key>')

        >>> MP = musicxml.xmlToM21.MeasureParser()
        >>> MP.xmlToKeySignature(mxKey)
        <music21.key.Key of f minor>


        Invalid modes get ignored and returned as KeySignatures

        >>> mxKey = ET.fromstring('<key><fifths>-4</fifths><mode>crazy</mode></key>')

        >>> MP = musicxml.xmlToM21.MeasureParser()
        >>> MP.xmlToKeySignature(mxKey)
        <music21.key.KeySignature of 4 flats>
        '''

        # TODO: cancel
        if mxKey.find('fifths') is None:
            ks = self.nonTraditionalKeySignature(mxKey)
        else:
            ks = key.KeySignature()
            seta = _setAttributeFromTagText
            seta(ks, mxKey, 'fifths', 'sharps', transform=int)

            mxKeyMode = mxKey.find('mode')
            if mxKeyMode is not None:
                modeValue = mxKeyMode.text
                if modeValue not in (None, ''):
                    try:
                        ks = ks.asKey(modeValue)
                    except exceptions21.Music21Exception:
                        pass  # mxKeyMode might not be a valid mode -- in which case ignore...
        self.mxKeyOctaves(mxKey, ks)
        # TODO: attr: number
        self.setPrintStyle(mxKey, ks)
        self.setPrintObject(mxKey, ks)

        return ks

    def mxKeyOctaves(self, mxKey, ks):
        # noinspection PyShadowingNames
        '''
        process the <key-octave> tags to potentially change a key signature
        to a non-standard key signature.

        >>> import xml.etree.ElementTree as ET
        >>> mxKey = ET.fromstring('<key><fifths>-4</fifths>'
        ...   + '<key-octave number="1">3</key-octave>'
        ...   + '<key-octave number="2">4</key-octave>'
        ...   + '<key-octave number="4">3</key-octave>'
        ...   + '</key>')

        >>> ks = key.KeySignature(-4)
        >>> MP = musicxml.xmlToM21.MeasureParser()
        >>> MP.mxKeyOctaves(mxKey, ks)
        >>> ks.alteredPitches
        [<music21.pitch.Pitch B-3>,
         <music21.pitch.Pitch E-4>,
         <music21.pitch.Pitch A->,
         <music21.pitch.Pitch D-3>]
        '''
        # key-octave
        keyOctaves = mxKey.findall('key-octave')
        if not keyOctaves:
            return

        alteredPitches = copy.deepcopy(ks.alteredPitches)

        for mxKeyOctave in keyOctaves:
            cancel = mxKeyOctave.get('cancel')
            # TODO: cancel
            if cancel == 'yes':
                continue
            pitchIndex = mxKeyOctave.get('number')
            try:
                alteredPitch = alteredPitches[int(pitchIndex) - 1]
            except (IndexError, ValueError):
                continue
            octaveToSet = int(mxKeyOctave.text)
            alteredPitch.octave = octaveToSet

        ks.alteredPitches = alteredPitches

    def nonTraditionalKeySignature(self, mxKey):
        # noinspection PyShadowingNames
        '''
        Returns a KeySignature object that represents a nonTraditional Key Signature

        called by xmlToKeySignature if <fifths> is not present.

        >>> import xml.etree.ElementTree as ET
        >>> MP = musicxml.xmlToM21.MeasureParser()

        >>> mxKey = ET.fromstring('<key><key-step>E</key-step><key-alter>-1</key-alter></key>')
        >>> MP.nonTraditionalKeySignature(mxKey)
        <music21.key.KeySignature of pitches: [E-]>

        Should be the same:

        >>> MP.xmlToKeySignature(mxKey)
        <music21.key.KeySignature of pitches: [E-]>


        Works with key-accidental also:

        >>> mxKey = ET.fromstring('<key><key-step>G</key-step><key-alter>1</key-alter>'
        ...                       + '<key-accidental>sharp</key-accidental></key>')
        >>> MP.nonTraditionalKeySignature(mxKey)
        <music21.key.KeySignature of pitches: [G#]>
        '''
        allChildren = list(mxKey)

        lastTag = None
        allSteps = []
        allAlters = []
        allAccidentals = []

        for c in allChildren:
            tag = c.tag
            if lastTag == 'key-alter' and tag == 'key-step':
                allAccidentals.append(None)

            if tag == 'key-step':
                allSteps.append(c.text)
            elif tag == 'key-alter':
                allAlters.append(float(c.text))
            elif tag == 'key-accidental':
                allAccidentals.append(c.text)
            lastTag = tag

        if len(allAccidentals) < len(allAlters):
            allAccidentals.append(None)
        if len(allSteps) != len(allAlters):
            raise MusicXMLImportException(
                'For non traditional signatures each step must have an alter')

        ks = key.KeySignature()

        alteredPitches = []
        for i in range(len(allSteps)):
            thisStep = allSteps[i]
            thisAlter = allAlters[i]
            thisAccidental = allAccidentals[i]
            p = pitch.Pitch(thisStep)
            if thisAccidental is not None:
                if thisAccidental in self.mxAccidentalNameToM21:
                    accidentalName = self.mxAccidentalNameToM21[thisAccidental]
                else:
                    accidentalName = thisAccidental
                p.accidental = pitch.Accidental(accidentalName)
                p.accidental.alter = thisAlter
            else:
                p.accidental = pitch.Accidental(thisAlter)

            alteredPitches.append(p)

        ks.alteredPitches = alteredPitches
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
        # staffNumber refers to the staff number for this Part -- i.e., usually None or 1
        # except for a piano score, etc.
        # ET.dump(mxDetails)

        staffNumber = mxDetails.get('number')
        if staffNumber is not None:
            staffNumber = int(staffNumber)
        else:
            staffNumber = 1

        layoutObjectKey = (staffNumber, self.offsetMeasureNote)
        existingStaffLayoutObject = self.staffLayoutObjects.get(layoutObjectKey, None)
        newStaffLayoutObject = self.xmlStaffLayoutFromStaffDetails(
            mxDetails,
            m21staffLayout=existingStaffLayoutObject
        )
        if existingStaffLayoutObject is None:
            self.insertCoreAndRef(self.offsetMeasureNote, mxDetails, newStaffLayoutObject)
            self.staffLayoutObjects[layoutObjectKey] = newStaffLayoutObject


    def xmlStaffLayoutFromStaffDetails(
        self,
        mxDetails,
        m21staffLayout: Optional[layout.StaffLayout] = None
    ) -> Optional[layout.StaffLayout]:
        # noinspection PyShadowingNames
        '''
        Returns a new StaffLayout object from staff-details or sets attributes on an existing one

        >>> from xml.etree.ElementTree import fromstring as EL
        >>> MP = musicxml.xmlToM21.MeasureParser()
        >>> mxDetails = EL('<details number="2" print-object="no">'
        ...                + '<staff-size>21.2</staff-size><staff-lines>4</staff-lines>'
        ...                + '</details>')
        >>> stl = MP.xmlStaffLayoutFromStaffDetails(mxDetails)
        >>> stl.staffSize
        21.2
        >>> stl.staffLines
        4
        >>> stl.staffNumber
        2
        >>> stl.hidden
        True

        `staffType` defaults to Regular:

        >>> stl.staffType
        <StaffType.REGULAR: 'regular'>
        >>> mxDetails2 = EL(r'<details number="2"><staff-type>cue</staff-type></details>')
        >>> MP.xmlStaffLayoutFromStaffDetails(mxDetails2, m21staffLayout=stl)
        >>> stl.staffType
        <StaffType.CUE: 'cue'>
        '''
        seta = _setAttributeFromTagText
        stl: layout.StaffLayout
        if not m21staffLayout:
            stl = layout.StaffLayout()
        else:
            stl = m21staffLayout
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

        mxStaffType = mxDetails.find('staff-type')
        if mxStaffType is not None:
            try:
                xmlText: str = mxStaffType.text.strip()
                # inspection bug: https://youtrack.jetbrains.com/issue/PY-42287
                # remove "no inspection..." when issue is closed
                # noinspection PyArgumentList
                stl.staffType = stream.enums.StaffType(xmlText)
            except ValueError:
                environLocal.warn(f'Got an incorrect staff-type in details: {mxStaffType}')
        # TODO: staff-tuning*
        # TODO: capo
        # TODO: show-frets
        # TODO: print-spacing
        if not m21staffLayout:
            return stl

    def handleMeasureStyle(self, mxMeasureStyle):
        '''
        measure + multi-measure repeats, slashed repeats, etc.

        But currently only multiMeasure rests are supported.

        Each of these applies to the entire measure, so there's
        no need to insert into the stream.

        Does not support multiple staves yet.
        '''
        # TODO: attr: number (staff number)
        # TODO: attr-group color
        # TODO: beat-repeat
        # TODO: measure-repeat
        mxMultiRest = mxMeasureStyle.find('multiple-rest')
        if mxMultiRest is not None and self.parent is not None:
            self.parent.multiMeasureRestsToCapture = int(mxMultiRest.text)
            mmrSpanner = spanner.MultiMeasureRest()
            useSymbols = mxMultiRest.get('use-symbols')
            if useSymbols == 'yes':
                mmrSpanner.useSymbols = True
            else:  # musicxml default is False
                mmrSpanner.useSymbols = False
            self.parent.activeMultiMeasureRestSpanner = mmrSpanner

            self.setFont(mxMultiRest, mmrSpanner)

        # TODO: slash

    def parseMeasureNumbers(self, mNumRaw=None):
        '''
        Gets the measure number from the 'number' attribute of the
        <measure> tag.  (Or, for testing, from the mNumRaw
        argument).  Sets MeasureParser.stream.number and possibly
        MeasureParser.stream.numberSuffix

        >>> MP = musicxml.xmlToM21.MeasureParser()
        >>> MP.parseMeasureNumbers('5')
        >>> MP.stream.number
        5

        Sets not only stream.number, but also MeasureParser.measureNumber and
        MeasureParser.numberSuffix

        >>> MP.parseMeasureNumbers('44b')
        >>> MP.stream.number
        44
        >>> MP.stream.numberSuffix
        'b'
        >>> MP.measureNumber
        44
        >>> MP.numberSuffix
        'b'

        >>> MP.parseMeasureNumbers('X1')
        >>> MP.stream.number
        1
        >>> MP.stream.numberSuffix
        'X'
        '''
        if mNumRaw is None and self.mxMeasure is not None:
            # this is the default situation
            mNumRaw = self.mxMeasure.get('number')

        m = self.stream
        if self.parent:
            lastMNum = self.parent.lastMeasureNumber
            lastMSuffix = self.parent.lastNumberSuffix
        else:
            lastMNum = None
            lastMSuffix = ''

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
        # noinspection PyShadowingNames
        '''
        Finds all the "voice" information in <note> tags and updates the set of
        `.voiceIndices` to be a set of all the voice texts, and if there is
        more than one voice in the measure, sets `.useVoices` to True
        and creates a voice for each.

        >>> import xml.etree.ElementTree as ET
        >>> MP = musicxml.xmlToM21.MeasureParser()
        >>> MP.mxMeasure = ET.fromstring('<measure><note><voice>1</voice></note></measure>')
        >>> MP.updateVoiceInformation()

        Puts a set object in `.voiceIndices`

        >>> MP.voiceIndices
        {'1'}
        >>> MP.useVoices
        False

        >>> MP = musicxml.xmlToM21.MeasureParser()
        >>> MP.mxMeasure = ET.fromstring('<measure><note><voice>1</voice></note>'
        ...                                     + '<note><voice>2</voice></note></measure>')
        >>> MP.updateVoiceInformation()
        >>> sorted(list(MP.voiceIndices))
        ['1', '2']
        >>> MP.useVoices
        True
        >>> len(MP.stream)
        2
        >>> len(MP.stream.getElementsByClass('Voice'))
        2
        '''
        mxm = self.mxMeasure
        for mxn in mxm.findall('note'):
            voice = mxn.find('voice')
            if textStripValid(voice):
                vIndex = voice.text.strip()
                self.voiceIndices.add(vIndex)
                # it is a set, so no need to check if already there
                # additional time < 1 sec per ten million ops.

        if len(self.voiceIndices) > 1:
            for vIndex in sorted(self.voiceIndices):
                v = stream.Voice()
                v.id = vIndex  # TODO: should use a separate voiceId or something in Voice.
                self.stream.coreInsert(0.0, v)
                self.voicesById[v.id] = v
            self.useVoices = True

            self.stream.coreElementsChanged()

# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------


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
        out = '['
        for p in listIn:
            out += str(p) + ', '
        out = out[0:len(out) - 2]
        out += ']'
        return out

    def testExceptionMessage(self):
        mxScorePart = self.EL('<score-part><part-name>Elec.</part-name></score-part>')
        mxPart = self.EL('<part><measure><note><type>thirty-tooth</type></note></measure></part>')

        PP = PartParser(mxPart=mxPart, mxScorePart=mxScorePart)
        PP.partId = '1'

        msg = 'In part (Elec.), measure (0): found unknown MusicXML type: thirty-tooth'
        with self.assertRaises(MusicXMLImportException) as error:
            PP.parse()
        self.assertEqual(str(error.exception), msg)

    def testBarRepeatConversion(self):
        from music21 import corpus
        # a = converter.parse(testPrimitive.simpleRepeat45a)
        # this is a good example with repeats
        s = corpus.parse('k80/movement3')
        for p in s.parts:
            post = p.flat.getElementsByClass('Repeat')
            self.assertEqual(len(post), 6)

        # a = corpus.parse('opus41no1/movement3')
        # s.show()

    def testVoices(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.voiceDouble)
        m1 = s.parts[0].getElementsByClass('Measure')[0]
        self.assertTrue(m1.hasVoices())

        self.assertEqual([v.id for v in m1.voices], ['1', '2'])

        self.assertEqual([e.offset for e in m1.voices[0]], [0.0, 1.0, 2.0, 3.0])
        self.assertEqual([e.offset for e in m1.voices['1']], [0.0, 1.0, 2.0, 3.0])

        self.assertEqual([e.offset for e in m1.voices[1]], [0.0, 2.0, 2.5, 3.0, 3.5])
        self.assertEqual([e.offset for e in m1.voices['2']], [0.0, 2.0, 2.5, 3.0, 3.5])
        # s.show()

    def testSlurInputA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.spannersSlurs33c)
        # have 5 spanners
        self.assertEqual(len(s.flat.getElementsByClass('Spanner')), 5)

        # can get the same from a recurse search
        self.assertEqual(len(s.recurse().getElementsByClass('Spanner')), 5)

        # s.show('t')
        # s.show()

    def testMultipleStavesPerPartA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.pianoStaff43a)
        self.assertEqual(len(s.parts), 2)
        # s.show()
        self.assertEqual(len(s.parts[0].flat.getElementsByClass('Note')), 1)
        self.assertEqual(len(s.parts[1].flat.getElementsByClass('Note')), 1)

        self.assertIsInstance(s.parts[0], stream.PartStaff)
        self.assertIsInstance(s.parts[1], stream.PartStaff)

    def testMultipleStavesPerPartB(self):
        from music21 import converter
        from music21.musicxml import testFiles

        s = converter.parse(testFiles.moussorgskyPromenade)  # @UndefinedVariable
        self.assertEqual(len(s.parts), 2)

        self.assertEqual(len(s.parts[0].flat.getElementsByClass('Note')), 19)
        # only chords in the second part
        self.assertEqual(len(s.parts[1].flat.getElementsByClass('Note')), 0)

        self.assertEqual(len(s.parts[0].flat.getElementsByClass('Chord')), 11)
        self.assertEqual(len(s.parts[1].flat.getElementsByClass('Chord')), 11)

        # s.show()

    def testMultipleStavesPerPartC(self):
        from music21 import corpus
        s = corpus.parse('schoenberg/opus19/movement2')
        self.assertEqual(len(s.parts), 2)

        s = corpus.parse('schoenberg/opus19/movement6')
        self.assertEqual(len(s.parts), 2)

        # s.show()

    def testSpannersA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.spanners33a)
        # this number will change as more are being imported
        self.assertGreaterEqual(len(s.flat.spanners), 2)

        # environLocal.printDebug(['pre s.measures(2,3)', 's', s])
        ex = s.measures(2, 3)  # this needs to get all spanners too

        # all spanners are referenced over; even ones that may not be relevant
        self.assertEqual(len(ex.flat.spanners), 15)
        # ex.show()

        # slurs are on measures 2, 3
        # crescendos are on measures 4, 5
        # wavy lines on measures 6, 7
        # brackets etc. on measures 10-14
        # glissando on measure 16
        # slide on measure 18 (= music21 Glissando)

    def testTextExpressionsA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.textExpressions)
        # s.show()
        self.assertEqual(len(s.flat.getElementsByClass('TextExpression')), 3)

        p1 = s.parts[0]
        m1 = p1.getElementsByClass('Measure')[0]
        self.assertEqual(len(m1.getElementsByClass('TextExpression')), 0)
        # all in measure 2
        m2 = p1.getElementsByClass('Measure')[1]
        self.assertEqual(len(m2.getElementsByClass('TextExpression')), 3)

        teStream = m2.getElementsByClass('TextExpression')
        self.assertEqual([te.offset for te in teStream], [1.0, 1.5, 4.0])

        # s.show()

    def testTextExpressionsC(self):
        from music21 import corpus
        s = corpus.parse('bwv66.6')
        p = s.parts[0]
        for m in p.getElementsByClass('Measure'):
            for n in m.flat.notes:
                if n.pitch.name in ['B']:
                    msg = f'{n.pitch.nameWithOctave}\n{n.duration.quarterLength}'
                    te = expressions.TextExpression(msg)
                    te.style.fontSize = 14
                    te.style.fontWeight = 'bold'
                    te.style.justify = 'center'
                    te.style.enclosure = 'rectangle'
                    te.style.absoluteY = -80
                    m.insert(n.offset, te)
        # p.show()

    def testTextExpressionsD(self):
        from music21 import corpus
        # test placing text expression in arbitrary locations
        s = corpus.parse('bwv66.6')
        p = s.parts[-1]  # get bass
        for m in p.getElementsByClass('Measure')[1:]:
            for pos in [1.5, 2.5]:
                te = expressions.TextExpression(pos)
                te.style.fontWeight = 'bold'
                te.style.justify = 'center'
                te.style.enclosure = 'rectangle'
                m.insert(pos, te)
        # p.show()

    def testTextExpressionsE(self):
        import random
        s = stream.Stream()
        for i in range(6):
            m = stream.Measure(number=i + 1)
            m.append(layout.SystemLayout(isNew=True))
            m.append(note.Rest(type='whole'))
            s.append(m)
        for m in s.getElementsByClass('Measure'):
            offsets = [x * 0.25 for x in range(16)]
            random.shuffle(offsets)
            offsets = offsets[:4]
            for o in offsets:
                te = expressions.TextExpression(o)
                te.style.fontWeight = 'bold'
                te.style.justify = 'center'
                te.style.enclosure = 'rectangle'
                m.insert(o, te)
        # s.show()

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
        # has repeats in it; start with single measure
        s = corpus.parse('opus74no1', 3)
        # there are 2 for each part, totaling 8
        self.assertEqual(len(s.flat.getElementsByClass('RepeatBracket')), 8)
        # can get for each part as spanners are stored in Part now

        # TODO: need to test getting repeat brackets after measure extraction
        # s.parts[0].show()  # 72 through 77
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
        # s.show('text')
        self.assertEqual(len(s.parts), 2)
        # there are voices, but they have been removed
        self.assertEqual(len(s.parts[0].getElementsByClass(
            'Measure')[0].voices), 0)

        # s.parts[0].show('t')
        # self.assertEqual(len(s.parts[0].voices), 2)
        s = converter.parse(testPrimitive.mixedVoices1b)
        self.assertEqual(len(s.parts), 2)
        self.assertEqual(len(s.parts[0].getElementsByClass(
            'Measure')[0].voices), 0)
        # s.parts[0].show('t')

        # this case, there were 4, but there should be 2
        s = converter.parse(testPrimitive.mixedVoices2)
        self.assertEqual(len(s.parts), 2)
        self.assertEqual(len(s.parts[0].getElementsByClass(
            'Measure')[0].voices), 2)
        self.assertEqual(len(s.parts[1].getElementsByClass(
            'Measure')[0].voices), 2)

        # s.parts[0].show('t')

#         s = converter.parse(testPrimitive.mixedVoices1b)
#         s = converter.parse(testPrimitive.mixedVoices2)

    #         s = converter.parse(testPrimitive.mixedVoices1b)
    #         s = converter.parse(testPrimitive.mixedVoices2)

    def testImportMetronomeMarksA(self):
        from music21.musicxml import testPrimitive
        from music21 import converter
        # has metronome marks defined, not with sound tag
        s = converter.parse(testPrimitive.metronomeMarks31c)
        # get all tempo indications
        mms = s.flat.getElementsByClass('TempoIndication')
        self.assertGreater(len(mms), 3)

    def testImportMetronomeMarksB(self):
        pass
        # TODO: look for files that only have sound tags and create MetronomeMarks
        # need to look for bundling of Words text expressions with tempo

        # has only sound tempo=x tag
        # s = converter.parse(testPrimitive.articulations01)
        # s.show()

    def testImportGraceNotesA(self):
        # test importing from musicxml
        from music21.musicxml import testPrimitive
        from music21 import converter
        unused_s = converter.parse(testPrimitive.graceNotes24a)

        # s.show()

    def testChordalStemDirImport(self):
        # NB: Finale apparently will not display a pitch that is a member of a chord without a stem
        # unless all chord members are without stems.
        # MuseScore 2.0.3 -- last <stem> tag rules.
        from music21.musicxml import m21ToXml
        from music21 import converter

        # this also tests the EXPORTING of stem directions on notes within chords...
        n1 = note.Note('f3')
        n1.notehead = 'diamond'
        n1.stemDirection = 'down'
        n2 = note.Note('c4')
        n2.stemDirection = 'noStem'
        c = chord.Chord([n1, n2])
        c.quarterLength = 2

        GEX = m21ToXml.GeneralObjectExporter()
        xml = GEX.parse(c).decode('utf-8')
        # print(xml.decode('utf-8'))
        # c.show()
        inputStream = converter.parse(xml)
        chordResult = inputStream.flat.notes[0]
        #         for n in chordResult:
        #             print(n.stemDirection)

        self.assertEqual(chordResult.getStemDirection(chordResult.pitches[0]), 'down')
        self.assertEqual(chordResult.getStemDirection(chordResult.pitches[1]), 'noStem')

    def testStaffGroupsA(self):
        from music21.musicxml import testPrimitive
        from music21 import converter

        s = converter.parse(testPrimitive.staffGroupsNested41d)
        staffGroups = s.getElementsByClass('StaffGroup')
        # staffGroups.show()
        self.assertEqual(len(staffGroups), 2)

        sg1 = staffGroups[0]
        self.assertEqual(sg1.symbol, 'line')
        self.assertTrue(sg1.barTogether)

        sg2 = staffGroups[1]  # Order is right here, was wrong in fromMxObjects
        self.assertEqual(sg2.symbol, 'brace')
        self.assertTrue(sg2.barTogether)

        # TODO: more tests about which parts are there...

    def testStaffGroupsPiano(self):
        from music21.musicxml import testPrimitive
        from music21 import converter

        s = converter.parse(testPrimitive.pianoStaff43a)
        sgs = s.getElementsByClass('StaffGroup')
        self.assertEqual(len(sgs), 1)
        self.assertEqual(sgs[0].symbol, 'brace')
        self.assertIs(sgs[0].barTogether, True)
        self.assertIs(sgs[0].style.hideObjectOnPrint, True)

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

        iStream1 = s.parts[0].flat.getElementsByClass('Instrument').stream()
        # three instruments; one initial, and then one for each transposition
        self.assertEqual(len(iStream1), 3)
        # should be 3
        iStream2 = s.parts[1].flat.getElementsByClass('Instrument').stream()
        self.assertEqual(len(iStream2), 3)
        # i2 = iStream2[0]

        iStream3 = s.parts[2].flat.getElementsByClass('Instrument').stream()
        self.assertEqual(len(iStream3), 1)
        i3 = iStream3[0]

        self.assertEqual(str(iStream1[0].transposition), 'None')
        self.assertEqual(str(iStream1[1].transposition), '<music21.interval.Interval P-5>')
        self.assertEqual(str(iStream1[2].transposition), '<music21.interval.Interval P1>')

        self.assertEqual(str(iStream2[0].transposition), '<music21.interval.Interval M-2>')
        self.assertEqual(str(iStream2[1].transposition), '<music21.interval.Interval m3>')

        self.assertEqual(str(i3.transposition), '<music21.interval.Interval P-5>')

        self.assertEqual(self.pitchOut(s.parts[0].flat.pitches),
                         '[A4, A4, A4, A4, A4, A4, A4, A4, '
                         + 'E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, '
                         + 'A4, A4, A4, A4]')
        self.assertEqual(self.pitchOut(s.parts[1].flat.pitches),
                         '[B4, B4, B4, B4, '
                         + 'F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, '
                         + 'F#4, F#4, F#4, F#4, F#4, B4, B4, B4, B4, B4, B4]')
        self.assertEqual(self.pitchOut(s.parts[2].flat.pitches),
                         '[E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, '
                         + 'E5, E5, E5, E5, E5, E5, E5, E5]')

        self.assertFalse(s.parts[0].flat.atSoundingPitch)

        sSounding = s.toSoundingPitch(inPlace=False)

        # all A4s
        self.assertEqual({p.nameWithOctave for p in sSounding.parts[0].flat.pitches},
                         {'A4'})
        self.assertEqual({p.nameWithOctave for p in sSounding.parts[1].flat.pitches},
                         {'A4'})
        self.assertEqual({p.nameWithOctave for p in sSounding.parts[2].flat.pitches},
                         {'A4'})

        # chordification by default places notes at sounding pitch
        sChords = s.chordify()
        self.assertEqual({p.nameWithOctave for p in sChords.flat.pitches},
                         {'A4'})
        # sChords.show()

    def testInstrumentTranspositionC(self):
        # generate all transpositions on output
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.transposing01)
        instStream = s.flat.getElementsByClass('Instrument')
        # for i in instStream:
        #    print(i.offset, i, i.transposition)
        self.assertEqual(len(instStream), 7)
        # s.show()

    def testHarmonyA(self):
        from music21 import corpus

        s = corpus.parse('leadSheet/berlinAlexandersRagtime.xml')
        self.assertEqual(len(s.flat.getElementsByClass('ChordSymbol')), 19)

        match = [h.chordKind for h in s.flat.getElementsByClass('ChordSymbol')]
        self.assertEqual(match, ['major', 'dominant-seventh', 'major', 'major', 'major',
                                 'major', 'dominant-seventh', 'major', 'dominant-seventh',
                                 'major', 'dominant-seventh', 'major', 'dominant-seventh',
                                 'major', 'dominant-seventh', 'major', 'dominant-seventh',
                                 'major', 'major'])

        match = [str(h.root()) for h in s.flat.getElementsByClass('ChordSymbol')]

        self.assertEqual(match, ['F3', 'C3', 'F3', 'B-2', 'F3', 'C3', 'G2', 'C3', 'C3',
                                 'F3', 'C3', 'F3', 'F2', 'B-2', 'F2', 'F3', 'C3', 'F3', 'C3'])

        match = {str(h.figure) for h in s.flat.getElementsByClass('ChordSymbol')}

        self.assertEqual(match, {'F', 'F7', 'B-', 'C7', 'G7', 'C'})

        s = corpus.parse('monteverdi/madrigal.3.12.xml')
        self.assertEqual(len(s.flat.getElementsByClass('ChordSymbol')), 10)

        s = corpus.parse('leadSheet/fosterBrownHair.xml')
        self.assertEqual(len(s.flat.getElementsByClass('ChordSymbol')), 40)

        # s.show()

    def x_testOrnamentAndTechnical(self):
        from music21 import converter
        beethoven = common.getCorpusFilePath() + '/beethoven/opus133.mxl'
        # TODO: this is way too long... lots of hidden 32nd notes for trills...
        s = converter.parse(beethoven, format='musicxml')
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

        # s.flat.show('t')
        num_tremolo_spanners = len(s.flat.getElementsByClass('TremoloSpanner'))
        self.assertEqual(num_tremolo_spanners, 0)  # no spanned tremolos

        count = 0
        for n in s.flat.notes:
            for e in n.expressions:
                if 'Tremolo' in e.classes:
                    count += 1
        self.assertEqual(count, 1)  # One single Tremolo

        count = 0
        for n in s.flat.notes:
            for e in n.expressions:
                if 'Turn' in e.classes:
                    count += 1
        self.assertEqual(count, 4)  # include inverted turn

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
        self.assertEqual(msg, ['This is a text box!', 'pos 200/300 (lower left)',
                               'pos 1000/300 (lower right)', 'pos 200/1500 (upper left)',
                               'pos 1000/1500 (upper right)'])

    def testImportSlursA(self):
        from music21 import corpus
        # this is a good test as this encoding uses staffs, not parts
        # to encode both parts; this requires special spanner handling
        s = corpus.parse('mozart/k545/movement1_exposition')
        sf = s.flat
        slurs = sf.getElementsByClass(spanner.Slur)
        self.assertEqual(len(slurs), 2)

        n1, n2 = s.parts[0].flat.notes[3], s.parts[0].flat.notes[5]
        # environLocal.printDebug(['n1', n1, 'id(n1)', id(n1),
        #     slurs[0].getSpannedElementIds(), slurs[0].getSpannedElementIds()])
        self.assertEqual(id(n1), slurs[0].getSpannedElementIds()[0])
        self.assertEqual(id(n2), slurs[0].getSpannedElementIds()[1])

        # environLocal.printDebug(['n2', n2, 'id(n2)', id(n2), slurs[0].getSpannedElementIds()])

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
        # s.show()
        self.assertEqual(len(s.flat.getElementsByClass('Line')), 6)

    def testTrillExtensionImportA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive
        s = converter.parse(testPrimitive.notations32a)
        # s.show()
        self.assertEqual(len(s.flat.getElementsByClass('TrillExtension')), 2)

    def testGlissandoImportA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive
        s = converter.parse(testPrimitive.spanners33a)
        # s.show()
        glisses = list(s.recurse().getElementsByClass('Glissando'))
        self.assertEqual(len(glisses), 2)
        self.assertEqual(glisses[0].slideType, 'chromatic')
        self.assertEqual(glisses[1].slideType, 'continuous')

    def testImportDashes(self):
        # dashes are imported as Lines (as are brackets)
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.spanners33a, format='musicxml')
        self.assertEqual(len(s.recurse().getElementsByClass('Line')), 6)

    def testImportGraceA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.graceNotes24a)
        # s.show()
        match = [str(p) for p in s.pitches]
        # print(match)
        self.assertEqual(match, ['D5', 'C5', 'E5', 'D5', 'C5', 'D5', 'C5', 'D5',
                                 'C5', 'D5', 'C5', 'E5', 'D5', 'C5', 'D5', 'C5',
                                 'D5', 'C5', 'E5', 'E5', 'F4', 'C5', 'D#5', 'C5',
                                 'D-5', 'A-4', 'C5', 'C5'])

    def testBarException(self):
        MP = MeasureParser()
        mxBarline = self.EL('<barline><bar-style>light-heavy</bar-style></barline>')
        # Raises the BarException
        self.assertRaises(bar.BarException, MP.xmlToRepeat, mxBarline)

        mxBarline = self.EL('<barline><bar-style>light-heavy</bar-style>'
                            + '<repeat direction="backward"/></barline>')

        # all fine now, no exceptions here
        MP.xmlToRepeat(mxBarline)

        # Raising the BarException
        mxBarline = self.EL('<barline><bar-style>wunderbar</bar-style></barline>')
        self.assertRaises(bar.BarException, MP.xmlToRepeat, mxBarline)

    def testChordSymbolException(self):
        MP = MeasureParser()
        mxHarmony = self.EL('<harmony><root><root-step>A</root-step></root>'
        '<degree><degree-value></degree-value><degree-type>add</degree-type></degree></harmony>')
        with self.assertRaisesRegex(MusicXMLImportException, 'degree-value missing'):
            MP.xmlToChordSymbol(mxHarmony)

    def testStaffLayout(self):
        from music21 import corpus
        c = corpus.parse('demos/layoutTest.xml')
        layouts = c.flat.getElementsByClass('LayoutBase').stream()
        systemLayouts = layouts.getElementsByClass('SystemLayout')
        self.assertEqual(len(systemLayouts), 42)
        staffLayouts = layouts.getElementsByClass('StaffLayout')
        self.assertEqual(len(staffLayouts), 20)
        pageLayouts = layouts.getElementsByClass('PageLayout')
        self.assertEqual(len(pageLayouts), 10)
        scoreLayouts = layouts.getElementsByClass('ScoreLayout')
        self.assertEqual(len(scoreLayouts), 1)

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
        from music21 import corpus
        c = corpus.parse('demos/layoutTestMore.xml')
        layouts = c.flat.getElementsByClass('LayoutBase').stream()
        self.assertEqual(len(layouts), 76)
        systemLayouts = layouts.getElementsByClass('SystemLayout')
        sl0 = systemLayouts[0]
        self.assertEqual(sl0.distance, None)
        self.assertEqual(sl0.topDistance, 211.0)
        self.assertEqual(sl0.leftMargin, 70.0)
        self.assertEqual(sl0.rightMargin, 0.0)

        staffLayouts = layouts.getElementsByClass('StaffLayout')
        sizes = []
        for s in staffLayouts:
            if s.staffSize is not None:
                sizes.append(s.staffSize)
        self.assertEqual(sizes, [80.0, 120.0, 80.0])

    def testCountDynamics(self):
        '''
        good test of both dynamics and a PartStaff...
        '''
        from music21 import corpus
        c = corpus.parse('schoenberg/opus19/movement2.mxl')
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

    def testTrillOnOneNote(self):
        from music21 import converter
        thisDir = common.getSourceFilePath() / 'musicxml'
        testFp = thisDir / 'testTrillOnOneNote.xml'
        c = converter.parse(testFp)  # , forceSource=True)

        trillExtension = c.parts[0].getElementsByClass('TrillExtension')[0]
        fSharpTrill = c.recurse().notes[0]
        # print(trillExtension.placement)
        self.assertEqual(fSharpTrill.name, 'F#')
        self.assertIs(trillExtension[0], fSharpTrill)
        self.assertIs(trillExtension[-1], fSharpTrill)

    def testLucaGloriaSpanners(self):
        '''
        lots of lines, including overlapping here; testing that
        a line attached to a rest is still there.  Formerly was a problem.

        Many more tests could be done on this piece...
        '''
        from music21 import corpus
        c = corpus.parse('luca/gloria')
        r = c.parts[1].measure(99).getElementsByClass('Rest')[0]
        bracketAttachedToRest = r.getSpannerSites()[0]
        self.assertIn('Line', bracketAttachedToRest.classes)
        self.assertEqual(bracketAttachedToRest.idLocal, '1')

        # c.show()
        # c.parts[1].show('t')

    def testTwoVoicesWithChords(self):
        from music21 import corpus
        c = corpus.parse('demos/voices_with_chords.xml')
        m1 = c.parts[0].measure(1)
        # m1.show('text')
        firstChord = m1.voices.getElementById('2').getElementsByClass('Chord')[0]
        self.assertEqual(repr(firstChord), '<music21.chord.Chord G4 B4>')
        self.assertEqual(firstChord.offset, 1.0)

    def testParseTupletStartStop(self):
        '''
        test that three notes with tuplets start, none, stop
        have these types
        '''

        def getNoteByTupletTypeNumber(tupletType=None, number=None):
            mxNBase = '''
            <note>
            <pitch>
              <step>C</step>
              <octave>4</octave>
            </pitch>
            <duration>56</duration>
            <voice>1</voice>
            <type>quarter</type>
            <time-modification>
              <actual-notes>3</actual-notes>
              <normal-notes>2</normal-notes>
            </time-modification>
            '''
            mxNEnd = '</note>'
            if tupletType is None:
                return mxNBase + mxNEnd

            if number is None:
                mxNMiddle = f'<notations><tuplet type="{tupletType}" /></notations>'
            else:
                mxNMiddle = (
                    f'<notations><tuplet number="{number}" type="{tupletType}" /></notations>'
                )
            return mxNBase + mxNMiddle + mxNEnd

        n0 = getNoteByTupletTypeNumber('start', 1)
        n1 = getNoteByTupletTypeNumber()
        n2 = getNoteByTupletTypeNumber('stop', 1)

        MP = MeasureParser()
        tupTypes = ('start', None, 'stop')
        for i, n in enumerate([n0, n1, n2]):
            mxNote = ET.fromstring(n)
            # mxNotations = mxNote.find('notations')
            # mxTuplets = mxNotations.findall('tuplet')
            tuplets = MP.xmlToTuplets(mxNote)
            self.assertEqual(len(tuplets), 1)
            self.assertEqual(tuplets[0].type, tupTypes[i])

        # without number....
        n0 = getNoteByTupletTypeNumber('start')
        n1 = getNoteByTupletTypeNumber()
        n2 = getNoteByTupletTypeNumber('stop')

        MP = MeasureParser()
        tupTypes = ('start', None, 'stop')
        for i, n in enumerate([n0, n1, n2]):
            mxNote = ET.fromstring(n)
            # mxNotations = mxNote.find('notations')
            # mxTuplets = mxNotations.findall('tuplet')
            tuplets = MP.xmlToTuplets(mxNote)
            self.assertEqual(len(tuplets), 1)
            self.assertEqual(tuplets[0].type, tupTypes[i])

    def testComplexTupletNote(self):
        '''
        test that a note with nested tuplets gets converted properly.
        '''
        mxN = '''
        <note default-x="347">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>9</actual-notes>
          <normal-notes>4</normal-notes>
        </time-modification>
        <stem default-y="-55">down</stem>
        <beam number="1">begin</beam>
        <notations>
          <tuplet bracket="yes" number="1" placement="below" type="start">
            <tuplet-actual>
              <tuplet-number>3</tuplet-number>
              <tuplet-type>eighth</tuplet-type>
            </tuplet-actual>
            <tuplet-normal>
              <tuplet-number>2</tuplet-number>
              <tuplet-type>eighth</tuplet-type>
            </tuplet-normal>
          </tuplet>
          <tuplet number="2" placement="below" type="start">
            <tuplet-actual>
              <tuplet-number>3</tuplet-number>
              <tuplet-type>eighth</tuplet-type>
            </tuplet-actual>
            <tuplet-normal>
              <tuplet-number>2</tuplet-number>
              <tuplet-type>eighth</tuplet-type>
            </tuplet-normal>
          </tuplet>
        </notations>
      </note>
        '''
        MP = MeasureParser()
        mxNote = ET.fromstring(mxN)
        # mxNotations = mxNote.find('notations')
        # mxTuplets = mxNotations.findall('tuplet')
        tuplets = MP.xmlToTuplets(mxNote)
        self.assertEqual(len(tuplets), 2)
        MP.xmlToNote(mxNote)
        n = MP.nLast
        self.assertEqual(len(n.duration.tuplets), 2)
        expected_tuplet_repr = ('(<music21.duration.Tuplet 3/2/eighth>, '
                                + '<music21.duration.Tuplet 3/2/eighth>)')
        self.assertEqual(repr(n.duration.tuplets),
                         expected_tuplet_repr)
        self.assertEqual(n.duration.quarterLength, fractions.Fraction(2, 9))

    def testNestedTuplets(self):
        from music21 import corpus
        c = corpus.parse('demos/nested_tuplet_finale_test2.xml')
        nList = list(c.recurse().notes)
        self.assertEqual(repr(nList[0].duration.tuplets),
                         '(<music21.duration.Tuplet 3/2/eighth>,)')
        expected_tuplet_repr_1_to_6 = ('(<music21.duration.Tuplet 3/2/eighth>, '
                                       + '<music21.duration.Tuplet 5/2/eighth>)')
        for i in range(1, 6):
            self.assertEqual(repr(nList[i].duration.tuplets),
                             expected_tuplet_repr_1_to_6)
        self.assertEqual(repr(nList[6].duration.tuplets), '()')
        expected_tuplet_repr_7_to_12 = ('(<music21.duration.Tuplet 5/4/16th>, '
                                        + '<music21.duration.Tuplet 3/2/eighth>)')
        for i in range(7, 12):
            self.assertEqual(repr(nList[i].duration.tuplets),
                             expected_tuplet_repr_7_to_12)
        self.assertEqual(repr(nList[12].duration.tuplets),
                         '(<music21.duration.Tuplet 3/2/eighth>,)')

    def testImpliedTuplet(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.tupletsImplied)
        # First tuplet group of 3 is silent on bracket and show-number: draw bracket
        # Second tuplet group of 3 is silent on bracket but show-number="none": don't draw bracket
        tuplets = [n.duration.tuplets[0] for n in s.flat.notes]
        self.assertEqual([tup.bracket for tup in tuplets], [True, True, True, False, False, False])

    def test34MeasureRestWithoutTag(self):
        from xml.etree.ElementTree import fromstring as EL

        scoreMeasure = '<measure><note><rest/><duration>40320</duration></note></measure>'
        mxMeasure = EL(scoreMeasure)
        pp = PartParser()
        pp.lastTimeSignature = meter.TimeSignature('3/4')
        m = pp.xmlMeasureToMeasure(mxMeasure)
        measureRest = m.notesAndRests[0]
        self.assertEqual(measureRest.duration.type, 'half')
        self.assertEqual(measureRest.duration.quarterLength, 3.0)

    def testPickupMeasureRestSchoenberg(self):
        '''
        Staff 2 of piano part 0 of schoenberg opus19.6 has a quarter rest not
        marked as a full measure rest (GOOD) as the last beat of a pickup measure.

        It should NOT become a full measure rest
        '''
        from music21 import corpus
        sch = corpus.parse('schoenberg/opus19/movement6')
        r = sch.parts[1].measure(1).notesAndRests[0]
        self.assertEqual(r.duration.type, 'quarter')
        self.assertEqual(r.fullMeasure, 'auto')

    def testRehearsalMarks(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.directions31a)
        rmIterator = s.recurse().getElementsByClass('RehearsalMark')
        self.assertEqual(len(rmIterator), 4)
        self.assertEqual(rmIterator[0].content, 'A')
        self.assertEqual(rmIterator[1].content, 'B')
        self.assertEqual(rmIterator[1].style.enclosure, None)
        self.assertEqual(rmIterator[2].content, 'Test')
        self.assertEqual(rmIterator[2].style.enclosure, 'square')

    def testNoChordImport(self):
        from music21 import converter

        thisDir = common.getSourceFilePath() / 'musicxml'
        testFp = thisDir / 'testNC.xml'
        s = converter.parse(testFp)

        self.assertEqual(5, len(s.flat.getElementsByClass('ChordSymbol')))
        self.assertEqual(2, len(s.flat.getElementsByClass('NoChord')))

        self.assertEqual('augmented-seventh',
                         s.flat.getElementsByClass('ChordSymbol')[0].chordKind)
        self.assertEqual('none', s.flat.getElementsByClass('ChordSymbol')[1].chordKind)

        self.assertEqual('random', str(s.flat.getElementsByClass('NoChord')[
            0].chordKindStr))
        self.assertEqual('N.C.', str(s.flat.getElementsByClass('NoChord')[
            1].chordKindStr))

    def testChordAlias(self):
        '''
        m21 name ('dominant-seventh') should be looked up from musicXML aliases
        (such as 'dominant').
        '''
        from xml.etree.ElementTree import fromstring as EL
        mp = MeasureParser()

        elStr = '<harmony><root><root-step>D</root-step><root-alter>-1</root-alter>'
        elStr += '</root><kind>major-minor</kind></harmony>'
        mxHarmony = EL(elStr)
        cs = mp.xmlToChordSymbol(mxHarmony)
        self.assertEqual(cs.chordKind, 'minor-major-seventh')

    def testChordOffset(self):
        from music21 import converter

        thisDir = common.getSourceFilePath() / 'musicxml'
        testFp = thisDir / 'testChordOffset.xml'
        s = converter.parse(testFp)

        offsets = [0.0, 2.0, 0.0, 2.0, 0.0, 2.0]
        for ch, offset in zip(s.recurse().getElementsByClass('ChordSymbol'),
                              offsets):
            self.assertEqual(ch.offset, offset)

    def testChordInversion(self):
        from xml.etree.ElementTree import fromstring as EL
        h = EL("""
        <harmony><root><root-step>C</root-step></root>
        <kind>major</kind><inversion>1</inversion></harmony>""")
        mp = MeasureParser()
        cs = mp.xmlToChordSymbol(h)
        self.assertEqual(cs.inversion(), 1)

    def testLineHeight(self):
        from xml.etree.ElementTree import fromstring as EL
        el1 = EL('<bracket type="start" line-end="down" end-length="12.5" number="1"></bracket>')
        el2 = EL('<bracket type="stop" line-end="down" end-length="12.5" number="1"></bracket>')

        mp = MeasureParser()
        line = mp.xmlDirectionTypeToSpanners(el1)[0]
        mp.xmlDirectionTypeToSpanners(el2)
        self.assertEqual(line.startHeight, 12.5)
        self.assertEqual(line.endHeight, 12.5)

    def testStringIndication(self):
        from music21 import converter

        thisDir = common.getSourceFilePath() / 'musicxml'
        testFp = thisDir / 'testTab.xml'
        score = converter.parse(testFp)
        guitar_part = score.parts[0]
        notes = list(guitar_part.recurse().notes)

        self.assertIsInstance(notes[0].articulations[0], articulations.StringIndication)
        self.assertEqual(notes[0].articulations[0].number, 4)

        self.assertIsInstance(notes[1].articulations[0], articulations.StringIndication)
        self.assertEqual(notes[1].articulations[0].number, 4)

        self.assertIsInstance(notes[2].articulations[0], articulations.StringIndication)
        self.assertEqual(notes[2].articulations[0].number, 1)

        self.assertIsInstance(notes[3].articulations[0], articulations.StringIndication)
        self.assertEqual(notes[3].articulations[0].number, 2)

    def testFretIndication(self):
        from music21 import converter

        thisDir = common.getSourceFilePath() / 'musicxml'
        testFp = thisDir / 'testTab.xml'
        score = converter.parse(testFp)
        guitar_part = score.parts[0]
        notes = list(guitar_part.recurse().notes)

        self.assertIsInstance(notes[0].articulations[1], articulations.FretIndication)
        self.assertEqual(notes[0].articulations[1].number, 7)

        self.assertIsInstance(notes[1].articulations[1], articulations.FretIndication)
        self.assertEqual(notes[1].articulations[1].number, 4)

        self.assertIsInstance(notes[2].articulations[1], articulations.FretIndication)
        self.assertEqual(notes[2].articulations[1].number, 0)

        self.assertIsInstance(notes[3].articulations[1], articulations.FretIndication)
        self.assertEqual(notes[3].articulations[1].number, 3)

    def testHiddenRests(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        # Voice 1: Half note, <forward> (quarter), quarter note
        # Voice 2: <forward> (half), quarter note, <forward> (quarter)
        s = converter.parse(testPrimitive.hiddenRests)
        v1, v2 = s.recurse().voices
        self.assertEqual(v1.duration.quarterLength, v2.duration.quarterLength)

        restV1 = v1.getElementsByClass(note.Rest)[0]
        self.assertTrue(restV1.style.hideObjectOnPrint)
        restsV2 = v2.getElementsByClass(note.Rest)
        self.assertEqual([r.style.hideObjectOnPrint for r in restsV2], [True, True])

    def testMultiDigitEnding(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        # Relevant barlines:
        # Measure 2, left barline: <ending number="1,2" type="start"/>
        # Measure 2, right barline: <ending number="1,2" type="stop"/>
        # Measure 3, left barline: <ending number="3" type="start"/>
        # Measure 3, right barline: <ending number="3" type="stop"/>
        score = converter.parse(testPrimitive.multiDigitEnding)
        repeatBrackets = score.recurse().getElementsByClass('RepeatBracket')
        self.assertListEqual(repeatBrackets[0].getNumberList(), [1, 2])
        self.assertListEqual(repeatBrackets[1].getNumberList(), [3])

        nonconformingInput = testPrimitive.multiDigitEnding.replace("1,2", "ad lib.")
        score2 = converter.parse(nonconformingInput)
        repeatBracket = score2.recurse().getElementsByClass('RepeatBracket')[0]
        self.assertListEqual(repeatBracket.getNumberList(), [1])

    def testChordAlteration(self):
        from music21 import musicxml
        from xml.etree.ElementTree import fromstring as EL
        MP = musicxml.xmlToM21.MeasureParser()
        elStr = (r'''<harmony><root><root-step>C</root-step></root><kind text="7b5">dominant</kind>
        <degree><degree-value>5</degree-value><degree-alter>-1</degree-alter>
        <degree-type>alter</degree-type></degree></harmony>''')
        mxHarmony = EL(elStr)
        cs = MP.xmlToChordSymbol(mxHarmony)
        # Check that we parsed a modification
        self.assertTrue(len(cs.getChordStepModifications()) == 1)
        # And that it affected the correct pitch in the right way
        self.assertTrue(pitch.Pitch("G-3") == cs.pitches[2])

    def testCompositeLyrics(self):
        '''
        Tests multiple lyrics in same note but with same number (not stanza change)
        '''
        from music21 import converter

        xmlDir = common.getSourceFilePath() / 'musicxml' / 'lilypondTestSuite'
        fp = xmlDir / '61l-Lyrics-Elisions-Syllables.xml'
        s = converter.parse(fp)
        notes = list(s.flat.notes)

        # Check that the second note has one composite lyric
        self.assertEqual(len(notes[1].lyrics), 1)
        ly1 = notes[1].lyrics[0]
        self.assertTrue(ly1.isComposite)
        self.assertEqual(ly1.syllabic, 'composite')
        self.assertEqual(len(ly1.components), 2)
        self.assertEqual(ly1.components[0].text, 'b')
        self.assertEqual(ly1.components[0].syllabic, 'middle')
        self.assertEqual(ly1.components[1].text, 'c')
        self.assertEqual(ly1.components[1].syllabic, 'middle')
        self.assertEqual(ly1.components[1].elisionBefore, ' ')

        # Third note is similar, but begins in the middle and ends at end
        # with empty elision tag.  Just check the rawText
        self.assertEqual(notes[2].name, 'E')  # make sure have right note
        self.assertEqual(len(notes[2].lyrics), 1)
        ly2 = notes[2].lyrics[0]
        self.assertEqual(len(ly2.components), 2)
        self.assertEqual(ly2.components[1].elisionBefore, '')
        self.assertEqual(ly2.rawText, '-de')

        # Check that the fourth note has parsed three separated lyrics (diff syllabic)
        self.assertEqual(notes[3].name, 'F')  # make sure have right note
        self.assertEqual(len(notes[3].lyrics), 1)
        ly3 = notes[3].lyrics[0]
        self.assertEqual(len(ly3.components), 3)
        self.assertEqual(ly3.components[1].elisionBefore, '_')
        self.assertEqual(ly3.components[2].elisionBefore, '~')
        self.assertEqual(ly3.rawText, 'f_g~h')
        self.assertEqual(ly3.components[0].syllabic, 'begin')
        self.assertEqual(ly3.components[1].syllabic, 'middle')
        self.assertEqual(ly3.components[2].syllabic, 'end')
        self.assertEqual(len(s.lyrics(recurse=True)[1][0]), 4)


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)  # , runTest='testExceptionMessage')
