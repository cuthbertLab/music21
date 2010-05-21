#-------------------------------------------------------------------------------
# Name:         base.py / musicxml.py
# Purpose:      Convert MusicXML to and from music21
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


import sys, os, copy
import unittest, doctest
import StringIO # this module is not supported in python3
try:
    import cPickle as pickleMod
except ImportError:
    import pickle as pickleMod

import xml.sax
import xml.dom.minidom

import music21
from music21 import defaults
from music21 import common
from music21 import node
xml.dom.minidom.Element.writexml = node.fixed_writexml

from music21 import environment
_MOD = 'musicxml.py'
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------
# store the highest version number of m21 that pickled mxl object files
# are compatible; compatible pickles (always written with the m21 version)
# are >= to this value
# if changes are made here that are not compatible, the m21 version number
# needs to be increased and this number needs to be set to that value
VERSION_MINIMUM = (0, 2, 2) 


#-------------------------------------------------------------------------------
# notes

# problem with element tree:
# http://effbot.org/zone/element.htm
# Note that the standard element writer creates a compact output. There is no built-in support for pretty printing or user-defined namespace prefixes in the current version, so the output may not always be suitable for human consumption (to the extent XML is suitable for human consumption, that is).

# unicode and python issues
# http://evanjones.ca/python-utf8.html

# TODO:
# handle direction-type metronome, beat-unit, etc.; test 31c
# deal with grace notes, in particular duration handling
# add print <print new-system="yes"/>

# tests matching
# 01a, 01b, 01c, 01d
# 02a, 02c, 02d, 02e

# tests that do not match
# 02b-Rest-PitchedRest.xml
#   rests currently do not store display settings



#-------------------------------------------------------------------------------
DYNAMIC_MARKS = ['p', 'pp', 'ppp', 'pppp', 'ppppp', 'pppppp',
        'f', 'ff', 'fff', 'ffff', 'fffff', 'ffffff',
        'mp', 'mf', 'sf', 'sfp', 'sfpp', 'fp', 'rf', 'rfz', 'sfz', 'sffz', 'fz']

# order here may matter
ARTICULATION_MARKS = ['staccato', 'accent', 'strong-accent', 'tenuto', 
            'detached-legato', 'staccatissimo', 'spiccato', 
            'scoop',  'plop', 'doit',  'falloff', 'breath-mark',
            'caesura',  'stress', 'unstress'] 

TECHNICAL_MARKS = ['up-bow', 'down-bow', 'harmonic', 'open-string',
         'thumb-position', 'fingering', 'pluck', 'double-tongue',
         'triple-tongue', 'stopped', 'snap-pizzicato', 'fret',
         'string', 'hammer-on', 'pull-off', 'tap', 'heel',
         'toe', 'fingernails']  

# 'bend' : not implemented as needs many sub components

#-------------------------------------------------------------------------------
def yesNoToBoolean(value):
    if value in ['yes', True]:
        return True
    else:
        return False


def booleanToYesNo(value):
    if value:
        return 'yes'
    else:
        return 'no'




#-------------------------------------------------------------------------------
class TagException(Exception):
    pass

class TagLibException(Exception):
    pass

class MusicXMLException(Exception):
    pass

class DocumentException(Exception):
    pass

#-------------------------------------------------------------------------------
class Tag(object):
    '''Object to store tags as encountered by SAX. Tags can be open or closed based on the status attribute. Tags can store character data collected between their defined tags. These are used only for finding and collecting tag attributes and elements. As we do not need character data for all tags, tags have an optional flag to select if the are to collect character data.'''
    def __init__(self, tag, cdFlag=False, className=None):
        self.tag = tag
        self.cdFlag = cdFlag # character data flag
        self.status = 0
        self.charData = u''
        self.className = className

        self.count = 0 # for statistics; not presentl used

    def start(self):
        if self.status: # already open
            raise TagException('Tag (%s) is already started.' % self.tag)
        self.status = 1

    def end(self):
        if not self.status:
            raise TagException('Tag (%s) is already ended.' % self.tag)
        self.status = 0
        # when not doing audit checks, no need to count
        #self.count += 1 # increment on close

    def clear(self):
        self.charData = u''

    def zeroCount(self):
        self.count = 0

    def __eq__(self, other):
        if other == self.tag: return True
        else: return False

    def __ne__(self, other):
        if other != self.tag: return 1
        else: return False

    def __call__(self):
        return self.charData

    def __str__(self):
        return "%s: %s" % (self.tag, self.charData)



class TagLib(object):
    '''
    An object to store all MusicXML tags as Tag objects. Tag objects are used 
    just to identify tags, store element contents and status in SAX parsing. 
    With this design some tags can be used simply in SAX parsing as 
    structural monitors, but not be instantiated as objects for content 
    delivery.
    '''
    def __init__(self):
        self._t = {}

        # store tag, charDataBool, className
        # charDataBool is if this tag stores char data
        # order here is based on most-often used, found through empircal tests
        _tags = [
('voice', True), 
('note', False, Note), 
('duration', True), 
('type', True), 
('beam', True, Beam), 
('step', True), 
('stem', True), 
('pitch', False, Pitch), 
('octave', True), 
('alter', True), 
('notations', False, Notations), 
('measure', False, Measure), 
('slur', False, Slur), 
('articulations', False, Articulations), 
('rest', False, Rest), 
('accidental', True, Accidental), 
('direction', False, Direction), 
('direction-type', False, DirectionType), 
('dot', False, Dot), 
('dynamics', False, Dynamics), 
('tied', False, Tied), 
('tie', False, Tie), 
('chord', False), 
('lyric', False, Lyric), 
('syllabic', True), 
('text', True),
('trill-mark', False, TrillMark), 
('attributes', False, Attributes), 
('divisions', True), 
('forward', False, Forward), 
('backup', False, Backup), 
('grace', False, Grace),  
('time-modification', False, TimeModification), 
('actual-notes', True), 
('normal-notes', True), 
('normal-type', True), 
('normal-dot', True), 
('tuplet', False, Tuplet), 
('notehead', True, Notehead), 
('technical', False, Technical), 
('wedge', False, Wedge), 
('ornaments', False, Ornaments), 
('part', False, Part), 
('key', False, Key), 
('fifths', True), 
('mode', True), 
('cancel', True), 
('key-step', True, KeyStep), 
('key-alter', True, KeyAlter), 
('key-octave', True, KeyOctave), 
('transpose', False, Transpose), 
('diatonic', True), 
('chromatic', True), 
('octave-change', True), 
('time', False, Time), 
('beats', True, Beats), 
('beat-type', True, BeatType), 
('clef', False, Clef), 
('sign', True), 
('line', True), 
('clef-octave-change', True), 
('staff', True), 
('fermata', True, Fermata), 
('barline', False, Barline), 
('ending', False, Ending), 
('bar-style', True), 
('repeat', False, Repeat), 
('measure-style', False, MeasureStyle), 
('multiple-rest', True), 
('staves', True), 
('display-step', True, DisplayStep), 
('display-octave', True, DisplayOctave),
        ]
        _tags += DYNAMIC_MARKS
        _tags += ARTICULATION_MARKS
        _tags += TECHNICAL_MARKS
        _tags += [('other-dynamics', True, DynamicMark), 
('other-articulation', True, ArticulationMark), 
('other-technical', True, TechnicalMark), 
('score-partwise', False), 
('score-timewise', False),  
('movement-title', True), 
('movement-number', True), 
('work', False, Work), 
('work-title', True), 
('work-number', True), 
('opus', False), 
('identification', False, Identification),  
('rights', True), 
('creator', True, Creator), 
('encoding', False, Encoding), 
('software', True, Software), 
('encoding-date', True), 
('part-list', False, PartList), 
('part-group', False, PartGroup), 
('group-name', True), 
('group-symbol', True), 
('group-barline', True), 
('group-name-display', False), 
('group-abbreviation', False), 
('group-abbreviation-display', False), 
('group-time', False), 
('solo', False), 
('ensemble', False), 
('score-part', False, ScorePart), 
('score-instrument', False, ScoreInstrument), 
('instrument-name', True), 
('instrument-abbreviation', True), 
('part-name', True), 
('midi-instrument', False, MIDIInstrument),
('midi-channel', True), 
('midi-program', True), 
('volume', False), 
('pan', False), 
('elevation', False),
('midi-name', False), 
('midi-bank', False), 
('midi-unpitched', False), 
('double', False),  
        ]

        # order matters: keep order here
        self.tagsCharData = []
        self.tagsAll = [] 

        for data in _tags:
            if common.isStr(data): # if just a string w/o a class definition
                if data in DYNAMIC_MARKS:
                    data = [data, False, DynamicMark]
                elif data in ARTICULATION_MARKS:
                    data = [data, False, ArticulationMark]
                elif data in TECHNICAL_MARKS:
                    data = [data, False, TechnicalMark]
                else:
                    raise MusicXMLException('got tag without any information on it: %s' % data)
            tagName = data[0]
            charDataBool = data[1]
            if len(data) > 2:
                className = data[2]
            else: # not all tags define a clas sname
                className = None

            # error check for redundancy
            if tagName in self._t.keys():
                raise TagLibException('duplicated tag %s' % tagName)

            # store tag names in order
            self.tagsAll.append(tagName)
            if charDataBool:
                self.tagsCharData.append(tagName)

            self._t[tagName] = Tag(tagName, charDataBool, className)
        
        # utility
        self._stat = None
        self._statMapWidth = 80

    def __getitem__(self, key):
        return self._t[key]

    #---------------------------------------------------------------------------
    # utilities for error checking and debugging

    def _statTabulate(self):
        self._stat = {}
        tags = self._t.keys()
        tags.sort()

        maxCount = 0
        maxTag = 0
        for tag in tags:
            if self._t[tag].count > maxCount: 
                maxCount = self._t[tag].count
            if len(tag) > maxTag: 
                maxTag = len(tag)

        for tag in tags:
            # get magnitude string
            if maxCount > 0:
                if maxCount > self._statMapWidth:
                    scalar = self._statMapWidth * (self._t[tag].count / 
                            float(maxCount))
                    scalar = int(round(scalar))
                else:
                    scalar = self._t[tag].count
                magStr = scalar * '.'
            else: magStr = ''
            # get formatted tag str
            tagStr = tag.ljust(maxTag+1)
            # store count, tag string, magnitude string
            self._stat[tag] = [self._t[tag].count, tagStr, magStr]

    def statClear(self):
        tags = self._t.keys()
        for tag in tags:
            self._t[tag].zeroCount()

    def _statMapActive(self):
        '''Display method for tag audit checks
        '''
        tags = self._t.keys()
        tags.sort()
        sortOrder = []
        for tag in tags:
            if self._stat[tag][0] > 0:
                # count, tagStr, magStr
                sortOrder.append(self._stat[tag])

        sortOrder.sort()
        msg = []
        for count, tagStr, magStr in sortOrder:
            msg.append(tagStr + str(count).ljust(4) + magStr)
        print('\n'.join(msg))

    def statRun(self):
        self._statTabulate()
        self._statMapActive()

    def audit(self):
        '''
        A way to check for errors in SAX parsing. Assumes that 
        all start() calls have been paired with an end() call, 
        and that all element data has been cleared.
        '''
        errors = []
        header = 'TagLib audit: '
        for key in self._t:
            if self._t[key].status != 0:
                errors.append('tag <%s> left open' % key)
            if self._t[key].cdFlag:
                sample = self._t[key].charData
                if sample != '':
                    errors.append('tag <%s> left element data: %s' % (key, sample))
        if len(errors) != 0:
            ok = 0
            return ok, header + ('%s erorrs found:\n' % len(errors)) + '\n'.join(errors)
        else:
            ok = 1
            return ok, header + 'no errors found.' 




