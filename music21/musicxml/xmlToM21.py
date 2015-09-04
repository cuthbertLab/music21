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
import xml.etree.ElementTree as ET
import unittest

from music21.ext import six
from music21 import common
from music21 import exceptions21

# modules that import this include converter.py.
# thus, cannot import these here
from music21 import articulations 
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



class MusicXMLImporter(object):
    '''
    Object for importing .xml, .mxl, .musicxml, MusicXML files into music21.
    '''
    def __init__(self):
        self.xmlText = None
        self.xmlFilename = None
        self.etree = None
        self.xmlRoot = None
        self.stream = stream.Score()
    
    def scoreFromFile(self, filename, systemScore = False):
        '''
        main program: opens a file given by filename and returns a complete
        music21 Score from it.
        '''
        self.parseXMLText()
        scoreObj = self.systemScoreFromScore(self.mainDom)
        if systemScore is True:
            return scoreObj
        else:
            partScore = self.partScoreFromSystemScore(scoreObj)
            return partScore
    
    def parseXMLText(self):
        sio = six.StringIO(self.xmlText)
        self.etree = ET.parse(sio)
        self.root = self.etree.getroot()
        if self.root.tag != 'score-partwise':
            raise MusicXMLImportException("Cannot parse MusicXML files not in score-partwise. Root tag was '{0}'".format(self.root.tag))
        self.xmlRootToScore(self.root, self.stream)

    def xmlRootToScore(self, mxScore, inputM21=None):
        '''
        parse an xml file into a Score() object.
        '''
        if inputM21 is None:
            s = stream.Score()
        else:
            s = inputM21
            
        md = self.xmlMetadata(mxScore)
        s._insertCore(0, md)
        
        mxDefaults = mxScore.find('defaults')
        if mxDefaults is not None:
            scoreLayout = self.xmlDefaultsToScoreLayout(mxDefaults)
            s._insertCore(0, scoreLayout)

        for mxCredit in mxScore.findall('credit'):
            credit = self.xmlCreditToTextBox(mxCredit)
            s._insertCore(0, credit)

            
        if inputM21 is None:
            return s
        
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
            content.append(cw.text)
        if len(content) == 0: # no text defined
            raise MusicXMLImportException('no credit words defined for a credit tag')
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
        Convert a :class:`~music21.musicxml.mxObjects.Defaults` 
        object to a :class:`~music21.layout.ScoreLayout` 
        object
        '''
        if inputM21 is None:
            scoreLayout = layout.ScoreLayout()
        else:
            scoreLayout = inputM21

        seta = self._setAttributeFromTagText

        mxScaling = mxDefaults.find('scaling')
        if mxScaling is not None:
            seta(scoreLayout, mxScaling, 'millimeters', 'scalingMillimeters', transform=float)
            seta(scoreLayout, mxScaling, 'tenths', 'scalingTenths', transform=float)
    
        mxPageLayout = mxDefaults.find('page-layout')
        if mxPageLayout is not None:
            scoreLayout.pageLayout = self.xmlPageLayoutToPageLayout(mxPageLayout)
        mxSystemLayout = mxDefaults.find('system-layout')
        if mxSystemLayout is not None:
            scoreLayout.systemLayout = self.xmlSystemLayoutToSystemLayout(mxSystemLayout)
        mxStaffLayout = mxDefaults.find('staff-layout')
        if mxStaffLayout is not None:
            scoreLayout.staffLayout = self.xmlStaffLayoutToStaffLayout(mxStaffLayout)
        
        # TODO: appearance
        # TODO: music-font
        # TODO: word-font
        # TODO: lyric-font
        # TODO: lyric-language
        
        return scoreLayout

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

        seta = self._setAttributeFromTagText
        
        seta(pageLayout, mxPageLayout, 'page-height', transform=float)
        seta(pageLayout, mxPageLayout, 'page-width', transform=float)
        
        #TODO -- record even, odd, both margins
        mxPageMargins = mxPageLayout.find('page-margins')
        if mxPageMargins is not None:
            for direction in ('top', 'bottom', 'left', 'right'):
                seta(pageLayout, mxPageMargins, direction + '-margin', transform=float)    
    
        if inputM21 is None:
            return pageLayout

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
    
        seta = self._setAttributeFromTagText

        #TODO -- record even, odd, both margins
        mxSystemMargins = mxSystemLayout.find('system-margins')
        if mxSystemMargins is not None:
            for direction in ('top', 'bottom', 'left', 'right'):
                seta(systemLayout, mxSystemMargins, direction + '-margin', transform=float)    

        seta(systemLayout, mxSystemLayout, 'system-distance', 'distance', transform=float)
        seta(systemLayout, mxSystemLayout, 'top-system-distance', 'topDistance', transform=float)
        
        # TODO: system-dividers

        if inputM21 is None:
            return systemLayout

    def xmlStaffLayoutToStaffLayout(self, mxStaffLayout, inputM21=None):
        '''
        get a StaffLayout object from an <staff-layout> tag
        '''
        if inputM21 is None:
            staffLayout = layout.StaffLayout()
        else:
            staffLayout = inputM21
        
        seta = self._setAttributeFromTagText
        seta(staffLayout, mxStaffLayout, 'staff-distance', 'distance', transform=float)

        if mxStaffLayout.staffDistance != None:
            staffLayout.distance = float(mxStaffLayout.staffDistance)

        data = mxStaffLayout.get('number')
        if data is not None:
            staffLayout.staffNumber = int(data)
        
        if inputM21 is None:
            return staffLayout

        
#     def _TagText(self, el, tag):
#         '''
#         helper function: checks whether a particular
#         tag exists at least once in el and if the
#         first tag of that type has text
#         '''
#         pass
    
        
    def xmlMetadata(self, el=None, inputM21=None):
        '''
        Converts part of the root element into a metadata object
        
        Supported: work-title, work-number, opus, movement-number,
        movement-title, identification (creator)
        
        Not supported: rights, encoding, source, relation, miscellaneous
        '''
        if el is None:
            el = self.root
        if inputM21 is not None:
            md = inputM21
        else:
            md = metadata.Metadata()
            
        seta = self._setAttributeFromTagText
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
            
        c.name = creator.text.strip()
        if inputM21 is None:
            return c        
        

    #------------------------------------------------------------------------------
    # Helpers...

