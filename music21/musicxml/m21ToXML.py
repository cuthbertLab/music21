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
from __future__ import print_function, division

from collections import OrderedDict
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
    r'''
    wrapper around xml.etree.ElementTree as ET that returns a string
    in every case, whether Py2 or Py3...

    >>> from music21.musicxml.m21ToXML import Element
    >>> e = Element('accidental')
    >>> musicxml.m21ToXML.dump(e)
    <accidental />
    
    >>> e.text = u'∆'
    >>> e.text == u'∆'
    True
    >>> musicxml.m21ToXML.dump(e)
    <accidental>...</accidental>

    Output differs in Python2 vs 3.
    '''
    if six.PY2:
        print(ET.tostring(xmlEl))
    else:
        print(ET.tostring(xmlEl, encoding='unicode'))

def typeToMusicXMLType(value):
    '''Convert a music21 type to a MusicXML type.
    
    >>> musicxml.m21ToXML.typeToMusicXMLType('longa')
    'long'
    >>> musicxml.m21ToXML.typeToMusicXMLType('quarter')
    'quarter'
    '''
    # MusicXML uses long instead of longa
    if value == 'longa': 
        return 'long'
    elif value == '2048th':
        raise ToMxObjectsException('Cannot convert "2048th" duration to MusicXML (too short).')
    else:
        return value

def accidentalToMx(a):
    '''
    >>> a = pitch.Accidental()
    >>> a.set('half-sharp')
    >>> a.alter == .5
    True
    >>> mxAccidental = musicxml.m21ToXML.accidentalToMx(a)
    >>> musicxml.m21ToXML.dump(mxAccidental)
    <accidental>quarter-sharp</accidental>
    '''
    if a.name == "half-sharp": 
        mxName = "quarter-sharp"
    elif a.name == "one-and-a-half-sharp": 
        mxName = "three-quarters-sharp"
    elif a.name == "half-flat": 
        mxName = "quarter-flat"
    elif a.name == "one-and-a-half-flat": 
        mxName = "three-quarters-flat"
    else: # all others are the same
        mxName = a.name

    mxAccidental = Element('accidental')
    # need to remove display in this case and return None
    #         if self.displayStatus == False:
    #             pass
    mxAccidental.text = mxName
    return mxAccidental
    

def normalizeColor(color):
    if color in (None, ''):
        return color
    if '#' not in color:
        return (webcolors.css3_names_to_hex[color]).upper()
    return color 