#-------------------------------------------------------------------------------
class MusicXMLElement(node.Node):
    '''MusicXML elements are an abstraction of MusicXML into an object oriented framework. Some, not all, of MusicXML elements are represented as objects. Some sub-elements are much more simply placed as attributes of parent objects. These simple elements have only a tag and character data. Elements that have attributes and/or sub-elements, however, must be represented as objects.
    '''

    def __init__(self):
        '''
    
        These tests are module specific and should be loaded as unittests, below

        >>> a = MusicXMLElement()
        >>> a._convertNameToXml('groupAbbreviation')
        'group-abbreviation'
        >>> a._convertNameToXml('midiUnpitched')
        'midi-unpitched'
        >>> a._convertNameToXml('groupNameDisplay')
        'group-name-display'
        >>> a._convertNameToXml('group-name-display')
        'group-name-display'

        >>> a = MusicXMLElement()
        >>> a._convertNameFromXml('group-abbreviation')
        'groupAbbreviation'
        >>> a._convertNameFromXml('midi-unpitched')
        'midiUnpitched'
        >>> a._convertNameFromXml('midiUnpitched')
        'midiUnpitched'
        >>> a._convertNameFromXml('opus')
        'opus'
        >>> a._convertNameFromXml('group-name-display')
        'groupNameDisplay'

        >>> a = MusicXMLElement()
        >>> len(a._publicAttributes())
        3
        >>> print(a._publicAttributes())
        ['charData', 'external', 'tag']


        '''
        node.Node.__init__(self)
        self.external = {} # references to external objects
    
        self._attr = {} # store attributes in dictionary
        self._tag = None # name of tag
        self.charData = None # obtained by assignment from a Tag

        self._doctypeName = 'score-partwise'
        self._doctypePublic = '-//Recordare//DTD MusicXML 2.0 Partwise//EN'
        self._doctypeSystem = 'http://www.musicxml.org/dtds/partwise.dtd'

        # dictionary of local Python name and possible names assumed
        # from music xml. used in get and set methods
        # specialize in subclassess
        self._crossReference = {'charData': ['characterData', 'content']}



class MusicXMLElementList(MusicXMLElement):
    '''MusicXML that is designed to function as a list. In general,
     this is an element this only used to contain other Elements. 
     List operations permit easy access and manipuation.

    Note that design here mirrors that of node.py NodeList, but this needs
    to be a subclass of of MusicXMLElement
    '''

    def __init__(self):
        MusicXMLElement.__init__(self)
        # basic storage location
        self.componentList = [] 
        # additional attributes and elements will be defined in subclass

    def _getComponents(self):
        return self.componentList

    def append(self, item):
        self.componentList.append(item)

    def __len__(self):
        return len(self.componentList)

    def __iter__(self):
        return common.Iterator(self.componentList)

    def __getitem__(self, key):
        '''Get item via index value
        '''
        return self.componentList[key]

    def __add__(self, other):
        '''Used to combine component lists of objects. There may be other object
        attributes not on component list that are not 'added' with this method.

        >>> a = MusicXMLElementList()
        >>> a.componentList.append(1)
        >>> b = MusicXMLElementList()
        >>> b.componentList.append(2)
        >>> c = a + b
        >>> c.componentList
        [1, 2]
        >>> a.componentList # original is not changed
        [1]
        '''
        new = copy.deepcopy(self)
        new.componentList += other.componentList
        return new



#-------------------------------------------------------------------------------
class Score(MusicXMLElementList):
    '''Score is used to collect score header elements and, 
    if available, all other MusicXML data. Score can be used for 
    partwise or timewise scores. This object includes all MusicXML score 
    information.
    '''
    def __init__(self, m21Version=None):
        '''
        >>> a = Score()
        >>> a.tag
        'score-partwise'
        >>> a.setDefaults()
        >>> b = Identification()
        >>> b.setDefaults()
        >>> a.set('identification', b)
        >>> c = Score()
        >>> d = c.merge(a)
        '''
        MusicXMLElementList.__init__(self)
        self._tag = 'score-partwise' # assumed for now
        # attributes
        self._attr['version'] = None
        # elements
        self.movementTitle = None
        self.movementNumber = None
        # component objects
        self.workObj = None
        self.identificationObj = None
        self.encodingObj = None 
        self.partListObj = None
        self.componentList = [] # list of Part objects

        self._crossReference['partListObj'] = ['partlist', 'part-list']
        self._crossReference['identificationObj'] = ['identification']

        # the score, as the outermost container, stores the m21 version 
        # number that it was made with when written to disc
        # this value is only relevant in comparing pickled files
        self.m21Version = m21Version

    def _getComponents(self):
        c = []
        c.append(self.workObj)
        c.append(('movement-number', self.movementNumber))
        c.append(('movement-title', self.movementTitle))
        c.append(self.identificationObj)
        c.append(self.partListObj)
        c = c + self.componentList
        return c

    def setDefaults(self):
        self.set('movementTitle', defaults.title)

    #---------------------------------------------------------------------------
    # utility methods unique to the score
    def getPartIds(self):
        '''A quick way to get all valid part ids
        '''
        post = []        
        for part in self.componentList:
            post.append(part.get('id'))
        return post

    def getPartNames(self):
        '''A quick way to get all valid par ids
        '''
        post = {} # return a dictionary
        for part in self.partListObj:
            if isinstance(part, ScorePart):
                post[part.get('id')] = part.get('part-name')
        return post

    def getInstrument(self, partId):
        '''Get an instrument from a part

        >>> a = Score()
        >>> a.setDefaults()
        >>> a.getInstrument('P3') == None
        True
        >>> from music21.musicxml import testPrimitive
        >>> b = Document()
        >>> b.read(testPrimitive.pitches01a)
        >>> b.score.getInstrument(b.score.getPartNames().keys()[0])
        <score-part id=P1 part-name=MusicXML Part>
        '''
        inst = None
        if self.partListObj == None:
            return inst
        for obj in self.partListObj:
            if isinstance(obj, ScorePart):
                if obj.get('id') == partId:
                    inst = obj 
                    break
        return inst


    def getPart(self, partId):
        ''' Get a part, given an id.

        >>> from music21.musicxml import testPrimitive
        >>> b = Document()
        >>> b.read(testPrimitive.ALL[0])
        >>> c = b.score.getPart(b.score.getPartNames().keys()[0])
        >>> isinstance(c, Part)
        True
        '''

        idFound = None

        partNames = self.getPartNames()    
        if partId in partNames.keys():
            idFound = partId
        else:
            for id in self.getPartIds():
                if id.lower() == partId.lower(): # assume always lower
                    idFound = id
                    break
                # check for part name
                elif partId.lower() == partNames[id].lower(): 
                    idFound = id
                    break
        if idFound == None:
            raise MusicXMLException('no part with id %s' % partId)
        # get part objects
        partObj = None
        for part in self.componentList:
            if part.get('id') == idFound:
                partObj = part
                break
        if partObj == None:
            raise MusicXMLException('could not find id %s in Score' % partId)
        return partObj




#-------------------------------------------------------------------------------
class Work(MusicXMLElement):
    def __init__(self):
        '''
        >>> a = Work()
        >>> a.tag
        'work'
        '''
        MusicXMLElement.__init__(self)
        self._tag = 'work'
        # simple elements
        self.workNumber = None
        self.workTitle = None
        self.opus = None # not implemented

    def _getComponents(self):
        c = []
        c.append(('work-number', self.workNumber))
        c.append(('work-title', self.workTitle))
        c.append(('opus', self.opus))
        return c

    def setDefaults(self):
        self.set('work-title', defaults.title)


class Identification(MusicXMLElement):
    def __init__(self):
        '''
        >>> a = Identification()
        >>> a.tag
        'identification'
        '''
        MusicXMLElement.__init__(self)
        self._tag = 'identification'
        # simple elements
        self.rights = None
        # component objects    
        self.creatorList = [] # list of creator objects
        self.encodingObj = None

    def _getComponents(self):
        c = []
        c = c + self.creatorList
        c.append(('rights', self.rights))
        c.append(self.encodingObj)
        # source
        # relation
        return c

    def setDefaults(self):
        mxCreator = Creator() # add a creator
        mxCreator.setDefaults()
        # TODO: make this a  components list and a ElementList subclas?
        self.set('creatorList', [mxCreator])


class Creator(MusicXMLElement):
    def __init__(self):
        '''
        >>> a = Creator()
        >>> a.tag
        'creator'
        '''
        MusicXMLElement.__init__(self)
        self._tag = 'creator'
        # attributes
        self._attr['type'] = type
        # character data
        self.charData = None
    
    def setDefaults(self):
        self.set('type', 'composer')
        self.set('charData', defaults.author)


class Encoding(MusicXMLElement):
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'encoding'
        # simple elements
        self.encodingDate = None
        # sub objects
        self.softwareList = [] # list of objects
    
    def _getComponents(self):
        c = []
        c.append(('encoding-date', self.encodingDate))
        # encoder
        c = c + self.softwareList 
        # encoding-description
        # supports
        return c


class Software(MusicXMLElement):
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'software'
        self.charData = None # only content

    def setDefaults(self):
        self.set('charData', defaults.software)


class PartList(MusicXMLElementList):
    def __init__(self):
        MusicXMLElementList.__init__(self)
        self._tag = 'part-list'
        # list of objects
        self.componentList = [] # a list of partGroups and scoreParts

    def _getComponents(self):
        return self.componentList



class PartGroup(MusicXMLElement):
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'part-group'
        # attributes
        self._attr['type'] = None
        self._attr['number'] = None
        # simple elements
        self.groupName = None
        self.groupNameDisplay = None
        self.groupAbbreviation = None
        self.groupAbbreviationDisplay = None
        self.groupSymbol = None
        self.groupBarline = None
        self.groupTime = None # empty element / boolean value

    def _getComponents(self):
        c = []
        c.append(('group-name', self.groupName))
        c.append(('group-name-display', self.groupNameDisplay))
        c.append(('group-abbreviation', self.groupAbbreviation))
        c.append(('group-abbreviation-display', self.groupAbbreviationDisplay))
        c.append(('group-symbol', self.groupSymbol))
        c.append(('group-barline', self.groupBarline))
        c.append(('group-time', self.groupTime))
        # editorial
        return c

    def setDefaults(self):
        self.set('group-name', defaults.partGroup)
        self.set('group-abbreviation', defaults.partGroupAbbreviation)



class ScorePart(MusicXMLElement):
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'score-part'
        # attributes
        self._attr['id'] = None
        # simple elements
        self.partName = None
        self.partAbbreviation = None
        # component objects
        self.scoreInstrumentList = [] # list of objects
        self.midiInstrumentList = [] # list of objects

    def _getComponents(self):
        c = []
        # identificationi
        c.append(('part-name', self.partName))
        # part-name-display
        c.append(('part-abbreviation', self.partAbbreviation))
        # part-abbreviation-display
        # group
        c = c + self.scoreInstrumentList
        # midi-device
        c = c + self.midiInstrumentList
        return c

    def setDefaults(self):
        self.set('partName', defaults.partName)
        self.set('id', defaults.partId)


class ScoreInstrument(MusicXMLElement):
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'score-instrument'
        # attributes
        self._attr['id'] = None
        # simple element
        self.instrumentName = None
        self.instrumentAbbreviation = None
        self.solo = None # boolean, empty tag
        self.ensemble = None # number or empty

    def _getComponents(self):
        c = []
        c.append(('instrument-name', self.instrumentName))
        c.append(('instrument-abbreviation', self.instrumentAbbreviation))
        c.append(('solo', self.solo))
        c.append(('ensemble', self.ensemble))
        return c



class MIDIInstrument(MusicXMLElement):
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'midi-instrument'
        # attribute
        # refers to score instrument that this applies to
        self._attr['id'] = None
        # simple elements
        self.midiChannel = None
        self.midiName = None 
        self.midiBank = None 
        self.midiProgram = None 
        self.midiUnpitched = None # specified note number for perc,1 to 128
        self.volume = None # from 0 to 100
        self.pan = None # from -180 to 180, where -90 is hard left
        self.elevation = None # from -180 to 180, where 90 is directly above

    def _getComponents(self):
        c = []
        c.append(('midi-channel', self.midiChannel))
        c.append(('midi-name', self.midiName))
        c.append(('midi-bank', self.midiBank))
        c.append(('midi-program', self.midiProgram))
        c.append(('midi-unpitched',self.midiUnpitched))
        c.append(('volume',self.volume))
        c.append(('pan', self.pan))
        c.append(('elevation', self.elevation))
        return c



