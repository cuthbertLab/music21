# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         musicxml/m21ToXML.py
# Purpose:      Translate from music21 objects to musicxml representation
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010-2012, 2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Converters for music21 objects to musicxml.

Does not handle the entire string architecture, that's what m21ToString is for.

Assumes that the outermost object is a score.
'''
import unittest
import copy
from music21.ext import webcolors, six

if six.PY3:
    import xml.etree.ElementTree as ET  # @UnusedImport
    from xml.etree.ElementTree import Element, SubElement

else:
    try:
        import xml.etree.cElementTree as ET
        from xml.etree.cElementTree import Element, SubElement

    except ImportError:
        import xml.etree.ElementTree as ET # @UnusedImport
        from xml.etree.ElementTree import Element, SubElement


# modules that import this include converter.py.
# thus, cannot import these here
from music21 import common
from music21 import defaults
from music21 import exceptions21

from music21 import bar
from music21 import key
from music21 import metadata
from music21 import note
from music21 import meter
from music21 import spanner
from music21 import stream

from music21.musicxml import xmlObjects

from music21 import environment
_MOD = "musicxml.m21ToXML"
environLocal = environment.Environment(_MOD)

#-------------------------------------------------------------------------------
class ToMxObjectsException(exceptions21.Music21Exception):
    pass
class NoteheadException(ToMxObjectsException):
    pass

def dump(xmlEl):
    '''
    wrapper around xml.etree.ElementTree as ET that returns a string
    in every case, whether Py2 or Py3...

    >>> from xml.etree.ElementTree import Element
    >>> e = Element('accidental')
    >>> musicxml.m21ToXML.dump(e)
    '<accidental />'
    
    >>> e.text = u'∆'
    >>> musicxml.m21ToXML.dump(e)
    '<accidental>∆</accidental>'
    '''
    if six.PY2:
        return ET.tostring(xmlEl)
    else:
        return ET.tostring(xmlEl, encoding='unicode')

def _setTagTextFromAttribute(m21El, xmlEl, tag, attributeName=None, 
                             transform=None, forceEmpty=False):
    '''
    If m21El has an attribute called attributeName, create a new SubElement
    for xmlEl and set its text to the value of the m21El attribute.
    
    Pass a function or lambda function as transform to transform the
    value before setting it.  String transformation is assumed.
    
    Returns the subelement
    
    Will not create an empty element unless forceEmpty is True
    
    >>> from xml.etree.ElementTree import Element
    >>> e = Element('accidental')

    >>> seta = musicxml.m21ToXML._setTagTextFromAttribute
    >>> acc = pitch.Accidental()
    >>> acc.alter = -2
    >>> subEl = seta(acc, e, 'alter')
    >>> subEl.text
    '-2'
    >>> subEl in e
    True
    >>> musicxml.m21ToXML.dump(e)
    '<accidental><alter>-2</alter></accidental>'
    '''
    if attributeName is None:
        attributeName = common.hyphenToCamelCase(tag)

    try:
        value = getattr(m21El, attributeName)
    except AttributeError:
        return None

    if transform is not None:
        value = transform(value)

    if value in (None, "") and forceEmpty is not True:
        return None
    
    subElement = SubElement(xmlEl, tag)
    
    if value not in (None, ""):
        subElement.text = str(value)

    return subElement
    
def _setAttributeFromAttribute(m21El, xmlEl, xmlAttributeName, attributeName=None, transform=None):
    '''
    If m21El has a at least one element of tag==tag with some text. If
    it does, set the attribute either with the same name (with "foo-bar" changed to
    "fooBar") or with attributeName to the text contents.
    
    Pass a function or lambda function as transform to transform the value before setting it
    
    >>> from xml.etree.ElementTree import fromstring as El

    >>> e = El('<page-layout/>')

    >>> setb = musicxml.m21ToXML._setAttributeFromAttribute
    >>> pl = layout.PageLayout()
    >>> pl.pageNumber = 4
    >>> pl.isNew = True
    
    >>> setb(pl, e, 'page-number')
    >>> e.get('page-number')
    '4'
    >>> musicxml.m21ToXML.dump(e)
    '<page-layout page-number="4" />'

    >>> setb(pl, e, 'new-page', 'isNew')
    >>> e.get('new-page')
    'True'


    Transform the isNew value to 'yes'.

    >>> convBool = musicxml.xmlObjects.booleanToYesNo
    >>> setb(pl, e, 'new-page', 'isNew', transform=convBool)
    >>> e.get('new-page')
    'yes'
    '''
    if attributeName is None:
        attributeName = common.hyphenToCamelCase(xmlAttributeName)

    value = getattr(m21El, attributeName)
    if value is None:
        return

    if transform is not None:
        value = transform(value)

    xmlEl.set(xmlAttributeName, str(value))



class XMLExporterBase(object):
    '''
    contains functions that could be called
    at multiple levels of exporting (Score, Part, Measure).
    '''
    m21AccidentalToMx = {'half-sharp': 'quarter-sharp',
                         'one-and-a-half-sharp': 'three-quarters-sharp',
                         'half-flat': 'quarter-flat',
                         'one-and-a-half-flat': 'three-quarters-flat',
                         }

    
    def __init__(self):
        pass
    
    def setPosition(self, m21Object, mxObject):
        if hasattr(m21Object, 'xPosition') and m21Object.xPosition is not None:
            mxObject.set('default-x', m21Object.xPosition)
        # TODO: attr: default-y, relative-x, relative-y
        # TODO: standardize "positionVertical, etc.

    def pageLayoutToXmlPrint(self, pageLayout, mxPrintIn=None):
        '''
        Given a PageLayout object, set object data for <print> 
    
        >>> pl = layout.PageLayout()
        >>> pl.pageHeight = 4000
        >>> pl.isNew = True
        >>> pl.rightMargin = 30.25
        >>> pl.leftMargin = 20
        >>> pl.pageNumber = 5

        >>> XPBase = musicxml.m21ToXML.XMLExporterBase()
        >>> mxPrint = XPBase.pageLayoutToXmlPrint(pl)
        >>> musicxml.m21ToXML.dump(mxPrint)
        '<print new-page="yes" page-number="5"><page-layout><page-height>4000</page-height><page-margins><left-margin>20</left-margin><right-margin>30.25</right-margin></page-margins></page-layout></print>'


        >>> MP = musicxml.xmlToM21.MeasureParser()
        >>> pl2 = MP.xmlPrintToPageLayout(mxPrint)
        >>> pl2.isNew
        True
        >>> pl2.rightMargin
        30.25
        >>> pl2.leftMargin
        20
        >>> pl2.pageNumber
        5    
        >>> pl2.pageHeight
        4000
        '''
        if mxPrintIn is None:
            mxPrint = Element('print')
        else:
            mxPrint = mxPrintIn
        
        setb = _setAttributeFromAttribute
        setb(pageLayout, mxPrint, 'new-page', 'isNew', transform=xmlObjects.booleanToYesNo)
        setb(pageLayout, mxPrint, 'page-number')
    
        mxPageLayout = self.pageLayoutToXmlPageLayout(pageLayout)
        mxPrint.append(mxPageLayout)
    
        if mxPrintIn is None:
            return mxPrint
        
    def pageLayoutToXmlPageLayout(self, pageLayout, mxPageLayoutIn=None):
        '''
        get a <page-layout> element from a PageLayout
        
        Called out from pageLayoutToXmlPrint because it
        is also used in the <defaults> tag
        '''
        if mxPageLayoutIn is None:
            mxPageLayout = Element('page-layout')
        else:
            mxPageLayout = mxPageLayoutIn

        seta = _setTagTextFromAttribute
        
        seta(pageLayout, mxPageLayout, 'page-height')
        seta(pageLayout, mxPageLayout, 'page-width')
        
        #TODO -- record even, odd, both margins
        mxPageMargins = Element('page-margins')
        for direction in ('top', 'bottom', 'left', 'right'):
            seta(pageLayout, mxPageMargins, direction + '-margin')
        if len(mxPageMargins) > 0:
            mxPageLayout.append(mxPageMargins)

        if mxPageLayoutIn is None:
            return mxPageLayout


    def systemLayoutToXmlPrint(self, systemLayout, mxPrintIn=None):
        '''
        Given a SystemLayout tag, set a <print> tag
        
        >>> sl = layout.SystemLayout()
        >>> sl.distance = 55
        >>> sl.isNew = True
        >>> sl.rightMargin = 30.25
        >>> sl.leftMargin = 20

        >>> XPBase = musicxml.m21ToXML.XMLExporterBase()
        >>> mxPrint = XPBase.systemLayoutToXmlPrint(sl)
        >>> musicxml.m21ToXML.dump(mxPrint)
        '<print new-system="yes"><system-layout><system-margins><left-margin>20</left-margin><right-margin>30.25</right-margin></system-margins><system-distance>55</system-distance></system-layout></print>'

        Test return conversion
        
        >>> MP = musicxml.xmlToM21.MeasureParser()
        >>> sl2 = MP.xmlPrintToSystemLayout(mxPrint)
        >>> sl2.isNew
        True
        >>> sl2.rightMargin
        30.25
        >>> sl2.leftMargin
        20
        >>> sl2.distance
        55
        '''
        if mxPrintIn is None:
            mxPrint = Element('print')
        else:
            mxPrint = mxPrintIn
    
        setb = _setAttributeFromAttribute
        setb(systemLayout, mxPrint, 'new-system', 'isNew', transform=xmlObjects.booleanToYesNo)
        mxSystemLayout = SubElement(mxPrint, 'system-layout')
        self.systemLayoutToXmlSystemLayout(systemLayout, mxSystemLayout)
    
        if mxPrintIn is None:
            return mxPrint


    def systemLayoutToXmlSystemLayout(self, systemLayout, mxSystemLayoutIn=None):
        '''
        get given a SystemLayout object configure <system-layout> or <print>
        
        Called out from xmlPrintToSystemLayout because it
        is also used in the <defaults> tag

        >>> sl = layout.SystemLayout()
        >>> sl.distance = 40.0
        >>> sl.topDistance = 70.0
        >>> XPBase = musicxml.m21ToXML.XMLExporterBase()
        >>> mxSl = XPBase.systemLayoutToXmlSystemLayout(sl)
        >>> musicxml.m21ToXML.dump(mxSl)
        '<system-layout><system-distance>40.0</system-distance><top-system-distance>70.0</top-system-distance></system-layout>'

        >>> sl = layout.SystemLayout()
        >>> sl.leftMargin = 30.0
        >>> mxSl = XPBase.systemLayoutToXmlSystemLayout(sl)
        >>> musicxml.m21ToXML.dump(mxSl)
        '<system-layout><system-margins><left-margin>30.0</left-margin></system-margins></system-layout>'
        '''
        if mxSystemLayoutIn is None:
            mxSystemLayout = Element('system-layout')
        else:
            mxSystemLayout = mxSystemLayoutIn
    
        seta = _setTagTextFromAttribute
        
        #TODO -- record even, odd, both margins
        mxSystemMargins = Element('system-margins')
        for direction in ('top', 'bottom', 'left', 'right'):
            seta(systemLayout, mxSystemMargins, direction + '-margin')
        if len(mxSystemMargins) > 0:
            mxSystemLayout.append(mxSystemMargins)
                
        seta(systemLayout, mxSystemLayout, 'system-distance', 'distance')
        seta(systemLayout, mxSystemLayout, 'top-system-distance', 'topDistance')
        
        # TODO: system-dividers

        if mxSystemLayoutIn is None:
            return mxSystemLayout

    def staffLayoutToXmlStaffLayout(self, staffLayout, mxStaffLayoutIn=None):
        '''
        get a <staff-layout> tag from a StaffLayout object
        
        In music21, the <staff-layout> and <staff-details> are
        intertwined in a StaffLayout object.
        
        >>> sl = layout.StaffLayout()
        >>> sl.distance = 40.0
        >>> sl.staffNumber = 1
        >>> XPBase = musicxml.m21ToXML.XMLExporterBase()
        >>> mxSl = XPBase.staffLayoutToXmlStaffLayout(sl)
        >>> musicxml.m21ToXML.dump(mxSl)
        '<staff-layout number="1"><staff-distance>40.0</staff-distance></staff-layout>'
        '''
        if mxStaffLayoutIn is None:
            mxStaffLayout = Element('staff-layout')
        else:
            mxStaffLayout = mxStaffLayoutIn
        seta = _setTagTextFromAttribute
        setb = _setAttributeFromAttribute
        
        seta(staffLayout, mxStaffLayout, 'staff-distance', 'distance')
        #ET.dump(mxStaffLayout)
        setb(staffLayout, mxStaffLayout, 'number', 'staffNumber')

        if mxStaffLayoutIn is None:
            return mxStaffLayout

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):
        pass

    def testDuration2048(self):
        '''
        typeToMusicXMLType(): when converting a Duration to a MusicXML duration, 2048th notes will
            not be exported to MusicXML, for which 1024th is the shortest duration. 2048th notes
            are valid in MEI, which is how they appeared in music21 in the first place.
        '''
        expectedError = 'Cannot convert "2048th" duration to MusicXML (too short).'
#         self.assertRaises(ToMxObjectsException, typeToMusicXMLType, '2048th')
#         try:
#             typeToMusicXMLType('2048th')
#         except ToMxObjectsException as exc:
#             self.assertEqual(expectedError, exc.args[0])



if __name__ == '__main__':
    import music21
    music21.mainTest(Test)