def _setTagTextFromAttribute(m21El, xmlEl, tag, attributeName=None, 
                             transform=None, forceEmpty=False):
    '''
    If m21El has an attribute called attributeName, create a new SubElement
    for xmlEl and set its text to the value of the m21El attribute.
    
    Pass a function or lambda function as transform to transform the
    value before setting it.  String transformation is assumed.
    
    Returns the subelement
    
    Will not create an empty element unless forceEmpty is True
    
    >>> from music21.musicxml.m21ToXML import Element
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
    <accidental><alter>-2</alter></accidental>
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
    <page-layout page-number="4" />

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
    
    def __init__(self):
        pass
    
    def dump(self, obj):
        dump(obj)
    
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
        >>> XPBase.dump(mxPrint)
        <print new-page="yes" page-number="5"><page-layout><page-height>4000</page-height><page-margins><left-margin>20</left-margin><right-margin>30.25</right-margin></page-margins></page-layout></print>


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
        >>> XPBase.dump(mxPrint)
        <print new-system="yes"><system-layout><system-margins><left-margin>20</left-margin><right-margin>30.25</right-margin></system-margins><system-distance>55</system-distance></system-layout></print>

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
        >>> XPBase.dump(mxSl)
        <system-layout><system-distance>40.0</system-distance><top-system-distance>70.0</top-system-distance></system-layout>

        >>> sl = layout.SystemLayout()
        >>> sl.leftMargin = 30.0
        >>> mxSl = XPBase.systemLayoutToXmlSystemLayout(sl)
        >>> XPBase.dump(mxSl)
        <system-layout><system-margins><left-margin>30.0</left-margin></system-margins></system-layout>
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
        >>> XPBase.dump(mxSl)
        <staff-layout number="1"><staff-distance>40.0</staff-distance></staff-layout>
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

class ScoreExporter(XMLExporterBase):
    '''
    Convert a Score (or outer stream with .parts) into
    a musicxml Element.
    '''
    def __init__(self, score=None):
        super(ScoreExporter, self).__init__()
        if score is None:
            # should not be done this way.
            self.stream = stream.Score()
        else:
            self.stream = score
        
        self.musicxmlVersion = "3.0"
        self.xmlRoot = Element('score-partwise')
        
        self.spannerBundle = None
        self.meterStream = None
        self.scoreLayouts = None
        self.firstScoreLayout = None
        self.textBoxes = None
        self.highestTime = 0
        
        self.refStreamOrTimeRange = [0, self.highestTime]

        self.mxPartList = []

        self.instrumentList = []
        self.midiChannelList = []
        
        self.parts = []

    def emptyObjectToMx(self):
        pass
    
    def scorePreliminaries(self):
        '''
        Populate the exporter object with
        `meterStream`, `scoreLayouts`, `spannerBundle`, and `textBoxes`
        '''
        self.setScoreLayouts()
        self.setMeterStream()
        self.setPartsAndRefStream()
        # get all text boxes
        self.textBoxes = self.stream.flat.getElementsByClass('TextBox')
    
        # we need independent sub-stream elements to shift in presentation
        self.highestTime = 0 # redundant, but set here.

        if self.spannerBundle is None:
            self.spannerBundle = self.stream.spannerBundle

    def setPartsAndRefStream(self):
        s = self.stream
        #environLocal.printDebug('streamToMx(): interpreting multipart')
        streamOfStreams = s.getElementsByClass('Stream')
        for innerStream in streamOfStreams:
            # may need to copy element here
            # apply this streams offset to elements
            innerStream.transferOffsetToElements()
            ht = innerStream.highestTime
            if ht > self.highestTime:
                self.highestTime = ht
        self.refStreamOrTimeRange = [0, self.highestTime]
        self.parts = streamOfStreams

    def setMeterStream(self):
        '''
        sets `self.meterStream` or uses a default.
        '''
        s = self.stream
        # search context probably should always be True here
        # to search container first, we need a non-flat version
        # searching a flattened version, we will get contained and non-container
        # this meter  stream is passed to makeNotation()
        meterStream = s.getTimeSignatures(searchContext=False,
                        sortByCreationTime=False, returnDefault=False)
        #environLocal.printDebug(['streamToMx: post meterStream search', meterStream, meterStream[0]])
        if len(meterStream) == 0:
            # note: this will return a default if no meters are found
            meterStream = s.flat.getTimeSignatures(searchContext=False,
                        sortByCreationTime=True, returnDefault=True)

        
    def setScoreLayouts(self):
        '''
        sets `self.scoreLayouts` and `self.firstScoreLayout`
        '''
        s = self.stream
        scoreLayouts = s.getElementsByClass('ScoreLayout')
        if len(scoreLayouts) > 0:
            scoreLayout = scoreLayouts[0]
        else:
            scoreLayout = None
        self.scoreLayouts = scoreLayouts
        self.firstScoreLayout = scoreLayout
    
    def scoreToXml(self):
        s = self.stream
        if len(s) == 0:
            return self.emptyObjectToMx()

        self.scorePreliminaries()    

        if s.hasPartLikeStreams():
            self.parsePartlikeScore()
        else:
            self.parseFlatScore()
            
        self.postPartProcess()
        
    def parsePartlikeScore(self):
        # would like to do something like this but cannot
        # replace object inside of the stream
        for innerStream in self.parts:
            innerStream.makeRests(self.refStreamOrTimeRange, inPlace=True)

        count = 0
        for innerStream in self.parts:
            count += 1
            if count > len(self.parts):
                raise ToMxObjectsException('infinite stream encountered')
            self.parseInnerStreamInstruments(innerStream)

            pp = PartExporter(innerStream, parent=self)
            mxPart = pp.parse()
            self.mxPartList.append(mxPart)
    
    def parseFlatScore(self):
        s = self.stream
        pp = PartExporter(s, parent=self)
        mxPart = pp.parse()
        self.mxPartList.append(mxPart)

    def parseInnerStreamInstruments(self, p):
        # only things that can be treated as parts are in finalStream
        # get a default instrument if not assigned
        instStream = p.getInstruments(returnDefault=True)
        inst = instStream[0] # store first, as handled differently
        instIdList = [x.partId for x in self.instrumentList]

        if inst.partId in instIdList: # must have unique ids 
            inst.partIdRandomize() # set new random id

        if (inst.midiChannel == None or
            inst.midiChannel in self.midiChannelList):
            try:
                inst.autoAssignMidiChannel(usedChannels=self.midiChannelList)
            except exceptions21.InstrumentException as e:
                environLocal.warn(str(e))
        self.midiChannelList.append(inst.midiChannel)
        #environLocal.printDebug(['midiChannel list', self.midiChannelList])

        # add to list for checking on next part
        self.instrumentList.append(inst)
        # force this instrument into this part
        # meterStream is only used here if there are no measures
        # defined in this part


    def postPartProcess(self):
        self.setMxScoreDefaults()
        self.setPartList()
        # addition of parts must simply be in the same order as above
        for mxScorePart, mxPart, p in mxComponents:
            mxScore.append(mxPart) # mxParts go on component list


    def setPartList(self):
        spannerBundle = self.spannerBundle
        
        mxPartList = mxObjects.PartList()
        # mxComponents is just a list 
        # returns a spanner bundle
        staffGroups = spannerBundle.getByClass('StaffGroup')
        #environLocal.printDebug(['got staff groups', staffGroups])
    
        # first, find which parts are start/end of partGroups
        partGroupIndexRef = {} # have id be key
        partGroupIndex = 1 # start by 1 by convetion
        for mxScorePart, mxPart, p in mxComponents:
            # check for first
            for sg in staffGroups:
                if sg.isFirst(p):
                    mxPartGroup = configureMxPartGroupFromStaffGroup(sg)
                    mxPartGroup.set('type', 'start')
                    mxPartGroup.set('number', partGroupIndex)
                    # assign the spanner in the dictionary
                    partGroupIndexRef[partGroupIndex] = sg
                    partGroupIndex += 1 # increment for next usage
                    mxPartList.append(mxPartGroup)
            # add score part
            mxPartList.append(mxScorePart)
            # check for last
            activeIndex = None
            for sg in staffGroups:
                if sg.isLast(p):
                    # find the spanner in the dictionary already-assigned
                    for key, value in partGroupIndexRef.items():
                        if value is sg:
                            activeIndex = key
                            break
                    mxPartGroup = mxObjects.PartGroup()
                    mxPartGroup.set('type', 'stop')
                    if activeIndex is not None:
                        mxPartGroup.set('number', activeIndex)
                    mxPartList.append(mxPartGroup)
        # set the mxPartList
        mxScore.set('partList', mxPartList)
        return mxScore
    

    def setMxScoreDefaults(self):
        s = self.stream

        # create score and part list
        # try to get mxScore from lead metadata first
        if s.metadata != None:
            self.parseMetadata(s.metadata) # returns an mx score
    
        # add text boxes
        for tb in self.textBoxes: # a stream of text boxes
            mxScore.creditList.append(textBoxToMxCredit(tb))
    
        mxScoreDefault = mxObjects.Score()
        mxScoreDefault.setDefaults()
        mxIdDefault = mxObjects.Identification()
        mxIdDefault.setDefaults() # will create a composer
        mxScoreDefault.set('identification', mxIdDefault)
    
        # merge metadata derived with default created
        mxScore = mxScore.merge(mxScoreDefault, returnDeepcopy=False)
        # get score defaults if any:
        if self.firstScoreLayout is None:
            from music21 import layout
            scoreLayout = layout.ScoreLayout()
            scoreLayout.scalingMillimeters = defaults.scalingMillimeters
            scoreLayout.scalingTenths = defaults.scalingTenths
    
        mxDefaults = scoreLayoutToMxDefaults(scoreLayout)
        mxScore.defaultsObj = mxDefaults
    
    
        addSupportsToMxScore(s, mxScore)
    

    
#-------------------------------------------------------------------------------
    
    
class PartExporter(XMLExporterBase):
    
    def __init__(self, partObj=None, parent=None):
        super(PartExporter, self).__init__()
        self.stream = partObj
        self.parent = parent # ScoreParser
        self.xmlRoot = Element('part')
        
        if parent is None:
            self.spannerBundle = spanner.SpannerBundle()
            self.meterStream = stream.Stream()
            self.instrumentStream = stream.Stream()
            self.instrumentObj = self.stream.getInstrument()
            self.instrumentStream.insert(0, self.instrumentObj)
            self.refStreamOrTimeRange = [0, 0]
        else:
            self.spannerBundle = parent.spannerBundle
            self.meterStream = parent.meterStream
            self.instrumentStream = parent.instrumentStream
            self.instrumentObj = self.instrumentStream[0]
            self.refStreamOrTimeRange = parent.refStreamOrTimeRange

    def parse(self):
        if self.instrumentObj.partId == None:
            self.instrumentObj.partIdRandomize()

#-------------------------------------------------------------------------------

class MeasureExporter(XMLExporterBase):
    classesToMethods = OrderedDict(
               [('Note', 'noteToXml'),
                ('ChordSymbol', 'chordSymbolToXml'),
                ('Chord', 'chordToXml'),
                ('Rest', 'restToXml'),
                # Skipping unpitched for now
                ('Dynamic', 'dynamicToXml'),
                ('Segno', 'segnoToXml'),
                ('Coda', 'codaToXml'),
                ('MetronomeMark', 'tempoIndicationToXml'),
                ('MetricModulation', 'tempoIndicationToXml'),
                ('TextEpxression', 'textExpressionToXml'),
                ('RepeatEpxression', 'textExpressionToXml'),
                ('Clef', 'midmeasureClefToXml')
               ])
    
    
    def __init__(self, measureObj=None, parent=None):
        super(MeasureExporter, self).__init__()
        if measureObj is not None:
            self.stream = measureObj
        else: # no point, but...
            self.stream = stream.Measure()
        
        self.parent = parent # PartExporter
        self.xmlRoot = Element('measure')
        self.currentDivisions = defaults.divisionsPerQuarter

        # TODO: allow for mid-measure transposition changes.
        self.transpositionInterval = None
        self.mxTranspose = None
        self.measureOffsetStart = 0.0
        self.offsetInMeasure = 0.0
        self.currentVoiceId = None
        
        self.rbSpanners = [] # rightBarline repeat spanners
        
        if parent is None:
            self.spannerBundle = spanner.SpannerBundle()
        else:
            self.spannerBundle = parent.spannerBundle

        self.objectSpannerBundle = self.spannerBundle # will change for each element.

    def parse(self):
        self.setTranspose()
        self.setRbSpanners()
        self.setMxAttributes()
        self.setMxPrint()
        self.setMxAttributesObject()
        self.setLeftBarline()
        self.mainElementsParse()
        self.setRightBarline()
        return self.xmlRoot
        
    def mainElementsParse(self):
        m = self.stream
        # need to handle objects in order when creating musicxml 
        # we thus assume that objects are sorted here

        if m.hasVoices():
            # TODO... Voice not Stream
            nonVoiceMeasureItems = m.getElementsNotOfClass('Stream')
        else:
            nonVoiceMeasureItems = m # use self.

        for v in m.voices:
            # Assumes voices are flat...
            self.parseFlatElements(v)
        
        self.parseFlatElements(nonVoiceMeasureItems)
    
    def parseFlatElements(self, m):
        '''
        m here can be a Measure or Voice, but
        flat...
        '''
        root = self.xmlRoot
        divisions = self.currentDivisions
        self.offsetInMeasure = 0.0
        if 'Voice' in m.classes:
            voiceId = m.id
        else:
            voiceId = None
        
        self.currentVoiceId = voiceId
        for obj in m:
            self.parseOneElement(obj, m)
        
        if voiceId is not None:
            mxBackup = Element('backup')
            mxDuration = SubElement(mxBackup, 'duration')
            mxDuration.text = str(int(divisions * self.offsetInMeasure))
            # TODO: editorial
            root.append(mxBackup)
        self.currentVoiceId = None

    def parseOneElement(self, obj, m):
        '''
        parse one element completely and add it to xmlRoot, updating
        offsetInMeasure, etc.
        
        m is either a measure or a voice object.
        '''
        root = self.xmlRoot
        self.objectSpannerBundle = self.spannerBundle.getBySpannedElement(obj)
        preList, postList = self.prePostObjectSpanners(obj)
        
        for sp in preList: # directions that precede the element
            root.append(sp)
            
        classes = m.classes
        if 'GeneralNote' in classes:
            self.offsetInMeasure += obj.duration.quarterLength

        # split at durations...
        if 'GeneralNote' in classes and obj.duration.type == 'complex':
            objList = obj.splitAtDurations()
        else:
            objList = [obj]
        
        
        for className, methName in self.classesToMethods:
            if className in classes:
                meth = getattr(self, methName)
                for o in objList:
                    meth(o)
                break
            environLocal.printDebug(['did not convert object', obj])
            # TODO: print something for non-converted...

        for sp in postList: # directions that follow the element
            root.append(sp)

    def prePostObjectSpanners(self, target):
        '''
        return two lists or empty tuples: 
        (1) spanners related to the object that should appear before the object
        to the <measure> tag. (2) spanners related to the object that should appear after the
        object in the measure tag.
        '''
        def getProc(su, target):
            if len(su) == 1: # have a one element wedge
                proc = ('first', 'last')
            else:
                if su.isFirst(target):
                    proc = ('first',)
                elif su.isLast(target):
                    proc = ('last',)
                else:
                    proc = ()
            return proc
        
        spannerBundle = self.objectSpannerBundle
        if len(spannerBundle) == 0:
            return (), ()

        preList = []
        postList = []
        
        # number, type is assumed; 
        # tuple: first is the elementType, 
        #        second: tuple of parameters to set,
        #        third: tuple of mappings: first musicxml attribute, then m21.
        paramsSet = {'Ottava': ('octave-shift', ('size',), ()),
                     # TODO: attrGroup: dashed-formatting, print-style
                     'DynamicWedge': ('wedge', ('spread',), ()),
                     # TODO: niente, attrGroups: line-type, dashed-formatting, position, color
                     'Line': ('bracket', ('line-end', 'end-length'), (('line-type', 'lineType'),))
                     # TODO: dashes???
                     }

        for m21spannerClass, infoTuple in paramsSet.items():
            mxtag, parameterSet, attributeSet = infoTuple
            for su in spannerBundle.getByClass(m21spannerClass):
                for posSub in getProc(su, target):
                    # create new tag
                    mxElement = Element(mxtag)
                    mxElement.set('number', str(su.idLocal))
                    # set attributes by number...
                    for mxAttr, m21Attr in attributeSet:
                        try:
                            v = getattr(target, m21Attr)
                        except AttributeError:
                            continue
                        if v is None:
                            continue
                        mxElement.set(mxAttr, str(m21Attr))
                    if posSub == 'first':
                        pmtrs = su.getStartParameters()
                    elif posSub == 'last':
                        pmtrs = su.getEndParameters()
                    else:
                        pmtrs = None
                        
                    if pmtrs is not None:
                        mxElement.set('type', pmtrs['type'])
                        for attrName in parameterSet:
                            if pmtrs[attrName] is not None:
                                mxElement.set(attrName, pmtrs[attrName])
                    mxDirection = Element('direction')
                    if su.placement is not None:
                        mxDirection.set('placement', str(su.placement))
                    mxDirectionType = SubElement(mxDirection, 'direction-type')
                    mxDirectionType.append(mxElement)
                    
                    if posSub == 'first':
                        preList.append(mxDirection)
                    else:
                        postList.append(mxDirection)
        
        return preList, postList
    
    def objectAttachedSpannersToNotations(self, obj):
        '''
        return a list of <notations> from spanners related to the object that should appear 
        in the notations tag (slurs, slides, etc.)
        '''
        notations = []
        sb = self.objectSpannerBundle
        if len(sb) == 0:
            return notations

        ornaments = []
        
        for su in sb.getByClass('Slur'):
            mxSlur = Element('slur')
            if su.isFirst(obj):
                mxSlur.set('type', 'start')
            elif su.isLast(obj):
                mxSlur.set('type', 'stop')
            else:
                continue # do not put a notation on mid-slur notes.
            mxSlur.set('number', str(su.idLocal))
            if su.placement is not None:
                mxSlur.set('placement', str(su.placement))
            notations.append(mxSlur)

        for su in sb.getByClass('Glissando'):
            mxGlissando = Element('glissando')
            mxGlissando.set('number', str(su.idLocal))
            if su.lineType is not None:
                mxGlissando.set('line-type', str(su.lineType))
            # is this note first in this spanner?
            if su.isFirst(obj):
                if su.label is not None:
                    mxGlissando.text = str(su.label)
                mxGlissando.set('type', 'start')
            elif su.isLast(obj):
                mxGlissando.set('type', 'stop')
            else:
                continue # do not put a notation on mid-gliss notes.
            # placement???
            notations.append(mxGlissando)

        # These add to Ornaments...
        
        for su in sb.getByClass('TremoloSpanner'):
            mxTrem = Element('tremolo')
            mxTrem.text = str(su.numberOfMarks)
            if su.isFirst(obj):
                mxTrem.set('type', 'start')
            elif su.isLast(obj):
                mxTrem.set('type', 'stop')
            else:
                # this is always an error for tremolos
                environLocal.printDebug(['spanner w/ a component that is neither a start nor an end.', su, obj])
            if su.placement is not None:
                mxTrem.set('placement', str(su.placement))
            # Tremolos get in a separate ornaments tag...
            ornaments.append(mxTrem)

        for su in sb.getByClass('TrillExtension'):
            mxWavyLine = Element('wavy-line')
            mxWavyLine.set('number', str(su.idLocal))
            # is this note first in this spanner?
            if su.isFirst(obj):
                mxWavyLine.set('type', 'start')
            elif su.isLast(obj):
                mxWavyLine.set('type', 'stop')
            else:
                continue # do not put a wavy-line tag on mid-trill notes
            if su.placement is not None:
                mxWavyLine.set('placement', su.placement)
            ornaments.append(mxWavyLine)



        if len(ornaments) > 0:
            mxOrn = Element('ornaments')
            for orn in ornaments:
                mxOrn.append(orn)
            notations.append(mxOrn)

        return notations

    def noteToXml(self, n, addChordTag=False):
        '''
        Translate a music21 :class:`~music21.note.Note` into a
        list of :class:`~music21.musicxml.mxObjects.Note` objects.
    
        Because of "complex" durations, the number of 
        `musicxml.mxObjects.Note` objects could be more than one.
    
        Note that, some note-attached spanners, such 
        as octave shifts, produce direction (and direction types) 
        in this method.
        
        >>> n = note.Note('D#5')
        >>> n.quarterLength = 3
        >>> MEX = musicxml.m21ToXML.MeasureExporter()
        >>> mxNote = MEX.noteToXml(n)
        >>> MEX.dump(mxNote)
        <note><pitch><step>D</step><alter>1</alter><octave>5</octave></pitch><duration>30240</duration><type>half</type><dot /><accidental>sharp</accidental></note>
         
        TODO: Test with spanners...
        '''
        # TODO: attrGroup x-position
        # TODO: attrGroup font
        # TODO: attr: dynamics
        # TODO: attr: end-dynamics
        # TODO: attr: attack
        # TODO: attr: release
        # TODO: attr: time-only
        mxNote = Element('note')
        if n.duration.isGrace is True:
            SubElement(mxNote, 'grace')

        # TODO: cue...
        if n.color is not None:
            mxNote.set('color', normalizeColor(n.color))
        if n.hideObjectOnPrint is True:
            mxNote.set('print-object', 'no')
            mxNote.set('print-spacing', 'yes')
            
        for art in n.articulations:
            if 'Pizzicato' in art.classes:
                mxNote.set('pizzicato', 'yes')
        
        if addChordTag:
            SubElement(mxNote, 'chord')
        
        if hasattr(n, 'pitch'):
            mxPitch = self.pitchToXml(n.pitch)
            mxNote.append(mxPitch)
        else: 
            # assume rest until unpitched works
            # TODO: unpitched
            SubElement(mxNote, 'rest')

        if n.duration.isGrace is not True:
            mxDuration = self.durationXml(n.duration)
            mxNote.append(mxDuration)
            # divisions only
        # TODO: skip if cue:
        if n.tie is not None:
            mxTieList = self.tieToXmlTie(n.tie)
            for t in mxTieList:
                mxNote.append(t)
        
            
        # TODO: instrument
        # TODO: editorial-voice
        mxType = Element('type')
        mxType.text = typeToMusicXMLType(n.duration.type)
        mxNote.append(mxType)
        
        for _ in range(n.duration.dots):
            SubElement(mxNote, 'dot')
            # TODO: dot placement...
        if (n.pitch.accidental is not None and 
                n.pitch.accidental.displayStatus in (True, None)):
            mxAccidental = accidentalToMx(n.pitch.accidental)
            mxNote.append(mxAccidental)
        if len(n.duration.tuplets) > 0:
            for tup in n.duration.tuplets:
                mxTimeModification = self.tupletToTimeModification(tup)
                mxNote.append(mxTimeModification)
        # TODO: stem
        if (n.notehead != 'normal' or n.noteheadFill is not None or
                n.color not in (None, '')):
            mxNotehead = self.noteheadToXml(n)
            mxNote.append(mxNotehead)
        # TODO: notehead-text
        # TODO: staff
        # TODO: beam
        if hasattr(n, 'beams') and n.beams:
            nBeamsList = self.beamsToXml(n.beams)
            for mxB in nBeamsList:
                mxNote.append(mxB)
    
        mxNotationsList = self.noteToNotations(n)
        for mxN in mxNotationsList:
            mxNote.append(mxN)

        for lyricObj in n.lyrics:
            mxNote.append(self.lyricToXml(lyricObj))
        # TODO: play
        self.xmlRoot.append(mxNote)
        return mxNote

    def restToXml(self, r):
        pass

    def chordToXml(self, c):
        pass

            
    def durationXml(self, dur):
        '''
        Convert a duration.Duration object to a <duration> tag using self.currentDivisions
        
        >>> d = duration.Duration(1.5)
        >>> MEX = musicxml.m21ToXML.MeasureExporter()
        >>> MEX.currentDivisions = 10
        >>> mxDuration = MEX.durationXml(d)
        >>> MEX.dump(mxDuration)
        <duration>15</duration>
        '''
        mxDuration = Element('duration')
        mxDuration.text = str(int(self.currentDivisions * dur.quarterLength))
        return mxDuration
    
    def pitchToXml(self, p):
        mxPitch = Element('pitch')
        _setTagTextFromAttribute(p, mxPitch, 'step')
        if p.accidental is not None:
            mxAlter = SubElement(mxPitch, 'alter')
            mxAlter.text = str(common.numToIntOrFloat(p.accidental.alter))
        _setTagTextFromAttribute(p, mxPitch, 'octave', 'implicitOctave')
        return mxPitch
    
    def tupletToTimeModification(self, tup):
        mxTimeModification = Element('time-modification')
        _setTagTextFromAttribute(tup, mxTimeModification, 'actual-notes', 'numberNotesActual')
        _setTagTextFromAttribute(tup, mxTimeModification, 'normal-notes', 'numberNotesNormal')
        mxNormalType = SubElement(mxTimeModification, 'normal-type')
        mxNormalType.text = typeToMusicXMLType(tup.durationNormal.type)
        if tup.durationNormal.dots > 0:
            for i in range(tup.durationNormal.dots):
                SubElement(mxTimeModification, 'normal-dot')
                
        return mxTimeModification
    
    def noteheadToXml(self, n):
        mxNotehead = Element('notehead')
        nh = n.notehead
        if nh is None:
            nh = 'none'
        mxNotehead.text = nh 
        setb = _setAttributeFromAttribute
        setb(n, mxNotehead, 'filled', 'noteheadFill', transform=xmlObjects.booleanToYesNo)
        setb(n, mxNotehead, 'parentheses', 'noteheadParenthesis', transform=xmlObjects.booleanToYesNo)
        # TODO: font
        if n.color not in (None, ''):
            color = normalizeColor(n.color)
            mxNotehead.set('color', color)
        return mxNotehead
    
    def noteToNotations(self, n):
        '''
        Take information from .expressions,
        .articulations, and spanners to
        make the <notations> tag for a note.
        '''
        mxArticulations = None
        mxTechnicalMark = None
        mxOrnaments = None

        notations = []

        for expObj in n.expressions:
            mxExpression = self.expressionToXml(expObj)
            if mxExpression is None:
                # TODO: should not!
                continue
            if 'Ornament' in expObj.classes:
                if mxOrnaments is None:
                    mxOrnaments = Element('ornaments')
                mxOrnaments.append(mxExpression)
            else:
                notations.append(mxExpression)

        for artObj in n.articulations:
            if 'TechnicalIndication' in artObj.classes:
                if mxTechnicalMark is None:
                    mxTechnicalMark = Element('technical')
                mxTechnicalMark.append(self.articulationToXmlTechnical(artObj))
            else:
                if mxArticulations is None:
                    mxArticulations = Element('articulations')
                mxArticulations.append(self.articulationToXmlArticulation(artObj))
        
        # TODO: attrGroup: print-object (for individual notations)
        # TODO: editorial (hard! -- requires parsing again in order...)
        
        # <tied>
        if n.tie is not None:
            tiedList = self.tieToXmlTied(n.tie)
            notations.extend(tiedList)
        # <tuplet>
        for tup in n.duration.tuplets:
            tupTagList = self.tupletToXmlTuplet(tup)
            notations.extend(tupTagList)

        notations.extend(self.objectAttachedSpannersToNotations(n))
        # TODO: slur            
        # TDOO: glissando
        # TODO: slide
                
        for x in (mxArticulations, 
                  mxTechnicalMark, 
                  mxOrnaments):
            if x is not None and len(x) > 0:
                notations.append(x)    

        # TODO: dynamics in notations
        # TODO: arpeggiate
        # TODO: non-arpeggiate
        # TODO: accidental-mark
        # TODO: other-notation
        
        return notations

    def tieToXmlTied(self, t):
        '''
        In musicxml, a tie is represented in sound
        by the tie tag (near the pitch object), and
        the <tied> tag in notations.  This
        creates the <tied> tag.
        
        Returns a list since a music21
        "continue" tie type needs two tags
        in musicxml.  List may be empty
        if tie.style == "hidden"
        '''
        if t.style == 'hidden':
            return []

        mxTiedList = []
        if t.type == 'continue':
            musicxmlTieType = 'stop'
        else:
            musicxmlTieType = t.type
        
        mxTied = Element('tied')
        mxTied.set('type', musicxmlTieType)
        mxTiedList.append(mxTied)
        
        if t.type == 'continue':            
            mxTied = Element('tied')
            mxTied.set('type', 'stop')
            mxTiedList.append(mxTied)
        
        # TODO: attr: number (distinguishing ties on enharmonics)
        # TODO: attrGroup: line-type
        # TODO: attrGroup: dashed-formatting
        # TODO: attrGroup: position
        # TODO: attrGroup: placement
        # TODO: attrGroup: orientation
        # TODO: attrGroup: bezier
        # TODO: attrGroup: color
        
        return mxTiedList

    def tupletToXmlTuplet(self, tuplet):
        '''
        In musicxml, a tuplet is represented by
        a timeModification and visually by the
        <notations><tuplet> tag.  This method
        creates the latter.

        Returns a list of them because a 
        startStop type tuplet needs two tuplet
        brackets.

        TODO: make sure something happens if
        makeTupletBrackets is not set.
        '''
        if tuplet.type in (None, ''):
            return []
        
        if tuplet.type not in ('start', 'stop', 'startStop'):
            raise ToMxObjectsException("Cannot create music XML from a tuplet of type " + tuplet.type)

        if tuplet.type == 'startStop': # need two musicxml
            localType = ['start', 'stop']
        else:
            localType = [tuplet.type] # place in list

        retList = []
        
        # TODO: tuplet-actual different from time-modification
        # TODO: tuplet-normal
        # TODO: attr: show-type
        # TODO: attrGroup: position
        
        for tupletType in localType:
            mxTuplet = Element('tuplet')
            mxTuplet.set('type', tupletType)
            # only provide other parameters if this tuplet is a start
            if tupletType == 'start':
                mxTuplet.set('bracket', 
                             xmlObjects.booleanToYesNo(tuplet.bracket))
                if tuplet.placement is not None:
                    mxTuplet.set('placement', tuplet.placement)
                if tuplet.tupletActualShow == 'none':
                    mxTuplet.set('show-number', 'none')
            retList.append(mxTuplet)
        return retList

    def expressionToXml(self, expression):
        '''
        Convert a music21 Expression (expression or ornament)
        to a musicxml tag; 
        return None if no conversion is possible.
        '''
        mapping = OrderedDict([
                   ('Trill', 'trill-mark'),
                   # TODO: delayed-inverted-turn
                   # TODO: vertical-turn
                   # TODO: 'delayed-turn'
                   ('InvertedTurn', 'inverted-turn'),
                   # last as others are subclasses
                   ('Turn', 'turn'), 
                   ('InvertedMordent', 'inverted-mordent'),
                   ('Mordent', 'mordent'),
                   ('Shake', 'shake'),
                   ('Schleifer', 'schleifer'),
                   # TODO: 'accidental-mark'
                   ('Ornament', 'other-ornament'),
                   # non-ornaments...
                   ('Fermata', 'fermata'),
                   ('Tremolo', 'tremolo'), # non-spanner
                   ])
        mx = None
        classes = expression.classes
        for k, v in mapping.items():
            if k in classes:
                mx = Element(v)
        if mx is None:
            environLocal.printDebug(['no musicxml conversion for:', expression])
            return 
        
        # TODO: print-style
        # TODO: trill-sound
        if expression.placement is not None:
            mx.set('placement', expression.placement)
        
        if 'Tremolo' in classes:
            mx.set('type', 'single')
            mx.text = str(expression.numberOfMarks)
        
        return mx
        
        
        
    def articulationToXmlArticulation(self, articulationMark):
        '''
        Returns a class (mxArticulationMark) that represents the
        MusicXML structure of an articulation mark.
    
        
        >>> a = articulations.Accent()
        >>> a.placement = 'below'
        >>> mxArticulationMark = musicxml.toMxObjects.articulationToMxArticulation(a)
        >>> mxArticulationMark
        <accent placement=below>
        '''
        # TODO: OrderedDict
        # these articulations have extra information
        # TODO: strong-accent
        # TODO: scoop/plop/doit/falloff - empty-line
        # TODO: breath-mark
        # TODO: other-articulation
        
        musicXMLArticulationName = None
        for c in xmlObjects.ARTICULATION_MARKS_REV:
            if isinstance(articulationMark, c):
                musicXMLArticulationName = xmlObjects.ARTICULATION_MARKS_REV[c]
        if musicXMLArticulationName is None:
            raise ToMxObjectsException("Cannot translate %s to musicxml" % articulationMark)
        mxArticulationMark = Element(musicXMLArticulationName)
        mxArticulationMark.set('placement', articulationMark.placement)
        #mxArticulations.append(mxArticulationMark)
        return mxArticulationMark
    
    def articulationToXmlTechnical(self, articulationMark):
        '''
        Returns a tag that represents the
        MusicXML structure of an articulation mark that is primarily a TechnicalIndication.
        
        >>> a = articulations.UpBow()
        >>> a.placement = 'below'
        >>> mxTechnicalMark = musicxml.toMxObjects.articulationToMxTechnical(a)
        >>> mxTechnicalMark
        <up-bow placement=below>
        '''
        # TODO: OrderedDict to make Technical Indication work...
        # these technical have extra information
        # TODO: handbell
        # TODO: arrow
        # TODO: hole
        # TODO: heel-toe
        # TODO: bend
        # TODO: pull-off/hammer-on
        # TODO: string
        # TODO: fret
        # TODO: fingering
        # TODO: harmonic
        
        musicXMLTechnicalName = None
        for c in xmlObjects.TECHNICAL_MARKS_REV:
            if isinstance(articulationMark, c):
                musicXMLTechnicalName = xmlObjects.TECHNICAL_MARKS_REV[c]
                break
        if musicXMLTechnicalName is None:
            raise ToMxObjectsException("Cannot translate technical indication %s to musicxml" % articulationMark)
        mxTechnicalMark = Element(musicXMLTechnicalName)
        mxTechnicalMark.set('placement', articulationMark.placement)
        #mxArticulations.append(mxArticulationMark)
        return mxTechnicalMark
    
    
    def chordSymbolToXml(self, cs):
        pass
    
    def dynamicToXml(self, dyn):
        pass
    
    def segnoToXml(self, segno):
        pass
    
    def codaToXml(self, coda):
        pass
    
    def tempoIndicationToXml(self, ti):
        pass
    
    def textExpressionToXml(self, te):
        pass
    
    def midmeasureClefToXml(self, clefObj):
        pass
    
    #------------------------------
    # note helpers...
    def lyricToXml(self, l):
        '''
        Translate a music21 :class:`~music21.note.Lyric` object 
        to a <lyric> tag.
        '''
        mxLyric = Element('lyric')
        _setTagTextFromAttribute(l, mxLyric, 'syllabic')
        _setTagTextFromAttribute(l, mxLyric, 'text')
        # TODO: elision
        # TODO: more syllabic
        # TODO: more text
        # TODO: extend
        # TODO: laughing
        # TODO: humming
        # TODO: end-line
        # TODO: end-paragraph
        # TODO: editorial
        if l.identifier is not None:
            mxLyric.set('number', l.identifier)
        else:
            mxLyric.set('number', str(l.number))
        # TODO: attr: name - alternate for lyric -- make identifier?
        # TODO: attrGroup: justify
        # TODO: attrGroup: position
        # TODO: attrGroup: placement
        # TODO: attrGroup: color
        # TODO: attrGroup: print-object
        return mxLyric
    
    def beamsToXml(self, beams):
        '''
        Returns a list of <beam> tags 
        from a :class:`~music21.beam.Beams` object
    
        
        >>> a = beam.Beams()
        >>> a.fill(2, type='start')
        >>> mxBeamList = musicxml.toMxObjects.beamsToMx(a)
        >>> len(mxBeamList)
        2
        >>> mxBeamList[0]
        <beam number=1 charData=begin>
        >>> mxBeamList[1]
        <beam number=2 charData=begin>
        '''
        mxBeamList = []
        for beamObj in beams.beamsList:
            mxBeamList.append(self.beamToXml(beamObj))
        return mxBeamList

    def beamToXml(self, beamObject):
        '''
    
        
        >>> a = beam.Beam()
        >>> a.type = 'start'
        >>> a.number = 1
        >>> b = musicxml.toMxObjects.beamToMx(a)
        >>> b.get('charData')
        'begin'
        >>> b.get('number')
        1
    
        >>> a.type = 'continue'
        >>> b = musicxml.toMxObjects.beamToMx(a)
        >>> b.get('charData')
        'continue'
    
        >>> a.type = 'stop'
        >>> b = musicxml.toMxObjects.beamToMx(a)
        >>> b
        <beam number=1 charData=end>
        >>> b.get('charData')
        'end'
    
        >>> a.type = 'partial'
        >>> a.direction = 'left'
        >>> b = musicxml.toMxObjects.beamToMx(a)
        >>> b.get('charData')
        'backward hook'
    
        >>> a.direction = 'right'
        >>> b = musicxml.toMxObjects.beamToMx(a)
        >>> b.get('charData')
        'forward hook'
    
        >>> a.direction = None
        >>> b = musicxml.toMxObjects.beamToMx(a)
        Traceback (most recent call last):
        ToMxObjectsException: partial beam defined without a proper direction set (set to None)
    
        >>> a.type = 'crazy'
        >>> b = musicxml.toMxObjects.beamToMx(a)
        Traceback (most recent call last):
        ToMxObjectsException: unexpected beam type encountered (crazy)
        '''
        mxBeam = Element('beam')
        if beamObject.type == 'start':
            mxBeam.text = 'begin'
        elif beamObject.type == 'continue':
            mxBeam.text = 'continue'
        elif beamObject.type == 'stop':
            mxBeam.text = 'end'
        elif beamObject.type == 'partial':
            if beamObject.direction == 'left':
                mxBeam.text = 'backward hook'
            elif beamObject.direction == 'right':
                mxBeam.text = 'forward hook'
            else:
                raise ToMxObjectsException('partial beam defined without a proper direction set (set to %s)' % beamObject.direction)
        else:
            raise ToMxObjectsException('unexpected beam type encountered (%s)' % beamObject.type)
    
        mxBeam.set('number', beamObject.number)
        # not todo: repeater (deprecated)
        # TODO: attr: fan
        # TODO: attr: color group
        return mxBeam

    
    def setRightBarline(self):        
        m = self.stream
        rbSpanners = self.rbSpanners
        rightBarline = self.stream.rightBarline
        if (rightBarline is None and 
                (len(rbSpanners) == 0 or not rbSpanners[0].isLast(m))):
            return
        self.setBarline(rightBarline, 'right')
        
    def setLeftBarline(self):
        m = self.stream
        rbSpanners = self.rbSpanners
        leftBarline = self.stream.leftBarline
        if (leftBarline is None and
                (len(rbSpanners) == 0 or not rbSpanners[0].isFirst(m))):
            return
        self.setBarline(leftBarline, 'left')

    def setBarline(self, barline, position):
        '''
        sets either a left or right barline from a 
        bar.Barline() object or bar.Repeat() object        
        '''        
        if barline is None:
            mxBarline = Element('barline')
        else:
            mxBarline = self.barlineToXml(barline)
        
        mxBarline.set('location', position)
        # TODO: editorial
        # TODO: wavy-line
        # TODO: segno
        # TODO: coda
        # TODO: fermata
        
        if len(self.rbSpanners) > 0: # and self.rbSpanners[0].isFirst(m)???
            mxEnding = Element('ending')
            if position == 'left':
                endingType = 'start'
            else:
                endingType = 'stop'
                mxEnding.set('number', str(self.rbSpanners[0].number))
            mxEnding.set('type', endingType)
            mxBarline.append(mxEnding) # make sure it is after fermata but before repeat.

        if 'Repeat' in barline.classes:
            mxRepeat = self.repeatToXml(barline)
            mxBarline.append(mxRepeat)
        
        # TODO: attr: segno
        # TODO: attr: coda
        # TODO: attr: divisions
        
        self.xmlRoot.append(mxBarline)
        return mxBarline

    def barlineToXml(self, barObject):
        '''
        Translate a music21 bar.Bar object to an mxBar
        while making two substitutions: double -> light-light
        and final -> light-heavy as shown below.
        
        >>> b = bar.Barline('final')
        >>> MEX = musicxml.m21ToXML.MeasureExporter()
        >>> mxBarline = MEX.barlineToXml(b)
        >>> MEX.dump(mxBarline)
        <barline><bar-style>light-heavy</bar-style></barline>
        
        >>> b.location = 'right'
        >>> mxBarline = MEX.barlineToXml(b)
        >>> MEX.dump(mxBarline)
        <barline location="right"><bar-style>light-heavy</bar-style></barline>        
        '''
        mxBarline = Element('barline')
        mxBarStyle = SubElement(mxBarline, 'bar-style')
        mxBarStyle.text = barObject.musicXMLBarStyle
        # TODO: mxBarStyle attr: color
        if barObject.location is not None:
            mxBarline.set('location', barObject.location)
        return mxBarline

    def repeatToXml(self, r):
        '''
        returns a <repeat> tag from a barline object.

        >>> b = bar.Repeat(direction='end')
        >>> MEX = musicxml.m21ToXML.MeasureExporter()
        >>> mxRepeat = MEX.repeatToXml(b)
        >>> MEX.dump(mxRepeat)
        <repeat direction="backward" />
        
        >>> b.times = 3
        >>> mxRepeat = MEX.repeatToXml(b)
        >>> MEX.dump(mxRepeat)
        <repeat direction="backward" times="3" />
        '''
        mxRepeat = Element('repeat')
        if r.direction == 'start':
            mxRepeat.set('direction', 'forward')
        elif r.direction == 'end':
            mxRepeat.set('direction', 'backward')
    #         elif self.direction == 'bidirectional':
    #             environLocal.printDebug(['skipping bi-directional repeat'])
        else:
            raise bar.BarException('cannot handle direction format:', r.direction)
    
        if r.times != None:
            mxRepeat.set('times', str(r.times))
            
        # TODO: attr: winged
        return mxRepeat

    def setMxAttributesObject(self):
        '''
        creates an <attributes> tag (always? or if needed...)
        '''
        m = self.stream
        self.currentDivisions = defaults.divisionsPerQuarter
        mxAttributes = Element('attributes')
        mxDivisions = SubElement(mxAttributes, 'divisions')
        mxDivisions.text = str(self.currentDivisions)
        if self.transpositionInterval is not None:
            mxAttributes.append(self.intervalToXmlTranspose)
        if m.clef is not None:
            mxAttributes.append(self.clefToXml(m.clef))
        if m.keySignature is not None:
            mxAttributes.append(self.keySignatureToXml(m.keySignature))
        if m.timeSignature is not None:
            mxAttributes.append(self.timeSignatureToXml(m.timeSignature))

        # todo returnType = 'list'
        found = m.getElementsByClass('StaffLayout')
        if len(found) > 0:
            sl = found[0] # assume only one per measure
            mxAttributes.append(self.staffLayoutToXmlStaffLayout(sl)) 

        self.xmlRoot.append(mxAttributes)
        return mxAttributes
    
    def timeSignatureToXml(self, ts):
        '''
        Returns a single <time> tag from a meter.TimeSignature object.
    
        Compound meters are represented as multiple pairs of beat
        and beat-type elements
    
        
        >>> a = meter.TimeSignature('3/4')
        >>> MEX = musicxml.m21ToXML.MeasureExporter()
        >>> b = MEX.timeSignatureToXml(a)
        >>> MEX.dump(b)
        <time><beats>3</beats><beat-type>4</beat-type></time>
        
        >>> a = meter.TimeSignature('3/4+2/4')
        >>> b = MEX.timeSignatureToXml(a)
        >>> MEX.dump(b)
        <time><beats>3</beats><beat-type>4</beat-type><beats>2</beats><beat-type>4</beat-type></time>        
        
        >>> a.setDisplay('5/4')
        >>> b = MEX.timeSignatureToXml(a)
        >>> MEX.dump(b)
        <time><beats>5</beats><beat-type>4</beat-type></time>
        '''
        #mxTimeList = []
        mxTime = Element('time')
        # always get a flat version to display any subivisions created
        fList = [(mt.numerator, mt.denominator) for mt in ts.displaySequence.flat._partition]
        if ts.summedNumerator:
            # this will try to reduce any common denominators into 
            # a common group
            fList = meter.fractionToSlashMixed(fList)
    
        for n, d in fList:
            mxBeats = SubElement(mxTime, 'beats')
            mxBeats.text = str(n)
            mxBeatType = SubElement(mxTime, 'beat-type')
            mxBeatType.text = str(d)
            # TODO: interchangeable
            
        # TODO: choice -- senza-misura
    
        # TODO: attr: interchangeable
        # TODO: attr: symbol
        # TODO: attr: separator
        # TODO: attr: print-style-align
        # TODO: attr: print-object
        return mxTime

    def keySignatureToXml(self, keySignature):
        '''
        returns a key tag from a music21
        key.KeySignature or key.Key object
        
        >>> ks = key.KeySignature(-3)
        >>> ks
        <music21.key.KeySignature of 3 flats>
        
        >>> MEX = musicxml.m21ToXML.MeasureExporter()
        >>> mxKey = MEX.keySignatureToXml(ks)
        >>> MEX.dump(mxKey)
        <key><fifths>-3</fifths></key>

        >>> ks.mode = 'major'
        >>> mxKey = MEX.keySignatureToXml(ks)
        >>> MEX.dump(mxKey)
        <key><fifths>-3</fifths><mode>major</mode></key>
        '''
        seta = _setTagTextFromAttribute
        mxKey = Element('key')
        # TODO: attr: number
        # TODO: attr: print-style
        # TODO: attr: print-object
        
        # choice... non-traditional-key...
        # TODO: key-step
        # TODO: key-alter
        # TODO: key-accidental
        
        # Choice traditional-key
        
        # TODO: cancel
        seta(keySignature, mxKey, 'fifths', 'sharps')
        if keySignature.mode is not None:
            seta(keySignature, mxKey, 'mode')
        # TODO: key-octave
        return mxKey
        
    def clefToXml(self, clefObj):
        '''
        Given a music21 Clef object, return a MusicXML clef 
        tag.
    
        >>> gc = clef.GClef()
        >>> gc
        <music21.clef.GClef>
        >>> MEX = musicxml.m21ToXML.MeasureExporter()
        >>> mxc = MEX.clefToXml(gc)
        >>> MEX.dump(mxc)
        <clef><sign>G</sign></clef>
    
        >>> b = clef.Treble8vbClef()
        >>> b.octaveChange
        -1
        >>> mxc2 = MEX.clefToXml(b)
        >>> MEX.dump(mxc2)
        <clef><sign>G</sign><line>2</line><clef-octave-change>-1</clef-octave-change></clef>

        >>> pc = clef.PercussionClef()
        >>> mxc3 = MEX.clefToXml(pc)
        >>> MEX.dump(mxc3)
        <clef><sign>percussion</sign></clef>
        
        Clefs without signs get exported as G clefs with a warning
        
        >>> generic = clef.Clef()
        >>> mxc4 = MEX.clefToXml(generic)
        Clef with no .sign exported; setting as a G clef
        >>> MEX.dump(mxc4)
        <clef><sign>G</sign></clef>
        '''
        # TODO: attr: number
        # TODO: attr: print-style
        # TODO: attr: print-object
        # TODO: attr: number (staff number)
        # TODO: attr: additional
        # TODO: attr: size
        # TODO: attr: after-barline
        mxClef = Element('clef')
        sign = clefObj.sign
        if sign is None:
            print("Clef with no .sign exported; setting as a G clef")
            sign = 'G'
        
        mxSign = SubElement(mxClef, 'sign')
        mxSign.text = sign
        _setTagTextFromAttribute(clefObj, mxClef, 'line')
        if clefObj.octaveChange not in (0, None):
            _setTagTextFromAttribute(clefObj, mxClef, 'clef-octave-change', 'octaveChange')

        return mxClef
        

    def intervalToXmlTranspose(self, i=None):
        '''
        >>> ME = musicxml.m21ToXML.MeasureExporter()
        >>> i = interval.Interval('P5')
        >>> mxTranspose = ME.intervalToXmlTranspose(i)
        >>> ME.dump(mxTranspose)
        <transpose><diatonic>4</diatonic><chromatic>7</chromatic></transpose>
        
        >>> i = interval.Interval('A13')
        >>> mxTranspose = ME.intervalToXmlTranspose(i)
        >>> ME.dump(mxTranspose)
        <transpose><diatonic>19</diatonic><chromatic>10</chromatic><octave-shift>1</octave-shift></transpose>

        >>> i = interval.Interval('-M6')
        >>> mxTranspose = ME.intervalToXmlTranspose(i)
        >>> ME.dump(mxTranspose)
        <transpose><diatonic>-5</diatonic><chromatic>-9</chromatic></transpose>
        '''
        # TODO: number attribute (staff number)
        # TODO: double empty attribute
        if i is None:
            i = self.transpositionInterval
        rawSemitones = i.chromatic.semitones # will be directed
        octShift = 0
        if abs(rawSemitones) > 12:
            octShift, semitones = divmod(rawSemitones, 12)
        else:
            semitones = rawSemitones
        rawGeneric = i.diatonic.generic.directed
        if octShift != 0:
            # need to shift 7 for each octave; sign will be correct
            generic = rawGeneric + (octShift * 7)
        else:
            generic = rawGeneric
    
        mxTranspose = Element('transpose')
        mxDiatonic = SubElement(mxTranspose, 'diatonic')
    
        # must implement the necessary shifts
        if rawGeneric > 0:
            mxDiatonic.text = str(generic - 1)
        elif rawGeneric < 0:
            mxDiatonic.text = str(generic + 1)

        mxChromatic = SubElement(mxTranspose, 'chromatic')
        mxChromatic.text = str(semitones)
    
        if octShift != 0:
            mxOctaveChange = SubElement(mxTranspose, 'octave-shift')
            mxOctaveChange.text = str(octShift)
        
        return mxTranspose


    def setMxPrint(self):
        m = self.stream
        # print objects come before attributes
        # note: this class match is a problem in cases where the object is created in the module itself, as in a test. 
    
        # do a quick search for any layout objects before searching individually...
        foundAny = m.getElementsByClass('LayoutBase')
        if len(foundAny) == 0:
            return
        
        found = m.getElementsByClass('PageLayout')
        if len(found) > 0:
            pl = found[0] # assume only one per measure
            mxPrint = self.pageLayoutToXmlPrint(pl)
        found = m.getElementsByClass('SystemLayout')
        if len(found) > 0:
            sl = found[0] # assume only one per measure
            if mxPrint is None:
                mxPrint = self.systemLayoutToXmlPrint(sl)
            else:
                self.systemLayoutToXmlPrint(sl, mxPrint)
        found = m.getElementsByClass('StaffLayout')
        if len(found) > 0:
            sl = found[0] # assume only one per measure
            if mxPrint is None:
                mxPrint = self.staffLayoutToXmlPrint(sl)
            else:
                self.staffLayoutToXmlPrint(sl, mxPrint)
        # TODO: measure-layout
        # TODO: measure-numbering
        # TODO: part-name-display
        # TODO: part-abbreviation-display

        # TODO: attr: blank-page
        # TODO: attr: page-number

        if mxPrint is not None:
            self.xmlRoot.append(mxPrint)

        
    def setMxAttributes(self):
        '''
        sets the attributes (x=y) for a measure,
        that is, number, and layoutWidth
        
        Does not create the <attributes> tag. That's elsewhere...
        
        '''
        m = self.stream
        self.xmlRoot.set('number', m.measureNumberWithSuffix())
        # TODO: attr: implicit
        # TODO: attr: non-controlling
        if m.layoutWidth is not None:
            _setAttributeFromAttribute(m, self.xmlRoot, 'width', 'layoutWidth')
        
    def setRbSpanners(self):
        self.rbSpanners = self.spannerBundle.getBySpannedElement(
                                self.stream).getByClass('RepeatBracket')
        
    def setTranspose(self):
        if self.parent is None:
            return
        if self.parent.stream is None:
            return
        if self.parent.stream.atSoundingPitch is True:
            return

        m = self.stream()
        self.measureOffsetStart = m.getOffsetBySite(self.parent.stream)

        instSubStream = self.parent.instrumentStream.getElementsByOffset(
                    self.measureOffsetStart,
                    self.measureOffsetStart + m.duration.quarterLength,
                    includeEndBoundary=False)        
        if len(instSubStream) == 0:
            return
        
        instSubObj = instSubStream[0]
        if instSubObj.transposition is None:
            return
        self.transpositionInterval = instSubObj.transposition
        # do here???
        #self.mxTranspose = self.intervalToMXTranspose()



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