class Part(MusicXMLElementList):
    '''This assumes a part-wise part'''
    def __init__(self):
        MusicXMLElementList.__init__(self)
        self._tag = 'part'
        # attributes
        self._attr['id'] = None
        # component objects
        self.componentList = [] # a list of measure objects

    def _getComponents(self):
        return self.componentList

    def setDefaults(self):
        # might need to do this a different way
        self.set('id', defaults.partId)


class Measure(MusicXMLElementList):
    def __init__(self):
        MusicXMLElementList.__init__(self)
        self._tag = 'measure'
        # not all measures store an attributes object
        # yet, a measure can refere to a divisons setting
        # established in previous measures
        self.external['attributes'] = None
        self.external['divisions'] = None

        # attributes
        self._attr['number'] = None
        self._attr['implicit'] = None
        self._attr['width'] = None
        # elements
        self.attributesObj = None # an object
        self.componentList = [] # a list notes and other things

        self._crossReference['attributesObj'] = ['attributes']

    def _getComponents(self):
        c = [] # have not checked order of this
        c.append(self.attributesObj)
        c += self.componentList
        return c

    def setDefaults(self):
        self.set('number', 1)
        attributes = Attributes()
        attributes.setDefaults()
        self.set('attributes', attributes)
        self.external['divisions'] = attributes.get('divisions')


    def update(self):
        '''This method looks at all note, forward, and backup objects and updates note start times'''
        counter = 0
        noteThis = None
        noteNext = None
        for pos in range(len(self.componentList)):
            obj = self.componentList[pos]
            if obj.tag == 'forward':
                counter += int(obj.duration)
                continue
            elif obj.tag == 'backup':
                counter -= int(obj.duration)
                continue
            elif obj.tag == 'note':
                noteThis = obj
                # get a reference to the next note
                if pos+1 == len(self.componentList):
                    noteNext = None
                else:
                    for posSub in range(pos+1, len(self.componentList)):
                        if self.componentList[posSub].tag == 'note':
                            noteNext = self.componentList[posSub]
                            break
                obj.external['start'] = counter
                # only increment if next note is not a chord
                if noteNext != None and not noteNext.chord:
                    if obj.duration == None: # a grace note
                        pass
                    else:
                        counter = counter + int(obj.duration)
            else: # direction elements are found here
                pass




class Attributes(MusicXMLElement):
    # store measure data; assuming that there is one per measure

    # TODO: timeList needs to be replaced by a single
    # time object.

    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'attributes'
        # simple elements
        self.divisions = None
        self.staves = None 
        # complex elements
        self.keyList = [] # there can be one key for each staff in a Part
        # more than one pair of beat and beat-type is used for composite signatures
        self.timeList = [] 
        self.clefList = []
        self.transposeObj = None # needs to be an ojbect
        self.measureStyleObj = None # for slash notation, mult rests

        # not yet implemented
        self.staffDetails = None # shows different stave styles
        self.directive = None

        self._crossReference['timeList'] = ['time']
        self._crossReference['clefList'] = ['clef']


    def _getComponents(self):
        c = []
        c.append(('divisions', self.divisions))
        c = c + self.keyList
        c = c + self.timeList
        c.append(('staves', self.staves))
        # part symbol
        # instruments
        c = c + self.clefList  
        # staff details
        c.append(self.transposeObj)
        # directive
        c.append(self.measureStyleObj)
        return c

    def setDefaultDivisions(self):
        '''Utility to just set the divisioins parameters
        '''
        self.set('divisions', defaults.divisionsPerQuarter)

    def setDefaults(self):
        self.set('divisions', defaults.divisionsPerQuarter)
        mxTime = Time()
        mxTime.setDefaults()
        self.timeList.append(mxTime)
        mxClef = Clef()
        mxClef.setDefaults()
        self.clefList.append(mxClef)
        mxKey = Key()
        mxKey.setDefaults()
        self.keyList.append(mxKey)

class Key(MusicXMLElement):
    # permits traditional and non-traditional keys
    # non traditional keys use key-step and key-alter pairs
    # traditional uses fifths, mode
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'key'

        # attribute
        # optional attributes that refers to staff numbers
        self._attr['number'] = None
        # cancel is given as a fifths value of the canceld key
        self.cancel = None # if a previous key signature should be canceled
        self.fifths = None
        self.mode = None
        # non-traditional keys are defined as three tags
        # key-step, key-alter, and key-octave; it is not clear if these 
        # need to be in order; best to store objects for each
        self.nonTraditionalKeyList = [] # a list of objects

    def _getComponents(self):
        c = []
        c.append(('cancel', self.cancel))
        c.append(('fifths', self.fifths))
        c.append(('mode', self.mode))
        c = c + self.nonTraditionalKeyList
        return c

    def setDefaults(self):
        self.set('fifths', defaults.keyFifths)
        self.set('mode', defaults.keyMode)


class KeyStep(MusicXMLElement):
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'key-step'
        self.charData = None # a number
        
class KeyAlter(MusicXMLElement):
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'key-alter'
        self.charData = None # a number


class KeyOctave(MusicXMLElement):
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'key-octave'
        self.charData = None # a number
        self._attr['number'] = None

class Transpose(MusicXMLElement):
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'transpose'
        # simple elements
        self.diatonic = None 
        self.chromatic= None 
        self.octaveChange = None 
        self.double = False # boolean

    def _getComponents(self):
        c = []
        c.append(('diatonic', self.diatonic))
        c.append(('chromatic', self.chromatic))
        c.append(('octave-change', self.octaveChange))
        c.append(('double', self.double))
        return c

class Time(MusicXMLElement):
    # there may be more than one time obj per attribute/measure
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'time'
        # attributes
        self._attr['symbol'] = None
        self._attr['number'] = None
        # simple elements
        self.componentList = [] # a list of beats and beatType
        #self.beats = None 
        #self.beatType = None
        self.senzaMisura = None # an empty element, but boolean here

    def _getComponents(self):
        c = []
        c += self.componentList # beats and beatType
        #c.append(('beats', self.beats))
        #c.append(('beat-type', self.beatType))
        c.append(('senza-misura', self.senzaMisura))
        return c

    def setDefaults(self):
        #self.set('beats', defaults.meterNumerator)
        #self.set('beat-type', defaults.meterDenominatorBeatType)
        beats = Beats(defaults.meterNumerator)
        beatType = BeatType(defaults.meterDenominatorBeatType)

        self.componentList.append(beats)
        self.componentList.append(beatType)


class Beats(MusicXMLElement):
    def __init__(self, charData=None):
        MusicXMLElement.__init__(self)
        self._tag = 'beats'
        self.charData = charData

class BeatType(MusicXMLElement):
    def __init__(self, charData=None):
        MusicXMLElement.__init__(self)
        self._tag = 'beat-type'
        self.charData = charData




class Clef(MusicXMLElement):
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'clef'
        # attributes:
        self._attr['number'] = None
        self._attr['additional'] = None
        # elements
        self.sign = None
        self.line = None
        self.clefOctaveChange = None # integer for transposing clefs

        self._crossReference['clefOctaveChange'] = ['octaveChange']


    def _getComponents(self):
        c = []
        c.append(('sign', self.sign))
        c.append(('line', self.line))
        c.append(('clef-octave-change', self.clefOctaveChange))
        return c

    def setDefaults(self):
        self.set('sign', defaults.clefSign)
        self.set('line', defaults.clefLine)


class Direction(MusicXMLElementList):
    '''One or more Direction objects are found in measures, after an attributes
    object. Within the Direction object may be a number of objects, including DirectionType, Sound.
    '''
    def __init__(self):
        MusicXMLElementList.__init__(self)
        self._tag = 'direction'
        # attributes
        self._attr['placement'] = None
        # elements
        self.componentList = []

    def _getComponents(self):
        c = []
        c = c + self.componentList
        return c

    def getDynamicMark(self):
        '''Search this direction and determine if it contains a dynamic mark, return, otherwise, return None

        >>> a = Direction()
        >>> b = DirectionType()
        >>> c = Dynamics()
        >>> d = DynamicMark('f')
        >>> c.append(d)
        >>> b.append(c)
        >>> a.append(b)
        >>> a.getDynamicMark() != None
        True
        '''
        for directionType in self.componentList:
            for obj in directionType:
                if isinstance(obj, Dynamics):
                    for subobj in obj:
                        if isinstance(subobj, DynamicMark):
                            return subobj
        return None

    def getWedge(self):
        '''Search this direction and determine if it contains a dynamic mark.

        >>> a = Direction()
        >>> b = DirectionType()
        >>> c = Wedge('crescendo')
        >>> b.append(c)
        >>> a.append(b)
        >>> a.getWedge() != None
        True
        '''
        for directionType in self.componentList:
            for obj in directionType:
                if isinstance(obj, Wedge):
                    return obj
        return None



class DirectionType(MusicXMLElementList):
    '''DirectionType stores objects like Pedal, dynamics, wedge
    '''
    def __init__(self):
        MusicXMLElementList.__init__(self)
        self._tag = 'direction-type'
        # attributes
        # elements
        self.componentList = []

    def _getComponents(self):
        c = []
        c = c + self.componentList
        return c


class MeasureStyle(MusicXMLElement):
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'measure-style'
        # elements
        self.multipleRest = None

    def _getComponents(self):
        c = []
        c.append(('multiple-rest', self.multipleRest))
        return c



class Barline(MusicXMLElement):
    # this may need to be refined if there are more bar options
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'barline'
        # attributes
        self._attr['location'] = None
        # elements
        self.barStyle = None
        self.endingObj = None
        self.repeatObj = None

    def _getComponents(self):
        c = []
        c.append(('bar-style', self.barStyle))
        # editorial
        # wavy-line
        # segno
        # coda
        # fermata
        c.append(self.endingObj)
        c.append(self.repeatObj)
        return c


class Ending(MusicXMLElement):
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'ending'
        # attributes
        self._attr['type'] = None
        self._attr['number'] = None


class Repeat(MusicXMLElement):
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'repeat'
        # attributes
        self._attr['direction'] = None


class Note(MusicXMLElement):
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'note'
        # note objects need a special attribute for start count
        # this value represents the start time as specified by MusicXML
        # backup and forward tags, and is in division units per Measure
        # this value can only be relative to measure, as each measure
        # can have a different divisions (music xml stats that forward/backward
        # should not cross measure boundaries
        # this can also be used to determine if note is part of a chord
        self.external['start'] = None
        # notes can optionally store a reference to the mesure object that 
        # contains them. 
        self.external['measure'] = None
        # nots can optional store a reference to the last encounted attributes
        # from whatever previous meassure had an attributes object
        # this is needed to get divisions from arbitrary notes
        self.external['attributes'] = None
        # in some cases the last attributes reference may not be enough 
        # to find the divisions; thus, we need to store a ref to the last
        # enctountered divisions value
        self.external['divisions'] = None

        # attributes: mostly position information default-x, etc
        self._attr['color'] = None
        self._attr['print-object'] = None # may be yes or no
        self._attr['print-dot'] = None # may be yes or no
        self._attr['print-spacing'] = None # may be yes or no

        # simple elements
        self.chord = False # boolean, default is false
        self.duration = None # number, in div per quarter
        self.voice = None # numbers
        self.type = None # string, representing long through 256th note
        self.stem = None # string
        self.staff = None # number, for parts w/ > 1 staff 

        self.restObj = None # if not None, a rest
        self.accidentalObj = None
        self.graceObj = None
        self.noteheadObj = None
        self.pitchObj = None # object
        self.timeModificationObj = None
        self.notationsObj = None # container of heterogenous objects

        self.lyricList = []
        self.dotList = [] # one or more dot objects may be defined
        self.beamList = [] # a list of Beam objects
        self.tieList = [] # list of objects, at most two; for sound, not notation

        self._crossReference['pitchObj'] = ['pitch']
        self._crossReference['graceObj'] = ['grace']
        self._crossReference['accidentalObj'] = ['accidental']
        self._crossReference['timeModificationObj'] = ['timemodification']
        self._crossReference['noteheadObj'] = ['notehead']
        self._crossReference['notationsObj'] = ['notations']
        self._crossReference['restObj'] = ['rest']


    def _getComponents(self):
        c = []
        c.append(self.graceObj)
        c.append(('chord', self.chord))
        c.append(self.pitchObj)
        c.append(self.restObj)
        # next is duration and tie
        c.append(('duration', self.duration))
        c = c + self.tieList
        # editorial voice group contains footnote, level, voice
        c.append(('voice', self.voice))
        # remaining
        c.append(('type', self.type))
        c = c + self.dotList
        c.append(self.accidentalObj)
        c.append(self.timeModificationObj)
        c.append(('stem', self.stem))
        c.append(self.noteheadObj)
        c.append(('staff', self.staff))
        c = c + self.beamList
        c.append(self.notationsObj)
        c = c + self.lyricList
        return c

    def setDefaults(self):
        mxPitch = Pitch()
        mxPitch.setDefaults()
        self.set('pitch', mxPitch)
        self.set('type', defaults.durationType)
        self.set('duration', defaults.divisionsPerQuarter)

    def _mergeSpecial(self, new, other, favorSelf=True):
        '''Provide handling of merging when given an object of a different class.
        '''
        if isinstance(other, Pitch): 
            # if local pitch is None
            if self.pitchObj == None:
                new.pitchObj = other
            # if local pitch is not None, new already has it from copy
            # only set of favorSelf is not true
            elif self.pitchObj != None:
                if not favorSelf:
                    new.pitchObj = other