#     def _runIfTag(self, el, tag, func, inputM21=None):
#         '''
#         If an ElementTree.Element has a element of a certain tag, get it as
#         mxObj, then call:
#         
#             return self.func(mxObj, inputM21)
#             
#         else, ret
#         CRAP, needs more...
#         '''
#         
#         mxObj = el.find('tag')
        

    def _setAttributeFromTagText(self, m21El, xmlEl, tag, attributeName=None, transform=None):
        '''
        If xmlEl has a at least one element of tag==tag with some text. If
        it does, set the attribute either with the same name (with "foo-bar" changed to
        "fooBar") or with attributeName to the text contents.
        
        Pass a function or lambda function as transform to transform the value before setting it
        
        >>> from xml.etree.ElementTree import Element, SubElement
        >>> e = Element('accidental')
        >>> a = SubElement(e, 'alter')
        >>> a.text = '-2'

        >>> MI = musicxml.xmlToM21.MusicXMLImporter()
        >>> acc = pitch.Accidental()
        >>> MI._setAttributeFromTagText(acc, e, 'alter')
        >>> acc.alter
        '-2'

        Transform the alter text to an int.

        >>> MI._setAttributeFromTagText(acc, e, 'alter', transform=int)
        >>> acc.alter
        -2
        
        >>> e2 = Element('score-partwise')
        >>> a2 = SubElement(e2, 'movement-title')
        >>> a2.text = "Trout"
        >>> md = metadata.Metadata()
        >>> MI._setAttributeFromTagText(md, e2, 'movement-title')
        >>> md.movementTitle
        'Trout'
        
        set a different attribute
        
        >>> MI._setAttributeFromTagText(md, e2, 'movement-title', 'composer')
        >>> md.composer
        'Trout'
        '''
        matchEl = xmlEl.find(tag) # find first
        if matchEl is None:
            return
        if matchEl.text in (None, ""):
            return 
        value = matchEl.text

        if transform is not None:
            value = transform(value)

        if attributeName is None:
            attributeName = common.hyphenToCamelCase(tag)
        setattr(m21El, attributeName, value)


class Test(unittest.TestCase):
    pass

    def testParseSimple(self):
        MI = MusicXMLImporter()
        MI.xmlText = r'''<score-timewise />'''
        self.assertRaises(MusicXMLImportException, MI.parseXMLText)

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
    
    
