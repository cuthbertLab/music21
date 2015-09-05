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
import pprint
import sys
import traceback
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
# Helpers...

#     def _runIfTag(el, tag, func, inputM21=None):
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
        

def _setAttributeFromTagText(m21El, xmlEl, tag, attributeName=None, transform=None):
    '''
    If xmlEl has a at least one element of tag==tag with some text. If
    it does, set the attribute either with the same name (with "foo-bar" changed to
    "fooBar") or with attributeName to the text contents.
    
    Pass a function or lambda function as transform to transform the value before setting it
    
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
    >>> seta(md, e2, 'movement-title')
    >>> md.movementTitle
    'Trout'
    
    set a different attribute
    
    >>> seta(md, e2, 'movement-title', 'composer')
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
        
        self.definesExplicitSystemBreaks = False # TODO -- set to score and parts
        self.definesExplicitPageBreaks = False

        self.spannerBundle = spanner.SpannerBundle()
        self.partIdDict = {}
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
        self.parseXMLText()
        return self.stream
    
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
            s._insertCore(0, part)
        
        s.elementsChanged()
        
        if inputM21 is None:
            return s

    def xmlPartToPart(self, mxPart, partIdDict):
        parser = PartParser(mxPart, partIdDict, parent=self)
        parser.parse()
        return parser.stream

    def parsePartList(self, mxScore):
        mxPartList = mxScore.find('part-list')
        if mxPartList is None:
            return

        for mxScorePart in mxPartList.findall('score-part'):
            partId = mxScorePart.get('id')
            self.partIdDict[partId] = mxScorePart

        for mxPartGroup in mxPartList.findall('part-group'):
            self.partGroupList.append(mxPartGroup)
            
        
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

        seta = _setAttributeFromTagText

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

        seta = _setAttributeFromTagText
        
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
    
        seta = _setAttributeFromTagText

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
        
        seta = _setAttributeFromTagText
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
            
        c.name = creator.text.strip()
        if inputM21 is None:
            return c        
        

#------------------------------------------------------------------------------
class PartParser(object):
    '''
    parser to work with a single <part> tag.
    
    called out for multiprocessing potential in future
    '''
    def __init__(self, mxPart=None, mxPartInfo=None, parent=None):
        self.mxPart = mxPart
        self.mxPartInfo = mxPartInfo
        self.partId = mxPart.get('id')
        self._parent = common.wrapWeakref(parent)
        self.spannerBundle = parent.spannerBundle
        self.stream = stream.Part()
        self.atSoundingPitch = True
        
        self.staffReferenceList = []
        
        self.lastTimeSignature = None
        self.lastTransposition = None  # may change at measure boundaries
        self.lastMeasureWasShort = False
        self.lastMeasureOffset = 0.0
        
        self.lastMeasureNumber = 0
        self.lastMeasureSuffix = None
        
        self.activeInstrument = None
        self.firstMeasureParsed = False
        self.activeAttributes = None # divisions, clef, etc.        
        self.lastDivisions = None

    def _getParent(self):
        return common.unwrapWeakref(self._parent)

    parent = property(_getParent)
    
    def parse(self):
        self.parsePartInfo()
        self.parseMeasures()
        self.stream.atSoundingPitch = self.atSoundingPitch
    
    def parseMeasures(self):
        part = self.stream
        for mxMeasure in self.iterfind('measure'):
            self.xmlMeasureToMeasure(mxMeasure)
        part.elementsChanged()
           
    def measureParsingError(self, mxMeasure, e):
        measureNumber = "unknown"
        try:
            measureNumber = mxMeasure.get('number')
        except:
            pass
        # see http://stackoverflow.com/questions/6062576/adding-information-to-a-python-exception
        execInfoTuple = sys.exc_info()
        if hasattr(e, 'message'):
            emessage = e.message
        else:
            emessage = execInfoTuple[0].__name__ + " : " #+ execInfoTuple[1].__name__
        message = "In measure (" + measureNumber + "): " + emessage
        raise type(e)(type(e)(message), pprint.pformat(traceback.extract_tb(execInfoTuple[2])))
    
    def xmlMeasureToMeasure(self, mxMeasure):
        parser = MeasureParser(mxMeasure, parent=self)
        try:
            parser.parse()
        except Exception as e:
            self.measureParsingError(mxMeasure, e)
        
        if parser.transposition is not None:
            if (self.lastTransposition is None 
                and self.firstMeasureParsed is False
                and self.activeInstrument is not None):
                self.activeInstrument.transposition = parser.transposition
            elif self.activeInstrument is not None:
                newInst = copy.deepcopy(self.activeInstrument)
                newInst.transposition = parser.transposition 
                self.stream._insertCore()
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
            self.lastMeasureSuffix = parser.numberSuffix      
        m = parser.stream
        if m.timeSignature is not None:
            self.lastTimeSignature = m.timeSignature
        elif self.lastTimeSignature is None and m.timeSignature is None:
            # if no time sigature is defined, need to get a default
            ts = meter.TimeSignature
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
        lastTimeSignatureQuarterLength = self.lastTimeSignature.barDuration.quarterLength

        if mHighestTime >= lastTimeSignatureQuarterLength :
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
        self.firstInstrumentObject = instrumentObj
        if instrumentObj.bestName() is not None:
            self.stream.id = instrumentObj.bestName()
        self.stream._insertCore(0, instrumentObj) # add instrument at zero offset
        
    def getDefaultInstrument(self):
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

        
        mxInfo = self.mxPartInfo
        i = instrument.Instrument()
        i.partId = self.partId
        i.groups.append(self.partId)

        seta(i, mxInfo, 'partName', transform=_clean)
        # TODO: partNameDisplay
        seta(i, mxInfo, 'partAbbreviation', transform=_clean)
        # TODO: partAbbreviationDisplay        
        # TODO: groups
        
        # for now, just get first instrument
        # TODO: get all instruments!
        mxScoreInstrument = mxInfo.find('score-instrument')
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
        seta(i, mxMIDIInstrument, 'midi-program', transform=_adjustMidiData)
        seta(i, mxMIDIInstrument, 'midi-channel', transform=_adjustMidiData)

        # TODO: reclassify 
        return i
#------------------------------------------------------------------------------
class MeasureParser(object):
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
                        'attributes': None,
                        'harmony': 'xmlHarmony',
                        'figured-bass': None,
                        'print': 'xmlPrint',
                        'sound': None,
                        'barline': 'xmlBarline',
                        'grouping': None,
                        'link': None,
                        'bookmark': None,    
                        # TODO: clefs???                    
                        }
    # TODO: editorial, i.e., footnote and level
    # TODO: staves (num staves)
    # TODO: part-symbol
    # TODO: directive DEPRECATED since MusicXML 2.0
    # TODO: measure-style
    def __init__(self, mxMeasure=None, parent=None):
        self.mxMeasure = mxMeasure
        self.parent = parent # PartParser
        self.transposition = None
        if parent is not None:
            self.spannerBundle = parent.spannerBundle
        else:
            self.spannerBundle = spanner.SpannerBundle()
            
        self.staffReference = {}
        self.useVoices = False
        self.voiceIndices = set()
        
        self.activeAttributes = None
        self.attributesAreInternal = True
        
        self.measureNumber = None
        self.measureSuffix = None
        
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
        
    def addToStaffReference(self, mxObjectOrNumber, m21Object):
        '''
        Utility routine for importing musicXML objects; 
        here, we store a reference to the music21 object in a dictionary, 
        where keys are the staff values. Staff values may be None, 1, 2, etc.
        '''
        staffReference = self.staffReference

        #environLocal.printDebug(['addToStaffReference(): called with:', music21Object])
        if common.isListLike(mxObjectOrNumber):
            if len(mxObjectOrNumber) > 0:
                mxObjectOrNumber = mxObjectOrNumber[0] # if a chord, get the first components
            else: # if an empty list
                environLocal.printDebug(['got an mxObject as an empty list', mxObjectOrNumber])
                return
        # add to staff reference
        if hasattr(mxObjectOrNumber, 'staff'):
            key = mxObjectOrNumber.staff
        # some objects store staff assignment simply as number
        else:
            try:
                key = mxObjectOrNumber.get('number')
            except AttributeError: # a normal number
                key = mxObjectOrNumber
        if key not in staffReference:
            staffReference[key] = []
        staffReference[key].append(m21Object)
    
    def insertCoreAndRef(self, offset, mxObjectOrNumber, m21Object):
        self.addToStaffReference(mxObjectOrNumber, m21Object)
        self.stream._insertCore(offset, m21Object)
        
    def parse(self):
        self.parseAttributes()
        self.updateVoiceInformation()
        
        for i, mxObj in enumerate(self.mxMeasure):
            self.parseIndex = i
            if mxObj.tag in self.attributeTagsToMethods:
                methName = self.attributeTagsToMethods[mxObj.tag]
                if methName is not None:
                    meth = getattr(self, methName)
                    meth(self, mxObj)
        
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

    def xmlToNote(self, mxNote):
        pass
    
    def xmlBarline(self, mxBarline):
        pass
    
    def xmlHarmony(self, mxHarmony):
        pass
    
    def xmlDirection(self, mxDirection):
        pass
    
    
    def parseAttributes(self):        
        self.parseMeasureNumbers()        
        # TODO: implicit
        # TODO: non-controlling 
        # may need to do a format/unit conversion?        
        self.layoutWidth = self.mxMeasure.get('width')
        self.parseAttributesTags()
        
    def parseAttributesTags(self):
        # TODO: keep track of where they occur in the measure...        
        mxMeasure = self.mxMeasure
        
        allAttributes = mxMeasure.findall('attributes')
        if len(allAttributes) == 0:
            self.attributesAreInternal = False
            self.activeAttributes = self.parent.activeAttributes
            if self.activeAttributes is None:
                raise MusicXMLImportException(
                            'no mxAttribues available for this measure: {0}'.format(mxMeasure)
                                              )
        # getting first for each of these for now
        if self.attributesAreInternal:
            mxAttributes = allAttributes[0]
            for mxSub in mxAttributes:
                meth = None
                # key, clef, time, details
                if mxSub.tag in self.attributeTagsToMethods:
                    meth = getattr(self, self.attributeTagsToMethods[mxSub.tag])
                if meth is not None:
                    meth(self, mxSub)
            transposeTag = mxAttributes.find('transpose')
            if transposeTag is not None:
                self.transposition = self.xmlTransposeToInterval(transposeTag)
            divisionsTag = mxAttributes.find('divisions')
            if divisionsTag is not None:
                self.parent.lastDivisions = common.opFrac(float(divisionsTag.text))
        
        self.divisions = self.parent.lastDivisions

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
            oc = int(mxOctaveChange) * 12
    
        # TODO: presently not dealing with <double>
        # doubled one octave down from what is currently written 
        # (as is the case for mixed cello / bass parts in orchestral literature)
        #environLocal.printDebug(['ds', ds, 'cs', cs, 'oc', oc])
        if ds is not None and ds != 0 and cs is not None and cs != 0:
            # diatonic step can be used as a generic specifier here if 
            # shifted 1 away from zero
            if ds < 0:
                post = interval.intervalFromGenericAndChromatic(ds - 1, cs + oc)
            else:
                post = interval.intervalFromGenericAndChromatic(ds + 1, cs + oc)
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
        >>> mxTime = ET.fromstring('<time><time-signature><beats>3</beats><beat-type>8</beat-type></time-signature></time>')
        
        >>> MP = musicxml.xmlToM21.MeasureParser()
        >>> MP.xmlToTimeSignature(mxTime)
        <music21.meter.TimeSignature 3/8>      
        '''
        ts = meter.TimeSignature()
        n = []
        d = []
        # just get first one for now;
        for beatOrType in mxTime.find('time-signature'):
            if beatOrType.tag == 'beats':
                n.append(beatOrType.text) # may be 3+2
            elif beatOrType.tag == 'beat-type':
                d.append(beatOrType.text)
        # convert into a string
        msg = []
        for i in range(len(n)):
            msg.append('%s/%s' % (n[i], d[i]))
    
        #environLocal.warn(['loading meter string:', '+'.join(msg)])
        ts.load('+'.join(msg))
        
        return ts
        
    def handleClef(self, mxClef):
        clef = self.xmlToClef(mxClef)
        self.insertCoreAndRef(0, mxClef, clef)
    
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
                octaveChange = int(mxOctaveChange)
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
        seta = _setAttributeFromTagText
        staffNumber = mxDetails.get('number')
        if staffNumber is not None:
            staffNumber = int(staffNumber)
            for stl in self.staffLayoutObjects:
                if stl.staffNumber == staffNumber:
                    try:
                        seta(stl, mxDetails, 'staff-size', transform=float)
                    except TypeError:
                        staffSize = mxDetails.find('staff-size')
                        if staffSize is None:
                            raise TypeError("Incorrect number for mxStaffDetails.staffSize: %s", staffSize)
                    return
        else:
            foundMatch = False
            for stl in self.staffLayoutObjects:
                if stl.staffSize is None:
                    seta(stl, mxDetails, 'staff-size', transform=float)
                    foundMatch = True
                if stl.staffLines is None:
                    seta(stl, mxDetails, 'staff-lines', transform=int)
                    foundMatch = True
            if foundMatch is True:
                return
        # no staffLayoutObjects or none that match on number
        stl = layout.StaffLayout()
        seta(stl, mxDetails, 'staff-size', transform=float)
        seta(stl, mxDetails, 'staff-lines', transform=int)
        staffNumber = mxDetails.get('number')
        if staffNumber is not None:
            stl.staffNumber = int(staffNumber)
        staffPrinted = mxDetails.get('print-object')
        if staffPrinted == 'no' or staffPrinted is False:
            stl.hidden = True
        elif staffPrinted == 'yes' or staffPrinted is True:
            stl.hidden = False
        
        # should this be 0.0 or current offset?
        self.insertCoreAndRef(0.0, mxDetails, stl)
        self.staffLayoutObjects.append(stl)

    
    def parseMeasureNumbers(self):
        m = self.stream
        lastMNum = self.parent.lastMeasureNumber
        lastMSuffix = self.parent.lastMeasureSuffix
        
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
        self.measureSuffix = m.numberSuffix
        
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

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
    
    