#     def addTie(self, tieType):
#         '''Convenience for settting up ties. Can only be used when 
#         not manually configure mxNotations
#         '''
#         if tieType not in ['start', 'stop']:
#             raise MusicXMLException('bad tie type %s' % tieType)
#         mxTie = Tie()
#         mxTie.set('type', tieType) # start, stop
#         self.tieList.append(mxTie)
# 
#         mxTied = Tied()
#         mxTied.set('type', tieType) 
#         self.notationsObj.append(mxTied)
#         



class Forward(MusicXMLElement):
    def __init__(self, type=None):
        MusicXMLElement.__init__(self)
        self._tag = 'forward'
        # attributes
        # elements
        self.duration = None

    def _getComponents(self):
        c = []
        c.append(('duration', self.duration))
        return c


class Backup(MusicXMLElement):
    def __init__(self, type=None):
        MusicXMLElement.__init__(self)
        self._tag = 'backup'
        # attributes
        # elements
        self.duration = None

    def _getComponents(self):
        c = []
        c.append(('duration', self.duration))
        return c


class Rest(MusicXMLElementList):
    def __init__(self, type=None):
        MusicXMLElementList.__init__(self)
        self._tag = 'rest'
        self.componentList = [] # stores display-step, display-octave

    def _getComponents(self):
        return self.componentList 

    # temporary; this needs to be set based on clef
    # this could take a clef as an argument
    def setDefaults(self):
        displayStep = DisplayStep()
        displayStep.set('charData', 'B') # was D4
        displayOctave = DisplayOctave()
        displayOctave.set('charData', '4')
        self.append(displayStep)
        self.append(displayOctave)


class DisplayStep(MusicXMLElement):
    def __init__(self, type=None):
        MusicXMLElement.__init__(self)
        self._tag = 'display-step'
        self.charData = None # only content

class DisplayOctave(MusicXMLElement):
    def __init__(self, type=None):
        MusicXMLElement.__init__(self)
        self._tag = 'display-octave'
        self.charData = None # only content




class Notations(MusicXMLElementList):
    def __init__(self, type=None):
        MusicXMLElementList.__init__(self)
        self._tag = 'notations'
        self.componentList = []  # objects tt are part of this node

    def _getComponents(self):
        return self.componentList 

    def getTuplets(self):
        '''A quick way to get all tuplets; there is likely only one
        '''
        post = []        
        for part in self.componentList:
            if isinstance(part, Tuplet):
                post.append(part)
        return post

    def getTieds(self):
        '''A quick way to get all tied objects; there is likely only one
        '''
        post = []        
        for part in self.componentList:
            if isinstance(part, Tied):
                post.append(part)
        return post

    def getArticulations(self):
        '''A quick way to get all articulations objects; there may be more than 
        one.

        Returns a list of ArticulationMark objects
        '''
        post = []        
        for part in self.componentList:
            if isinstance(part, Articulations):
                # note: articulation marks are being stripped out
                post += part.componentList
        return post

    def getFermatas(self):
        '''Get a fermata.
        '''
        post = []        
        for part in self.componentList:
            if isinstance(part, Fermata):
                post.append(part)
        return post





class Dynamics(MusicXMLElementList):
    def __init__(self, type=None):
        MusicXMLElementList.__init__(self)
        self._tag = 'dynamics'
        # attributes
        self._attr['placement'] = None
        self._attr['relative-y'] = None
        self._attr['relative-x'] = None
        self._attr['default-y'] = None
        self._attr['default-x'] = None
        # elements are dynamic tags
        self.componentList = []  # objects tt are part of this node

    def _getComponents(self):
        c = []
        c = c + self.componentList 
        return c

class Articulations(MusicXMLElementList):
    def __init__(self, type=None):
        MusicXMLElementList.__init__(self)
        self._tag = 'articulations'
        # attributes
        # elements are articulation marks
        self.componentList = []  # objects tt are part of this node

    def _getComponents(self):
        c = []
        c = c + self.componentList 
        return c

class Technical(MusicXMLElementList):
    def __init__(self, type=None):
        MusicXMLElementList.__init__(self)
        self._tag = 'technical'
        # attributes
        # elements are dynamics
        self.componentList = []  # objects tt are part of this node

    def _getComponents(self):
        c = []
        c = c + self.componentList 
        return c

class DynamicMark(MusicXMLElement):
    '''This is not an XML object in the normal sense, but a container for all XML dynamic tags. Dynamic tags have no attributes or elements. Tags inlcude common marks such as p, pp, ff, etc.'''

    def __init__(self, tag):
        MusicXMLElement.__init__(self)
        if tag not in DYNAMIC_MARKS and tag != 'other-dynamics':
            raise MusicXMLException('no known dynamic tag %s' % tag)
        self._tag = tag
        # character data 
        self.charData = None # found only in other-dynamics tag


class ArticulationMark(MusicXMLElement):
    '''This is not an XML object, but a container for all XML articulation tags.
    '''
    def __init__(self, tag):
        MusicXMLElement.__init__(self)
        if tag not in ARTICULATION_MARKS and tag != 'other-articulation':
            raise MusicXMLException('no known articulation tag %s' % tag)
        self._tag = tag
        # attributes
        self._attr['placement'] = None
        # character data 
        self.charData = None # found only in other-articulation tag

class TechnicalMark(MusicXMLElement):
    '''This is not an XML object, but a container for all XML technical tags.
    '''
    def __init__(self, tag):
        MusicXMLElement.__init__(self)
        if tag not in TECHNICAL_MARKS and tag != 'other-technical':
            raise MusicXMLException('no known technical tag %s' % tag)
        self._tag = tag
        # attributes
        self._attr['type'] = None
        # character data 
        self.charData = None # found in fingering, pluck, other-artic


class Grace(MusicXMLElement):
    def __init__(self, type=None):
        MusicXMLElement.__init__(self)
        self._tag = 'grace'
        # attributes
        self._attr['steal-time-previous'] = None
        self._attr['steal-time-following'] = None
        self._attr['make-time'] = None
        self._attr['slash'] = None



class Wedge(MusicXMLElement):
    def __init__(self, type=None):
        MusicXMLElement.__init__(self)
        self._tag = 'wedge'
        # attributes
        self._attr['type'] = None # crescendo, stop, or diminuendo
        self._attr['spread'] = None
        self._attr['relative-y'] = None
        self._attr['relative-x'] = None




class Ornaments(MusicXMLElementList):
    def __init__(self, type=None):
        MusicXMLElementList.__init__(self)
        self._tag = 'ornaments'
        self.componentList = []  # objects tt are part of this node

    def _getComponents(self):
        return self.componentList 



class TrillMark(MusicXMLElement):
    def __init__(self, type=None):
        MusicXMLElement.__init__(self)
        self._tag = 'trill-mark'
        self._attr['placement'] = None # above/below





class Notehead(MusicXMLElement):
    def __init__(self, type=None):
        MusicXMLElement.__init__(self)
        self._tag = 'notehead'
        # attributes
        self._attr['filled'] = None
        self._attr['parentheses'] = None
        # character data 
        self.charData = None

# valid note heads values
#"slash", "triangle", "diamond", "square", "cross", "x" , "circle-x", "inverted, triangle", "arrow down", "arrow up", "slashed", "back slashed", "normal", "cluster", "none", "do", "re", "mi", "fa", "so", "la", "ti" 

class Dot(MusicXMLElement):
    def __init__(self, type=None):
        MusicXMLElement.__init__(self)
        self._tag = 'dot'
    

class Tie(MusicXMLElement):
    def __init__(self, type=None):
        MusicXMLElement.__init__(self)
        self._tag = 'tie'
        # attributes
        self._attr['type'] = type


class Fermata(MusicXMLElement):
    def __init__(self, type=None):
        MusicXMLElement.__init__(self)
        self._tag = 'fermata'
        # attributes
        self._attr['type'] = type # upright
        # character data
        self.charData = None


class Accidental(MusicXMLElement):
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'accidental'
        # attributes
        self._attr['editorial'] = None # yes or no
        # character data
        self.charData = None

class Slur(MusicXMLElement):
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'slur'
        # attributes
        self._attr['number'] = None
        self._attr['placement'] = None
        self._attr['type'] = None


class Tied(MusicXMLElement):
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'tied'
        # attributes
        self._attr['type'] = None
        self._attr['number'] = None


class Beam(MusicXMLElement):
    '''Beams are specified is individual objects for each beam, in order, where the beam number refers to its duration representation (8th, 16th, etc) and its character data specifies whether it is begin/continue/end (for normal beams) or backward hook/forward wook (for beams that do not continue are attached only to the staff). These character data values can be mixed: one beam can continue while another can hook or end. 

1 = 8th
2 = 16th
3 = 32th
4 = 64th
5 = 128th
6 = 256th

From musicxml.xsd:

Beam values include begin, continue, end, forward hook, and backward hook. Up to six concurrent beam levels are available to cover up to 256th notes. The repeater attribute, used for tremolos, needs to be specified with a "yes" value for each beam using it. Beams that have a begin value can also have a fan attribute to indicate accelerandos and ritardandos using fanned beams. The fan attribute may also be used with a continue value if the fanning direction changes on that note. The value is "none" if not specified.
	
Note that the beam number does not distinguish sets of beams that overlap, as it does for slur and other elements. Beaming groups are distinguished by being in different voices and/or the presence or absence of grace and cue 
    '''
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'beam'
        # attributes
        self._attr['number'] = None
        self._attr['repeater'] = None # yes or no
        self._attr['fan'] = None # present or not present
        # single text element
        # begin, continue, end, forward hook, backward hook
        self.charData = None # string, continue, begin, etc

class Lyric(MusicXMLElement):
    '''Multiple Lyric objects can be defined within a single Note.
    '''
    def __init__(self, number=None):
        MusicXMLElement.__init__(self)
        self._tag = 'lyric'
        # attributes
        # can be a number for mult line or name (e.g. chorus)
        self._attr['number'] = None
        # entities
        self.syllabic = None
        self.text = None

    def filterLyric(self, text):
        '''
        Remove and fix character strings that cause problems in MusicXML
        '''
        # this results in incorrect encoding of </>
        #text = xml.sax.saxutils.escape(text)
        text = text.replace('>', unichr(62))
        text = text.replace('<', unichr(60))
        text = text.replace('&', unichr(38))

        # need to remove hyphens; but &mdash; and similar do not work
        text = text.replace('-', unichr(8211))
        return text

    def _getComponents(self):
        c = []
        c.append(('syllabic', self.syllabic))
        # only filter when getting components
        c.append(('text', self.filterLyric(self.text)))
        return c


class Pitch(MusicXMLElement):
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'pitch'
        # simple entities
        self.step = None # string
        self.alter = None # string
        self.octave = None # string

    def _getComponents(self):
        c = []
        c.append(('step', self.step))
        c.append(('alter', self.alter))
        c.append(('octave', self.octave))
        return c

    def setDefaults(self):
        self.set('step', defaults.pitchStep)
        self.set('octave', defaults.pitchOctave)

class TimeModification(MusicXMLElement):
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'time-modification'
        # simple elements
        self.actualNotes = None
        self.normalNotes = None
        self.normalType = None
        self.normalDot = None

    def _getComponents(self):
        c = []
        c.append(('actual-notes', self.actualNotes))
        c.append(('normal-notes', self.normalNotes))
        c.append(('normal-type', self.normalType))
        c.append(('normal-dot', self.normalDot))
        return c


class Tuplet(MusicXMLElement):
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'tuplet'
        # attributes
        self._attr['bracket'] = None
        self._attr['number'] = None
        self._attr['type'] = None
        self._attr['show-number'] = None
        self._attr['show-type'] = None
        self._attr['line-shape'] = None
        self._attr['placement'] = None




#-------------------------------------------------------------------------------
class Handler(xml.sax.ContentHandler):
    '''extact data for all parts'''
   
    def __init__(self, tagLib=None):
        if tagLib == None:
            self.t = TagLib()
        else:
            self.t = tagLib

        # this might be used in startElement() to speed up processing
        # this is not opperational yet
        self._currentObj = None # store current mx object for processing
        self._currentTag = None # store current tag object

        # all objects built in processing
        # scoreObj is returned as content, contains everything
        # stores version of m21 used to create this file
        self._scoreObj = Score(music21.VERSION) 

        # component objects
        self._creatorObj = None
        self._workObj = None
        self._identificationObj = None
        self._encodingObj = None
        self._softwareObj = None

        self._partListObj = None  # added to score obj
        self._partGroupObj = None
        self._scorePartObj = None
        self._scoreInstrumentObj = None
        self._midiInstrumentObj = None

        self._parts = [] # added to score obj

        self._partObj = None
        self._measureObj = None
        self._noteObj = None
        self._forwardObj = None
        self._backupObj = None

        self._restObj = None
        self._displayStepObj = None
        self._displayOctaveObj = None

        self._pitchObj = None
        self._beamObj = None
        self._barlineObj = None
        self._endingObj = None
        self._repeatObj = None
        self._attributesObj = None
        # need to store last attribute obj accross multiple measures
        self._attributesObjLast = None
        # need to store last divisions accross mulitple mesausers
        self._divisionsLast = None

        self._keyObj = None
        self._keyStepObj = None
        self._keyAlterObj = None
        self._keyOctaveObj = None
        self._noteheadObj = None
        self._measureStyleObj = None

        self._transposeObj = None
        self._notationsObj = None
        self._slurObj = None
        self._tiedObj = None
        self._fermataObj = None

        self._ornamentsObj = None
        self._trillMarkObj = None

        self._timeObj = None
        # store last encountered
        self._timeObjLast = None

        self._clefObj = None
        self._tieObj = None
        self._accidentalObj = None
        self._lyricObj = None
        self._dotObj = None

        self._timeModificationObj = None
        self._tupletObj = None
        self._dynamicsObj = None
        self._dynamicMarkObj = None
        self._articulationsObj = None
        self._articulationMarkObj = None
        self._articulationsObj = None
        self._articulationMarkObj = None
        self._technicalObj = None
        self._technicalMarkObj = None

        self._directionObj = None
        self._directionTypeObj = None
        self._graceObj = None
        self._wedgeObj = None

    def setDocumentLocator(self, locator):
        '''A locator object can be used to get line numbers from the XML document.'''
        self._locator = locator

    def _getLocation(self):
        '''Using the locator object, get the present location in the file.'''
        line = str(self._locator.getLineNumber()).ljust(4)
        col = str(self._locator.getColumnNumber()).ljust(4)
        return 'line %s column %s' % (line, col)

    def _debugTagStr(self, head, name, attrs=None):
        '''Provide a formatted string with a header string and the tag name. Also includes location information. '''
        msg = []
        msg.append(head.ljust(8))
        tag = '<%s>' % name
        msg.append(tag.ljust(18))
        msg.append(self._getLocation())
        return ''.join(msg)


    def characters(self, charData):
        '''Because each _Handler sub-class defines its own _tags, 
        and because each Tag knows whether it is to receive character data or not, 
        this method can be found in the base-class and need not be defined for each sub-class.
        '''
        # in all but a very few cases self.t[tag].charData = charData is 
        # sufficient for getting charData. however, in a few cases this
        # will not gather all data and cause very unexpected results
        for tag in self.t.tagsCharData:
            if self.t[tag].status:
                self.t[tag].charData += charData
                break


    #---------------------------------------------------------------------------
    def startElement(self, name, attrs):
        environLocal.printDebug([self._debugTagStr('start', name, attrs)], common.DEBUG_ALL)

        if name in self.t.tagsAll:
            self._currentTag = self.t[name]
            self._currentTag.start() 

            # presently, doing this breaks xml processing; not sure why
#             if self.t[name].className != None:
#                 self._currentObj = self.t[name].className()
#                 #environLocal.printDebug(['got', self._currentObj])
#                 self._currentObj.loadAttrs(attrs)
#                 self._currentObj = None

        
        # place most commonly used tags first
        if name == 'note':
            self._noteObj = Note()      
            # store a reference to the measure containing
            self._noteObj.external['measure'] = self._measureObj
            self._noteObj.external['attributes'] = self._attributesObjLast
            self._noteObj.external['divisions'] = self._divisionsLast
            self._noteObj.loadAttrs(attrs)

        elif name == 'beam':
            self._beamObj = Beam()
            self._beamObj.loadAttrs(attrs)

        elif name == 'pitch':
            self._pitchObj = Pitch()

        elif name == 'notations': 
            self._notationsObj = Notations()

        elif name == 'rest':
            self._restObj = Rest()

        elif name == 'measure':
            self._measureObj = Measure()
            self._measureObj.external['attributes'] = self._attributesObjLast
            self._measureObj.external['divisions'] = self._divisionsLast
            # some attributes definitions do store time, and refer only
            # to the last defined time value; store here for access
            self._measureObj.external['time'] = self._timeObjLast
            self._measureObj.loadAttrs(attrs)


        elif name == 'slur':
            self._slurObj = Slur()
            self._slurObj.loadAttrs(attrs)


        elif name == 'accidental':
            self._accidentalObj = Accidental()
            self._accidentalObj.loadAttrs(attrs)

        elif name == 'tie':
            self._tieObj = Tie()
            self._tieObj.loadAttrs(attrs)

        elif name == 'tied':
            self._tiedObj = Tied()
            self._tiedObj.loadAttrs(attrs)


        elif name == 'direction': 
            self._directionObj = Direction()
            self._directionObj.loadAttrs(attrs)

        elif name == 'direction-type': 
            self._directionTypeObj = DirectionType()


        elif name == 'dot': 
            self._dotObj = Dot()


        elif name == 'dynamics': 
            self._dynamicsObj = Dynamics()
            self._dynamicsObj.loadAttrs(attrs) # loads placement and pos args

        elif name == 'time-modification': 
            self._timeModificationObj = TimeModification()

        elif name == 'tuplet': 
            self._tupletObj = Tuplet()
            self._tupletObj.loadAttrs(attrs)

        elif name == 'forward':
            self._forwardObj = Forward()

        elif name == 'backup':
            self._backupObj = Backup()

        elif name == 'articulations': 
            self._articulationsObj = Articulations()

        elif name == 'attributes':
            self._attributesObj = Attributes()



        elif name == 'lyric':
            self._lyricObj = Lyric()
            self._lyricObj.loadAttrs(attrs)

        elif name == 'trill-mark': 
            self._trillMarkObj = TrillMark()
            self._trillMarkObj.loadAttrs(attrs)


        elif name == 'grace':
            #environLocal.printDebug('creating mxGrace object')
            self._graceObj = Grace()
            self._graceObj.loadAttrs(attrs)


        elif name == 'notehead': 
            self._noteheadObj = Notehead()
            self._noteheadObj.loadAttrs(attrs)


        elif name == 'technical': 
            self._technicalObj = Technical()

        elif name == 'wedge': 
            self._wedgeObj = Wedge()
            self._wedgeObj.loadAttrs(attrs)

        elif name == 'ornaments': 
            self._ornamentsObj = Ornaments()

        elif name in DYNAMIC_MARKS:
            self._dynamicMarkObj = DynamicMark(name)

        elif name == 'other-dynamics':
            self._dynamicMarkObj = DynamicMark(name)

        elif name in ARTICULATION_MARKS:
            self._articulationMarkObj = ArticulationMark(name)
            self._articulationMarkObj.loadAttrs(attrs)

        elif name == 'other-articulation':
            self._articulationMarkObj = ArticulationMark(name)

        elif name in TECHNICAL_MARKS:
            self._technicalMarkObj = TechnicalMark(name)
            self._technicalMarkObj.loadAttrs(attrs)

        elif name == 'other-technical':
            self._technicalMarkObj = TechnicalMark(name)

        elif name == 'fermata':
            self._fermataObj = Fermata()
            self._fermataObj.loadAttrs(attrs)


        elif name == 'score-partwise':
            self._scoreObj.loadAttrs(attrs)
            self._scoreObj.format = 'score-partwise'

        elif name == 'score-timewise':
            self._scoreObj.loadAttrs(attrs)
            self._scoreObj.format = 'score-timewise'
            raise MusicXMLException('timewise is not supported')

        elif name == 'work':
            self._workObj = Work()

        elif name == 'identification':
            self._identificationObj = Identification()

        elif name == 'creator':
            self._creatorObj = Creator()
            self._creatorObj.loadAttrs(attrs)

        elif name == 'encoding':
            self._encodingObj = Encoding()

        elif name == 'software':
            self._softwareObj = Software()


        # formerly part of handler partList
        elif name == 'part-list':
            self._partListObj = PartList()

        elif name == 'part-group':
            self._partGroupObj = PartGroup()
            self._partGroupObj.loadAttrs(attrs)

        elif name == 'score-part':
            self._scorePartObj = ScorePart()
            self._scorePartObj.loadAttrs(attrs)

        elif name == 'score-instrument':
            self._scoreInstrumentObj = ScoreInstrument()
            self._scoreInstrumentObj.loadAttrs(attrs)

        elif name == 'midi-instrument': # maybe soud def tag
            self._midiInstrumentObj = MIDIInstrument()
            self._midiInstrumentObj.loadAttrs(attrs)


        # part of handler part
        elif name == 'part':
            self._partObj = Part()
            self._partObj.loadAttrs(attrs)

        elif name == 'key':
            self._keyObj = Key()

        elif name == 'key-step':
            self._keyStepObj = KeyStep()

        elif name == 'key-alter':
            self._keyAlterObj = KeyAlter()

        elif name == 'key-octave':
            self._keyOctaveObj = KeyOctave()
            self._keyOctaveObj.loadAttrs(attrs)

        elif name == 'transpose':
            self._transposeObj = Transpose()

        elif name == 'time':
            self._timeObj = Time()
            self._timeObj.loadAttrs(attrs)

        elif name == 'clef':
            self._clefObj = Clef()
            self._clefObj.loadAttrs(attrs)

        elif name == 'measure-style':
            self._measureStyleObj = MeasureStyle()

        elif name == 'display-step':
            self._displayStepObj = DisplayStep()

        elif name == 'display-octave':
            self._displayOctaveObj = DisplayOctave()

        elif name == 'barline':
            self._barlineObj = Barline()
            self._barlineObj.loadAttrs(attrs)

        elif name == 'ending':
            self._endingObj = Ending()
            self._endingObj.loadAttrs(attrs)

        elif name == 'repeat': 
            self._repeatObj = Repeat()
            self._repeatObj.loadAttrs(attrs)



    #---------------------------------------------------------------------------
    def endElement(self, name):
        environLocal.printDebug([self._debugTagStr('end', name)],  
                common.DEBUG_ALL)
    
        if name in self.t.tagsAll:
            self._currentObj = None # reset
            #environLocal.printDebug([self._currentTag.tag])

        # place most commonly used tags first
        if name == 'note':
            self._measureObj.componentList.append(self._noteObj)
            self._noteObj = None

        elif name == 'voice':
            if self._noteObj != None: # not a forward/backup tag
                self._noteObj.voice = self._currentTag.charData
            else: # inside of backup tag
                pass
                #environLocal.printDebug([' cannot deal with this voice', self._currentTag.charData])

        elif name == 'duration':
            if self._noteObj != None: # not a forward/backup tag
                self._noteObj.duration = self._currentTag.charData
            elif self._backupObj != None:
                self._backupObj.duration = self._currentTag.charData
            elif self._forwardObj != None:
                self._forwardObj.duration = self._currentTag.charData
            else: # ignoring figured-bass
                pass
                #raise MusicXMLException('cannot handle duration tag at: %s' % self._getLocation())

        elif name == 'type':
            self._noteObj.type = self._currentTag.charData

        elif name == 'stem':
            self._noteObj.stem = self._currentTag.charData

        elif name == 'beam':
            self._beamObj.charData = self._currentTag.charData
            self._noteObj.beamList.append(self._beamObj)
            self._beamObj = None

        elif name == 'pitch':
            self._noteObj.pitchObj = self._pitchObj
            self._pitchObj = None

        elif name == 'step':
            self._pitchObj.step = self._currentTag.charData

        elif name == 'octave':
            self._pitchObj.octave = self._currentTag.charData

        elif name == 'alter':
            self._pitchObj.alter = self._currentTag.charData


        elif name == 'notations': 
            self._noteObj.notationsObj = self._notationsObj
            self._notationsObj = None

        elif name == 'rest':
            self._noteObj.restObj = self._restObj
            self._restObj = None

        elif name == 'measure':
            # measures need to be stored in order; numbers may have odd values
            # X1, for example.
            # update note start times w/ measure utility method
            self._measureObj.update()
            self._partObj.componentList.append(self._measureObj)
            self._measureObj = None # clear to avoid mistakes


        elif name == 'slur': 
            self._notationsObj.componentList.append(self._slurObj)
            self._slurObj = None

        elif name == 'accidental':
            self._accidentalObj.charData = self._currentTag.charData
            self._noteObj.accidentalObj = self._accidentalObj
            self._accidentalObj = None


        elif name == 'tie':
            self._noteObj.tieList.append(self._tieObj)


        elif name == 'tied':
            self._notationsObj.componentList.append(self._tiedObj)
            self._tiedObj = None


        elif name == 'direction':
            # only append of direction has components
            if self._directionObj.componentList != []:
                self._measureObj.componentList.append(self._directionObj)
            self._directionObj = None

        elif name == 'direction-type': 
            # only append of direction-type has components
            if self._directionTypeObj.componentList != []:
                self._directionObj.componentList.append(self._directionTypeObj)
            self._directionTypeObj = None


        elif name == 'chord':
            self._noteObj.chord = True            

        elif name == 'dot': 
            self._noteObj.dotList.append(self._dotObj)


        elif name == 'dynamics': 
            if self._notationsObj != None: 
                self._notationsObj.componentList.append(self._dynamicsObj)
            elif self._directionTypeObj != None: 
                self._directionTypeObj.componentList.append(self._dynamicsObj)
            else:
                raise MusicXMLException('do not know where these dyanmics go', self._dynamicsObj)
            self._dynamicsObj = None


        elif name == 'lyric':
            if self._noteObj != None: # can be associtaed w/ harmony tag
                self._noteObj.lyricList.append(self._lyricObj)
            else:
                environLocal.printDebug(['cannot deal with this lyric'])
            self._lyricObj = None

        elif name == 'syllabic':
            self._lyricObj.syllabic = self._currentTag.charData

        elif name == 'text':
            self._lyricObj.text = self._currentTag.charData

        elif name == 'trill-mark': 
            self._ornamentsObj.append(self._trillMarkObj)
            self._trillMarkObj = None



        elif name == 'time-modification': 
            self._noteObj.timeModificationObj = self._timeModificationObj
            self._timeModificationObj = None

        elif name == 'actual-notes': 
            self._timeModificationObj.actualNotes = self._currentTag.charData

        elif name == 'normal-notes': 
            self._timeModificationObj.normalNotes = self._currentTag.charData

        elif name == 'normal-type':
            self._timeModificationObj.normalType = self._currentTag.charData

        elif name == 'normal-dot': 
            self._timeModificationObj.normalDot = self._currentTag.charData

        elif name == 'tuplet': 
            self._notationsObj.componentList.append(self._tupletObj)
            self._tupletObj = None




        elif name == 'attributes':
            self._measureObj.attributesObj = self._attributesObj
            # update last found
            self._attributesObjLast = copy.deepcopy(self._attributesObj)
            # remove current, as loaded into measure
            self._attributesObj = None

        elif name == 'divisions':
            self._attributesObj.divisions = self._currentTag.charData
            self._divisionsLast = self._currentTag.charData
    
        elif name == 'forward':
            self._measureObj.componentList.append(self._forwardObj)
            self._forwardObj = None

        elif name == 'backup':
            self._measureObj.componentList.append(self._backupObj)
            self._backupObj = None


        elif name == 'grace':
            self._noteObj.graceObj = self._graceObj
            self._graceObj = None


        elif name == 'notehead':
            self._noteheadObj.charData = self._currentTag.charData
            self._noteObj.noteheadObj = self._noteheadObj
            self._noteheadObj = None

        elif name == 'articulations': 
            self._notationsObj.componentList.append(self._articulationsObj)
            self._articulationsObj = None

        elif name == 'technical': 
            self._notationsObj.componentList.append(self._technicalObj)
            self._technicalObj = None

        elif name == 'wedge': 
            if self._directionTypeObj != None: 
                self._directionTypeObj.componentList.append(self._wedgeObj)
            else:
                raise MusicXMLException('do not know where this wedge goes', self._wedgeObj)
            self._wedgeObj = None

        elif name == 'ornaments': 
            self._notationsObj.append(self._ornamentsObj)
            self._ornamentsObj = None


        elif name in DYNAMIC_MARKS:
            self._dynamicsObj.componentList.append(self._dynamicMarkObj)
            self._dynamicMarkObj = None

        elif name == 'other-dynamics':
            self._dynamicMarkObj.charData = self._currentTag.charData            
            self._dynamicsObj.componentList.append(self._dynamicMarkObj)
            self._dynamicMarkObj = None

        elif name in ARTICULATION_MARKS:
            self._articulationsObj.componentList.append(
                self._articulationMarkObj)
            self._articulationMarkObj = None

        elif name == 'other-articulation':
            self._articulationMarkObj.charData = self._currentTag.charData            
            self._articulationsObj.componentList.append(self._dynamicMarkObj)
            self._articulationMarkObj = None

        elif name in TECHNICAL_MARKS:
            if self._technicalObj != None:
                self._technicalObj.componentList.append(self._technicalMarkObj)
            else:
                # could be w/n <frame-note>
                pass
            self._technicalMarkObj = None

        elif name == 'other-technical':
            self._technicalMarkObj.charData = self._currentTag.charData            
            self._technicalObj.componentList.append(self._technicalMarkObj)
            self._technicalMarkObj = None

        elif name == 'fermata':
            self._fermataObj.charData = self._currentTag.charData  
            self._notationsObj.componentList.append(self._fermataObj)
            self._fermataObj = None



        # formerly part of handler score
        elif name == 'movement-title':
            self._scoreObj.movementTitle = self._currentTag.charData

        elif name == 'movement-number':
            self._scoreObj.movementNumber = self._currentTag.charData

        elif name == 'work':
            self._scoreObj.workObj = self._workObj
            self._workObj = None

        elif name == 'work-title':
            self._workObj.workTitle = self._currentTag.charData

        elif name == 'work-number':
            self._workObj.workNumber = self._currentTag.charData

        elif name == 'identification':
            self._scoreObj.identificationObj = self._identificationObj
            self._identificationObj = None

        elif name == 'rights':
            self._identificationObj.rights = self._currentTag.charData

        elif name == 'creator':
            self._creatorObj.charData = self._currentTag.charData
            self._identificationObj.creatorList.append(self._creatorObj)
            self._creatorObj = None

        elif name == 'encoding':
            self._identificationObj.encodingObj = self._encodingObj
            self._encodingObj = None

        elif name == 'software':
            self._softwareObj.charData = self._currentTag.charData
            self._encodingObj.softwareList.append(self._softwareObj)
            self._softwareObj = None

        elif name == 'encoding-date':
            self._encodingObj.encodingDate = self._currentTag.charData


        # formerly part of handler part list
        elif name == 'part-group':
            self._partListObj.componentList.append(self._partGroupObj)
            self._partGroupObj = None 

        elif name == 'group-name':
            self._partGroupObj.groupName = self._currentTag.charData

        elif name == 'group-symbol':
            self._partGroupObj.groupSymbol = self._currentTag.charData

        elif name == 'group-barline':
            self._partGroupObj.groupBarline = self._currentTag.charData

        elif name == 'score-instrument':
            self._scorePartObj.scoreInstrumentList.append(
                self._scoreInstrumentObj)
            self._scoreInstrumentObj = None

        elif name == 'instrument-name':
            self._scoreInstrumentObj.instrumentName = self._currentTag.charData

        elif name == 'instrument-abbreviation':
            self._scoreInstrumentObj.instrumentAbbreviation = self._currentTag.charData

        elif name == 'score-part':
            self._partListObj.componentList.append(self._scorePartObj)
            self._scorePartObj = None 

        elif name == 'part-name':
            # copy completed character data and clear
            self._scorePartObj.partName = self._currentTag.charData

        elif name == 'score-instrument':                
            self._scorePartObj.scoreInstrumentList.append(
                self._scoreInstrumentObj)
            self._scoreInstrumentObj = None

        elif name == 'midi-instrument':                
            if self.t['score-part'].status: # may be in a <sound> def
                self._scorePartObj.midiInstrumentList.append( 
                    self._midiInstrumentObj)
                self._midiInstrumentObj = None
             
        elif name == 'midi-channel':
            if self.t['score-part'].status:
                self._midiInstrumentObj.midiChannel = self._currentTag.charData

        elif name == 'midi-program':
            if self.t['score-part'].status:
                self._midiInstrumentObj.midiProgram = self._currentTag.charData




        # formerly part of handler part
        elif name == 'part':
            self._parts.append(self._partObj) # outermost container
            self._partObj = None # clear to avoid mistakes



        elif name == 'key':
            self._attributesObj.keyList.append(self._keyObj)
            self._keyObj = None

        elif name == 'fifths':
            self._keyObj.fifths = self._currentTag.charData

        elif name == 'mode':
            self._keyObj.mode = self._currentTag.charData

        elif name == 'cancel':
            self._keyObj.cancel = self._currentTag.charData

        elif name == 'key-step':
            self._keyStepObj.charData = self._currentTag.charData
            self._keyObj.nonTraditionalKeyList.append(self._keyStepObj)
            self._keyStepObj = None

        elif name == 'key-alter':
            self._keyAlterObj.charData = self._currentTag.charData
            self._keyObj.nonTraditionalKeyList.append(self._keyAlterObj)
            self._keyAlterObj = None

        elif name == 'key-octave':
            self._keyOctaveObj.charData = self._currentTag.charData
            self._keyObj.nonTraditionalKeyList.append(self._keyOctaveObj)
            self._keyOctaveObj = None

        elif name == 'transpose':
            self._attributesObj.transposeObj = self._transposeObj
            self._transposeObj = None

        elif name == 'diatonic':
            self._transposeObj.diatonic = self._currentTag.charData

        elif name == 'chromatic':
            self._transposeObj.chromatic = self._currentTag.charData

        elif name == 'octave-change':
            self._transposeObj.octaveChange = self._currentTag.charData

        elif name == 'double': 
            self._transposeObj.double = True

        elif name == 'time':
            self._attributesObj.timeList.append(self._timeObj)
            self._timeObjLast = copy.deepcopy(self._timeObj)
            self._timeObj = None

        elif name == 'staves':
            self._attributesObj.staves = self._currentTag.charData

        elif name == 'beats':
            self._timeObj.componentList.append(
                Beats(self._currentTag.charData))
            #self._timeObj.beats = self._currentTag.charData

        elif name == 'beat-type':
            self._timeObj.componentList.append(
                BeatType(self._currentTag.charData))
            #self._timeObj.beatType = self._currentTag.charData

        elif name == 'clef':
            self._attributesObj.clefList.append(self._clefObj)
            self._clefObj = None

        elif name == 'multiple-rest':
            self._measureStyleObj.multipleRest = self._currentTag.charData

        elif name == 'measure-style':
            self._attributesObj.measureStyleObj = self._measureStyleObj
            self._measureStyleObj = None

        elif name == 'sign':
            self._clefObj.sign = self._currentTag.charData

        elif name == 'line':
            self._clefObj.line = self._currentTag.charData

        elif name == 'clef-octave-change':
            self._clefObj.clefOctaveChange = self._currentTag.charData
            #environLocal.printDebug(['got coc tag', self._clefObj])



        elif name == 'display-step':
            # chara data loaded in object
            self._restObj.componentList.append(self._displayStepObj)
            self._displayStepObj = None

        elif name == 'display-octave':
            self._restObj.componentList.append(self._displayOctaveObj)
            self._displayOctaveObj = None





        elif name == 'staff': 
            if self._noteObj != None: # not a forward/backup tag
                self._noteObj.staff = self._currentTag.charData
            else:
                pass
                #environLocal.printDebug([' cannot deal with this staff', self._currentTag.charData])


        elif name == 'barline': 
            self._measureObj.componentList.append(self._barlineObj)
            self._barlineObj = None

        elif name == 'ending':
            self._barlineObj.endingObj = self._endingObj
            self._endingObj = None

        elif name == 'bar-style': 
            self._barlineObj.barStyle = self._currentTag.charData

        elif name == 'repeat': 
            self._barlineObj.repeatObj = self._repeatObj
            self._repeatObj = None

        # clear and end
        if name in self.t.tagsAll:
            self.t[name].clear() 
            self.t[name].end() 



    #---------------------------------------------------------------------------
    def getContent(self):
        self._scoreObj.partListObj = self._partListObj
        self._scoreObj.componentList = self._parts
        return self._scoreObj



#-------------------------------------------------------------------------------
class Document(object):
    '''Represent a MusicXML document, 
    importing and writing'''

    def __init__(self):
        # create one tagLib for efficiency
        self.tagLib = TagLib()
        self.score = None

    def _getParser(self):
        '''Setup and return a saxparser with default configuration.'''
        saxparser = xml.sax.make_parser()
        # need ot turn off dtd resolver, as tries to do this online if a url is given
        saxparser.setFeature(xml.sax.handler.feature_external_ges, 0)
        saxparser.setFeature(xml.sax.handler.feature_external_pes, 0)
        # not sure if namespaces are needed
        saxparser.setFeature(xml.sax.handler.feature_namespaces, 0)   
        return saxparser

    def _load(self, fileLike, file=True, audit=False):
        saxparser = self._getParser()

        t = common.Timer()
        t.start()

        # call the handler with tagLib
        h = Handler(self.tagLib) 
        saxparser.setContentHandler(h)

        if not file:
            fileLikeOpen = StringIO.StringIO(fileLike)
        else:
            fileLikeOpen = open(fileLike)

        # the file always needs to be closed, otherwise
        # subsequent parsing operations produce an unclosed token error
        try:
            saxparser.parse(fileLikeOpen)
        except:
            fileLikeOpen.close()
        fileLikeOpen.close()

        t.stop()
        environLocal.printDebug(['parsing time:', t])

        if audit:
            ok, msg = self.tagLib.audit() # audit tags
            if not ok:
                raise DocumentException(msg)
            else:
                environLocal.printDebug(msg)

        self.score = h.getContent()

        if audit:
            self.tagLib.statRun()
            self.tagLib.statClear()


    def read(self, xmlString, audit=False):
        '''load musicxml form a string, instead of a file
        '''
        self._load(xmlString, False, audit)

    def open(self, fp, audit=False):
        self._load(fp, True, audit)

    #---------------------------------------------------------------------------        
    # convenience routines to get meta-data
    def getBestTitle(self):
        '''title may be stored in more than one place'''
        if self.score.movementTitle != None:
            title = self.score.movementTitle
        elif self.score.workObj != None:
            title = self.score.workObj.workTitle
        else:
            title = None
        return title

    #---------------------------------------------------------------------------        
    def repr(self):
        self.reprTest()

    def reprTest(self):
        '''Basic display for testing'''

        print('+'*20 + ' ' + self.getBestTitle())
        print(self.score)
        print()
        print(self.score.toxml(None, None, 1))

    def reprPolyphony(self):
        # create an event list by measure
        for part in self.score.componentList:
            print('+'*20 + ' ' + 'part-id', part.get('id'))
            for measure in part.componentList:
                print(' '*10 + '+'*10 + ' ' + 'measure-no', measure.get('number'))
                for note in measure.componentList:
                    # skip forward and backward objects
                    if note.tag != 'note': continue
                    startStr = str(note.external['start']).ljust(5)
                    print(' '*20 + ' ' + 'note', startStr, note)

    #---------------------------------------------------------------------------
    def write(self, fp):
        msg = self.score.toxml(None, None, 1)
        f = open(fp, 'w')
        f.write(msg)
        f.close()

    def writePickle(self, fp):
        f = open(fp, 'wb') # binary
        # a negative protocal value will get the highest protocal; 
        # this is generally desirable 
        pickleMod.dump(self.score, f, protocol=-1)
        f.close()


    def openPickle(self, fp):
        f = open(fp, 'rb')
        self.score = pickleMod.load(f)
        f.close()






#-------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):
    '''Tests that require acces to external files
    '''
    def runTest(self):
        pass

    def testOpen(self, fp=None):    
        from music21 import corpus
        if fp == None: # get shuman
            fp = corpus.getWork('opus41no1', 2)
        c = Document()
        c.open(fp, audit=True)
        c.repr()

    def testCompareFile(self, fpIn=None, fpOut=None):
        '''input a file and write it back out as xml'''
        from music21 import corpus
        if fpIn == None: # get shuman
            fpIn = corpus.getWork('opus41no1', 2)

        if fpOut == None:
            fpOut = environLocal.getTempFile('.xml')

        c = Document()
        c.open(fpIn, audit=True)
        c.write(fpOut)
        environLocal.printDebug([_MOD, 'wrote:', fpOut])


#     def testInputDirectory(self, dirPath=None):
#         if dirPath == None:
#             from music21 import corpus
#             fpList = corpus.mozart
#         else:
#             fpList = []
#             for fn in os.listdir(dirPath):
#                 fpList.append(os.path.join(dirPath, fName))
# 
#         for fp in fpList:
#             if fp.endswith('.xml'):
#                 print '='*20, fp
#                 self.testOpen(fp)


#     def testCompareDirectory(self, dirPath):
#         c = Document()
#         audit = 1
#         for fName in os.listdir(dirPath):
#             if fName.endswith('.xml'):
#                 if fName.endswith('-music21.xml'):
#                     continue
#                 fp = os.path.join(dirPath, fName)
#                 print '='*20, fp
#                 self.testCompareFile(fp)

    def testPolyphonyFile(self, fp=None):

        from music21 import corpus
        if fp == None: # get shuman
            fp = corpus.getWork('opus41no1', 2)

        c = Document()
        c.open(fp, audit=True)
        c.reprPolyphony()

# need new path
#    def testMarkings(self):
#        # note: this import path will likely change
#        from music21.musicxml import testFiles
#        from music21.m21xml import lvbOp59No2Mvmt1
#
#        for score in lvbOp59No2Mvmt1.ALL:
#            a = Document()
#            a.read(score)
#            for part in a.score:
#                for measure in part:
#                    for entry in measure:
#                        if isinstance(entry, Direction):
#                            print entry



#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    '''Unit tests
    '''

    def runTest(self):
        pass


    def setUp(self):
        pass


    def testCopyAndDeepcopy(self):
        '''Test copyinng all objects defined in this module
        '''
        import sys, types, copy
        for part in sys.modules[self.__module__].__dict__.keys():
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            name = getattr(sys.modules[self.__module__], part)
            if callable(name) and not isinstance(name, types.FunctionType):
                try: # see if obj can be made w/ args
                    obj = name()
                except TypeError:
                    continue
                a = copy.copy(obj)
                b = copy.deepcopy(obj)

    def testTagLib(self):
        t = TagLib()
        # create some conditions that would trigger an error
        t['sign'].charData = 'G'
        t['pitch'].start()
        ok, msg = t.audit()
        # should be an error
        self.assertEqual(ok, 0)


    def _compareParsed(self, a, b):
        '''Recursuve domtree testing method.
        '''
        if a.tagName != b.tagName:
            return False
        if sorted(a.attributes.items()) != sorted(b.attributes.items()):
            return False
        if len(a.childNodes) != len(b.childNodes):
            return False
        for ac, bc in zip(a.childNodes, b.childNodes):
            if ac.nodeType != bc.nodeType:
                return False
            if ac.nodeType == ac.TEXT_NODE and ac.data != bc.data:
                return False
            if (ac.nodeType == ac.ELEMENT_NODE and 
                not self._compareParsed(ac, bc)):
                return False
        return True

    def _compareXml(self, a, aExpected):
        aParsed = xml.dom.minidom.parseString(a.xmlStr())
        aExpected = xml.dom.minidom.parseString(aExpected)
        self.assert_(self._compareParsed(aParsed.documentElement, 
                aExpected.documentElement))



    def testPrimitiveXMLOut(self):
        beats = Beats(3)
        beatType = BeatType(8)

        a = Time()
        a.componentList.append(beats)
        a.componentList.append(beatType)

        #a.set('beats', 3)
        #a.set('beatType', 8)
        #print a.toxml(None, None, 1)
        aExpected = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE score-partwise
  PUBLIC '-//Recordare//DTD MusicXML 2.0 Partwise//EN'
  'http://www.musicxml.org/dtds/partwise.dtd'>
<time>
  <beats>3</beats>
  <beat-type>8</beat-type>
</time>'''

        self._compareXml(a, aExpected)

        a1 = Clef()
        a1.set('sign', 'C')
        a1.set('line', 3)
        #print a1.toxml(None, None, 1)
        a1Expected = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE score-partwise
  PUBLIC '-//Recordare//DTD MusicXML 2.0 Partwise//EN'
  'http://www.musicxml.org/dtds/partwise.dtd'>
<clef>
  <sign>C</sign>
  <line>3</line>
</clef>'''
        self._compareXml(a1, a1Expected)


        a2 = Key()
        a2.set('cancel', None)
        a2.set('fifths', 3)
        a2.set('mode', 'major')
        #print a2.toxml(None, None, 1)
        a2Expected = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE score-partwise
  PUBLIC '-//Recordare//DTD MusicXML 2.0 Partwise//EN'
  'http://www.musicxml.org/dtds/partwise.dtd'>
<key>
  <fifths>3</fifths>
  <mode>major</mode>
</key>'''
        self._compareXml(a2, a2Expected)



        for step, alter in [(0,-2),(4,2),(1,-1)]:
            b = KeyStep() # non traditional key
            b.set('charData', step)
            a2.nonTraditionalKeyList.append(b)

            c = KeyAlter() # non traditional key
            c.set('charData', alter)
            a2.nonTraditionalKeyList.append(c)

        for number, octave in [(1,2),(2,3),(3,4)]:
            d = KeyOctave() # non traditional key
            d.set('number', number)
            d.set('charData', octave)
            a2.nonTraditionalKeyList.append(d)

        a2Expected = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE score-partwise
  PUBLIC '-//Recordare//DTD MusicXML 2.0 Partwise//EN'
  'http://www.musicxml.org/dtds/partwise.dtd'>
<key>
  <fifths>3</fifths>
  <mode>major</mode>
  <key-step>0</key-step>
  <key-alter>-2</key-alter>
  <key-step>4</key-step>
  <key-alter>2</key-alter>
  <key-step>1</key-step>
  <key-alter>-1</key-alter>
  <key-octave number="1">2</key-octave>
  <key-octave number="2">3</key-octave>
  <key-octave number="3">4</key-octave>
</key>
'''
        #print a2.toxml(None, None, 1)
        self._compareXml(a2, a2Expected)

        d = Direction()
        d.set('placement', 'below')
        dExpected = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE score-partwise
  PUBLIC '-//Recordare//DTD MusicXML 2.0 Partwise//EN'
  'http://www.musicxml.org/dtds/partwise.dtd'>
<direction placement="below"/>'''
        self._compareXml(d, dExpected)

        f = Ending()
        f.set('type', 'stop')
        f.set('number', 1)
        fExpected= '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE score-partwise
  PUBLIC '-//Recordare//DTD MusicXML 2.0 Partwise//EN'
  'http://www.musicxml.org/dtds/partwise.dtd'>
<ending number="1" type="stop"/>'''
        self._compareXml(f, fExpected)

        g = Repeat()
        g.set('direction', 'forward')
        gExpected = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE score-partwise
  PUBLIC '-//Recordare//DTD MusicXML 2.0 Partwise//EN'
  'http://www.musicxml.org/dtds/partwise.dtd'>
<repeat direction="forward"/>'''
        self._compareXml(g, gExpected)

 
        e = Barline()
        e.set('location', 'right')
        e.set('barStyle', "light-heavy")
        e.set('endingObj', f)
        e.set('repeatObj', g)
        #print e.toxml(None, None, 1)
        eExpected = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE score-partwise
  PUBLIC '-//Recordare//DTD MusicXML 2.0 Partwise//EN'
  'http://www.musicxml.org/dtds/partwise.dtd'>
<barline location="right">
  <bar-style>light-heavy</bar-style>
  <ending number="1" type="stop"/>
  <repeat direction="forward"/>
</barline>'''
        self._compareXml(e, eExpected)


        h = Pitch()
        h.set('step', 'C')
        h.set('alter', 1)
        h.set('octave',4)
        hExpected = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE score-partwise
  PUBLIC '-//Recordare//DTD MusicXML 2.0 Partwise//EN'
  'http://www.musicxml.org/dtds/partwise.dtd'>
<pitch>
  <step>C</step>
  <alter>1</alter>
  <octave>4</octave>
</pitch>'''
        self._compareXml(h, hExpected)



#         i = Lyric()
#         i.set('number', 3)
#         i.set('syllabic', 'single')
#         i.set('text', 'Mai,')
#         print i.toxml(None, None, 1)
# 
#         j = Beam()
#         j.set('number', 1)
#         j.charData = 'backward hook'
#         print j.toxml(None, None, 1)
# 
#         j2 = Beam()
#         j2.set('number', 2)
#         j2.charData = 'begin'
#         print j2.toxml(None, None, 1)
# 
# #these need to be updated with set method
# 
#         k = Slur()
#         k.number = 1
#         k.placement = 'below'
#         k.type = 'start'
#         print k.toxml(None, None, 1)
# 
#         l = Tie()
#         l.type = 'stop'
#         print l.toxml(None, None, 1)
# 
#         l2 = Tie()
#         l2.type = 'start'
#         print l2.toxml(None, None, 1)
# 
#         n = Notations()
#         n.componentList.append(k)
#         print n.toxml(None, None, 1)
# 
#         o = Tied()
#         o.type = 'start'
#         n.componentList.append(o)
#         print n.toxml(None, None, 1)
# 
#         s = Notehead()
#         s.filled = 'no'
#         s.parentheses = 'yes'
#         s.charData = 'triangle'
#         print s.toxml(None, None, 1)
# 
#         t = TimeModification()
#         t.actualNotes = 3
#         t.normalNotes = 2
#         t.normalType = 'quarter'
#         print t.toxml(None, None, 1)
# 
#         m = Note()
#         m.chord = True
#         m.rest = False
#         m.duration = 2
#         m.voice = 1
#         m.type = '16th'
#         m.stem = 'down'
#         m.staff = 1
#         m.noteheadObj = s
#         m.accidental = 'sharp'
#         m.beamList.append(j)
#         m.beamList.append(j2)
#         m.pitchObj = h
#         m.tieList.append(l)
#         m.tieList.append(l2)
#         m.notationsObj = n
#         m.timeModificationObj = t
#         m.lyricObj = i
#         print m
#         print m.toxml(None, None, 1)
# 
#         q = Transpose()
#         q.diatonic = -1
#         q.chromatic = -2
#         q.octaveChange = -1
#         print q.toxml(None, None, 1)
# 
#         p = Attributes()
#         p.divisions = 8
#         p.keyList.append(a2)
#         p.timeList.append(a)
#         p.clefList.append(a1)
#         p.transposeObj = q
#         print p.toxml(None, None, 1)
# 
#         r = Measure(1) # number is init arg
#         r.attributesObj = p
#         r.componentList.append(m)
#         r.componentList.append(e)
#         print r.toxml(None, None, 1)
# 
#         s = Part()
#         s.id = 'P1'
#         s.componentList.append(r)
#         print s
#         print s.toxml(None, None, 1)
# 
#         aa = Work()
#         aa.workNumber = 'Op. 48'
#         aa.workTitle = 'Dicterliebe'
#         print aa.toxml(None, None, 1)
# 
#         cc = Creator()
#         cc.type = 'composer'
#         cc.charData = 'Robert Schumann'
#         print cc.toxml(None, None, 1)
# 
#         cc1 = Creator()
#         cc1.type = 'lyricist'
#         cc1.charData = 'Heinrich Heine'
#         print cc1.toxml(None, None, 1)
# 
#         ee = Software()
#         ee.charData = 'Finle 2005 for Wdows'
# 
#         ff = Software()
#         ff.charData = 'Olet 4.0 Beta 4 for Finle'
# 
#         gg = Encoding()
#         gg.softwareList = [ee, ff]
#         gg.encodingDate = '2007-06-19'
#         print gg.toxml(None, None, 1)
# 
#         bb = Identification()
#         bb.rights = 'Copyright 2009'
#         bb.creatorList = [cc, cc1]
#         bb.encodingObj = gg
#         print bb.toxml(None, None, 1)
# 
#         dd = Score('2.0')
#         dd.movementTitle = 'Sonata'
#         dd.movementNumber = '234'
#         dd.workObj = aa
#         dd.identificationObj = bb
#         print dd
#         print dd.toxml(None, None, 1)
# 
#         hh = MIDIInstrument("P1-I18")
#         hh.midiChannel = 1
#         hh.midiProgram = 73
#         hh.elevation = 90
#         hh.pan = -180
#         print hh.toxml(None, None, 1)
# 
#         ii = ScoreInstrument("P1-I18")
#         ii.instrumentName = "Piccolo"
#         ii.instrumentAbbreviation = "Picc."
#         ii.solo = True
#         print ii.toxml(None, None, 1)
# 
#         jj = ScorePart()
#         jj.partName = 'Piccolo'
#         jj.partAbbreviation = 'Picc.'
#         jj.scoreInstrumentList = [ii]
#         jj.midiInstrumentList = [hh]
#         
#         kk = PartGroup()
#         kk.groupName = 'green'
#         kk.groupSymbol = 'bracket'
#         kk.groupBarline = 'yes'
#         print kk
#         print kk.toxml(None, None, 1)

#         ll = Fermata()
#         ll.type = 'inverted'
#         print ll
#         print ll.toxml(None, None, 1)





    def testSetMethod(self):
        '''test setting attributes via xml entity names'''
        a = Pitch()
        a.set('step', 'G')
        a.set('alter', 1)
        a.set('octave', 4)
        # print a.xmlStr()

        aExpected = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE score-partwise
  PUBLIC '-//Recordare//DTD MusicXML 2.0 Partwise//EN'
  'http://www.musicxml.org/dtds/partwise.dtd'>
<pitch>
  <step>G</step>
  <alter>1</alter>
  <octave>4</octave>
</pitch>    
"""
        self._compareXml(a, aExpected)

        b = Creator()
        b.set('type', 'composer')
        b.set('charData', 'Xenakis')
        # print b.xmlStr()

        bExpected = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE score-partwise
  PUBLIC '-//Recordare//DTD MusicXML 2.0 Partwise//EN'
  'http://www.musicxml.org/dtds/partwise.dtd'>
<creator type="composer">Xenakis</creator>
"""
        self._compareXml(b, bExpected)


        c = MIDIInstrument()
        c.set('midi-channel', 8)
        c.set('midi-name', 'Flute')
        c.set('midi-program', 120)
        #print c.xmlStr()

        cExpected = """<!DOCTYPE score-partwise
  PUBLIC '-//Recordare//DTD MusicXML 2.0 Partwise//EN'
  'http://www.musicxml.org/dtds/partwise.dtd'>
<midi-instrument>
  <midi-channel>8</midi-channel>
  <midi-name>Flute</midi-name>
  <midi-program>120</midi-program>
</midi-instrument>
"""
        self._compareXml(c, cExpected)

        beats = Beats(3)
        beatType = BeatType(8)

        d = Time()
        d.set('symbol', 'common')
        d.componentList.append(beats)
        d.componentList.append(beatType)
        #print d.xmlStr()

        dExpected = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE score-partwise
  PUBLIC '-//Recordare//DTD MusicXML 2.0 Partwise//EN'
  'http://www.musicxml.org/dtds/partwise.dtd'>
<time symbol="common">
  <beats>3</beats>
  <beat-type>8</beat-type>
</time>
"""
        self._compareXml(d, dExpected)



    def testDefaults(self):
        for className in [Score, Work, Identification, Creator, Encoding, Software, PartList, PartGroup, ScorePart, ScoreInstrument, MIDIInstrument, Part, Measure, Attributes, Key, KeyStep, KeyAlter, KeyOctave, Transpose, Time, Clef, Direction, DirectionType, MeasureStyle, Barline, Ending, Repeat, Note, Forward, Backup, Notations, Dynamics, Articulations, Technical, Grace, Notehead, Dot, Tie, Fermata, Accidental, Slur, Tied, Beam, Lyric, Pitch, TimeModification, Tuplet]:

        # need args
        # DynamicMark, ArticulationMark, TechnicalMark
            a = className()
            a.setDefaults()


    def testTestFiles(self):
        # note: this import path will likel change
        from music21.musicxml import testFiles
        for score in testFiles.ALL[:1]:
            a = Document()
            a.read(score)


    def testTestPrimitive(self):
        # note: this import path will likel change
        from music21.musicxml import testPrimitive
        
        a = Document()
        for xmlString in testPrimitive.ALL:
            a.read(xmlString)

    def testOpenCorpus(self):
        from music21 import corpus
        path = corpus.getWork('luca')
        d = Document()
        d.open(path)

        mxMeasure = d.score.componentList[1][0] # second part, first measure
        mxAttributes = mxMeasure.get('attributes')
        mxClef = mxAttributes.get('clefList')[0]
        self.assertEqual(mxClef.get('sign'), 'G')
        # values is stored as a string
        self.assertEqual(mxClef.get('clef-octave-change'), '-1')

#-------------------------------------------------------------------------------
if __name__ == "__main__":
    # this is a temporary hack to get encoding working right
    # this may not be the best way to do this
    reload(sys)
    sys.setdefaultencoding("utf-8")


    if len(sys.argv) != 2:
        music21.mainTest(Test)


    elif len(sys.argv) == 2:
        t = TestExternal()
        if os.path.isdir(sys.argv[1]): 
            t.testInputDirectory(sys.argv[1])
        else: # assume it is a single file
            t.testOpen(sys.argv[1])




