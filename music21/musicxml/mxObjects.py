# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         musicxml/mxObjects.py
# Purpose:      MusicXML objects for conversion to and from music21
#
# Authors:      Christopher Ariza
#
# Copyright:    Copyright © 2009-2014 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
This module defines an object representation of MusicXML, used for converting to and from 
MusicXML and music21.
'''
import sys


import copy
import unittest
#import io

from music21 import defaults
from music21 import common
from music21 import exceptions21
from music21 import xmlnode

from music21.ext import six

from music21 import environment
_MOD = 'musicxml.py'
environLocal = environment.Environment(_MOD)

 
# new objects to add: octave-shift, in direction-type
# bracket, in direction-type
# Notations -> ornaments, trill-mark/wavy-line
# notations -> glissando
# dashes, in direction-type

#-------------------------------------------------------------------------------
# notes

# problem with element tree:
# http://effbot.org/zone/element.htm
# Note that the standard element writer creates a compact output. 
# There is no built-in support for pretty printing or user-defined 
# namespace prefixes in the current version, so the output may not 
# always be suitable for human consumption (to the extent XML is 
# suitable for human consumption, that is).

# unicode and python issues
# http://evanjones.ca/python-utf8.html

# TODO: deal with grace notes, in particular duration handling
# TODO: add print <print new-system="yes"/>

# tests matching
# 01a, 01b, 01c, 01d
# 02a, 02c, 02d, 02e

# tests that do not match
# 02b-Rest-PitchedRest.xml
#   rests currently do not store display settings



#-------------------------------------------------------------------------------
# these single-entity tags are bundled together. 
# order here may matter in performance

DYNAMIC_MARKS = ['p', 'pp', 'ppp', 'pppp', 'ppppp', 'pppppp',
        'f', 'ff', 'fff', 'ffff', 'fffff', 'ffffff',
        'mp', 'mf', 'sf', 'sfp', 'sfpp', 'fp', 'rf', 'rfz', 'sfz', 'sffz', 'fz']

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
    if value in ('yes', True):
        return True
    return False

def booleanToYesNo(value):
    if value:
        return 'yes'
    return 'no'

#-------------------------------------------------------------------------------
class TagException(exceptions21.Music21Exception):
    pass

class TagLibException(exceptions21.Music21Exception):
    pass

class MusicXMLException(exceptions21.Music21Exception):
    pass

class DocumentException(exceptions21.Music21Exception):
    pass

#-------------------------------------------------------------------------------
class Tag(common.SlottedObject):
    '''Object to store tags as encountered by SAX. Tags can be open or closed based on the 
    status attribute. Tags can store character data collected between their defined tags. 

    These objects are used only for finding and collecting tag attributes and elements. 
    As we do not need character data for all tags, tags have an optional flag to select 
    if the are to collect character data.
    '''
    __slots__ = ('tag', 'cdFlag', 'status', 'charData', 'className', 'count')
    
    def __init__(self, tag, cdFlag=False, className=None):
        '''        
        >>> t = musicxml.mxObjects.Tag('note')
        >>> t.start()
        >>> t.start() # catch double starts
        Traceback (most recent call last):
        TagException: Tag (note) is already started.

        Calling the tag returns the charData

        >>> t.cdFlag = True # can handle charData
        >>> t.charData = 'Hello'
        >>> t()
        'Hello'
        '''
        self.tag = tag
        self.cdFlag = cdFlag # character data flag
        self.status = False
        self.charData = u''
        self.className = className

        self.count = 0 # Used for statistics/debugging -- audit; not otherwise used

    def start(self):
        if self.status: # already open
            raise TagException('Tag (%s) is already started.' % self.tag)
        self.status = True

    def end(self):
        if not self.status:
            raise TagException('Tag (%s) is already ended.' % self.tag)
        self.status = False
        # when not doing audit checks, no need to count
        #self.count += 1 # increment on close

    def clear(self):
        self.charData = u''

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
    An object to store all MusicXML tags as :class:`~music21.musicxml.base.Tag` objects. 
    Tag objects are used just to identify tags, store element contents and status in SAX parsing. 

    With this design some tags (called simple elements) can be used simply in 
    SAX parsing as structural monitors, but not be instantiated as objects for content 
    delivery.
    '''
    def __init__(self):
        '''
        
        >>> tl = musicxml.mxObjects.TagLib()
        >>> tl['voice'].tag
        'voice'
        >>> tl['voice'].status # open or closed
        False
        >>> tl.audit()
        (True, 'TagLib audit: no errors found.')
        >>> tl['note'].start()
        >>> tl.audit()
        (False, 'TagLib audit: 1 errors found:\\ntag <note> left open')
        '''
        self._t = {}

        # store tag, charDataBool, className
        # charDataBool is if this tag stores char data
        # order here is based on most-often used, found through empirical tests
        # all tags under collection must be defined here, even if they do not   
        # have an object but are defined only as simple entities
        _tags = [
        ('voice', True), 
        ('note', False, Note), 
        ('duration', True), # no object, just a tag
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
        ('mordent', False, Mordent), 
        ('inverted-mordent', False, InvertedMordent), 
        
        ('turn', False, Turn), 
        ('delayed-turn', False, DelayedTurn), 
        ('inverted-turn', False, InvertedTurn), 
        ('accidental-mark', True, AccidentalMark), 
        ('shake', False, Shake), 
        ('schleifer', False, Schleifer), 
        ('tremolo', True, Tremolo), 
        
        ('attributes', False, Attributes), 
        
        ('divisions', True), 
        ('staff-details', False, StaffDetails),
        ('staff-lines', True),
        ('staff-size', True),
        
        ('forward', False, Forward), 
        ('backup', False, Backup), 
        ('grace', False, Grace),  
        
        # this position is not based on measured tag usage
        ('sound', False, Sound),  
        ('words', True, Words),  
        ('offset', True),  # no object
                
        ('defaults', False, Defaults),
        ('scaling', False, Scaling),
        ('millimeters', True),
        ('tenths', True),
        ('print', False, Print),  
        ('page-layout', False, PageLayout),  
        ('page-margins', False, PageMargins),  
        ('page-height', True),  
        ('page-width', True),  
        ('system-layout', False, SystemLayout),  
        ('system-margins', False, SystemMargins),  
        ('right-margin', True),  
        ('left-margin', True),
        ('top-margin', True),
        ('bottom-margin', True),
        ('system-distance', True),  
        ('top-system-distance', True),
        ('staff-layout', False, StaffLayout),
        ('staff-distance', True),
        
        
        ('metronome', False, Metronome), # no char data
        ('beat-unit', True, BeatUnit),
        ('beat-unit-dot', False, BeatUnitDot),
        ('per-minute', True, PerMinute),
        
        ('time-modification', False, TimeModification), 
        ('actual-notes', True), 
        ('normal-notes', True), 
        ('normal-type', True), 
        ('normal-dot', True), 
        ('tuplet', False, Tuplet), 
        ('notehead', True, Notehead), 
        ('technical', False, Technical), 
        
        ('wedge', False, Wedge), 
        ('octave-shift', False, OctaveShift), 
        ('bracket', False, Bracket), 
        ('wavy-line', False, WavyLine), 
        ('glissando', True, Glissando), 
        ('dashes', False, Dashes), 
        
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
        
        ('segno', False, Segno),  
        ('coda', False, Coda),  
        
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
        ('credit', False, Credit), 
        ('credit-words', True, CreditWords), 
        ('encoding', False, Encoding), 
        ('software', True, Software), 
        ('supports', False, Supports),
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
        
        ('harmony', False, Harmony), 
        ('inversion', True), 
        ('function', True), 
        ('root', False, Root), 
        ('root-step', True), 
        ('root-alter', True), 
        ('kind', True, Kind), 
        ('bass', False, Bass), 
        ('bass-step', True), 
        ('bass-alter', True), 
        ('degree', False, Degree), 
        ('degree-value', True, DegreeValue), 
        ('degree-alter', True, DegreeAlter), 
        ('degree-type', True, DegreeType), 
         
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
        self.tagsCharData = [] # note: this may no longer be needed
        self.tagsAll = [] 

        for data in _tags:
            # some cases have a string w/o a class definition
            if isinstance(data, str):
            # if common.isStr(data): 
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
            else: # not all tags define a class name
                className = None

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

    def getClassName(self, key):
        '''
        Get the class or name, or None if none defined.

        
        >>> tl = musicxml.mxObjects.TagLib()
        >>> tl.getClassName('voice')

        '''
        return self._t[key].className # may be None

    def keys(self):
        return self._t.keys()

    #---------------------------------------------------------------------------
    # utilities for error checking and debugging

    def _statTabulate(self):
        self._stat = {}
        tags = list(self._t.keys())
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
            self._t[tag].count = 0

    def _statMapActive(self):
        '''Display method for tag audit checks
        '''
        tags = list(self._t.keys())
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
            if self._t[key].status: # if true
                errors.append('tag <%s> left open' % key)
            if self._t[key].cdFlag:
                sample = self._t[key].charData
                if sample != '':
                    errors.append('tag <%s> left element data: %s' % (key, sample))
        if len(errors) != 0:
            ok = False
            return ok, header + ('%s errors found:\n' % len(errors)) + '\n'.join(errors)
        else:
            ok = True
            return ok, header + 'no errors found.' 




#-------------------------------------------------------------------------------
class MusicXMLElement(xmlnode.XMLNode):
    '''MusicXML elements are an abstraction of MusicXML 
    into an object oriented framework. Some, not all, of MusicXML 
    elements are represented as objects. Some sub-elements are much more 
    simply placed as attributes of parent objects. These simple elements 
    have only a tag and character data. Elements that have attributes 
    and/or sub-elements, however, must be represented as objects.
    '''

    def __init__(self):
        '''
        These tests are module specific and should be loaded as unittests, below        

        >>> a = musicxml.mxObjects.MusicXMLElement()
        >>> a._convertNameToXml('groupAbbreviation')
        'group-abbreviation'
        >>> a._convertNameToXml('midiUnpitched')
        'midi-unpitched'
        >>> a._convertNameToXml('groupNameDisplay')
        'group-name-display'
        >>> a._convertNameToXml('group-name-display')
        'group-name-display'

        >>> a = musicxml.mxObjects.MusicXMLElement()
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

        >>> a = musicxml.mxObjects.MusicXMLElement()
        >>> len(a._publicAttributes())
        3
        >>> print(a._publicAttributes())
        ['charData', 'external', 'tag']
        '''
        xmlnode.XMLNode.__init__(self)
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

    def insert(self, position, item):
        self.componentList.insert(position, item)

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

        
        >>> a = musicxml.mxObjects.MusicXMLElementList()
        >>> a.componentList.append(1)
        >>> b = musicxml.mxObjects.MusicXMLElementList()
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
                
        
        >>> a = musicxml.mxObjects.Score()
        >>> a.tag
        'score-partwise'
        >>> a.setDefaults()
        >>> b = musicxml.mxObjects.Identification()
        >>> b.setDefaults()
        >>> a.set('identification', b)
        >>> c = musicxml.mxObjects.Score()
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
        self.defaultsObj = None
        self.encodingObj = None 
        self.partListObj = None
        
        self.creditList = [] # store a list of credit objects
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
        c.append(self.defaultsObj)
        c = c + self.creditList
        c.append(self.partListObj)
        c = c + self.componentList
        return c

    def setDefaults(self):
        self.set('movementTitle', defaults.title)

    #---------------------------------------------------------------------------
    # utility methods unique to the score
    def getPartIds(self):
        '''
        A quick way to get all valid part ids in the componentList
        '''
        post = []        
        for part in self.componentList:
            post.append(part.get('id'))
        return post

    def getPartIdsFromPartListObj(self):
        '''
        A quick way to get all valid part ids in the partListObj
        for each one that is a ScorePart
        '''
        post = []        
        for part in self.partListObj:
            if isinstance(part, ScorePart):
                post.append(part.get('id'))
        return post

    def partIdToNameDict(self):
        '''
        A quick way to get a mapping of valid part ids to the part names
        from a :class:`~music21.musicxml.Score` (musicxml.Score)
        object in the `.partListObj` property.
        
        Returns a dictionary mapping part id to part-name for each  :class:`~music21.musicxml.ScorePart`
        in `.partListObj`.
        
        Note that dictionaries are not sorted, so the order of `.partListObj`
        still needs to be used.
        '''
        post = {} # return a dictionary
        for part in self.partListObj:
            if isinstance(part, ScorePart):
                post[part.get('id')] = part.get('part-name')
        return post

    def getPartGroupData(self):
        '''Get part groups organized by part id in dictionaries.

        Returns a list of dictionaries, 
        each dictionary containing number, a list of part ids, 
        and a mx PartGroup object.
        '''
        openParts = []
        closedParts = []
        # the parts list object contains both ScorePart and PartGroup objs
        for p in self.partListObj:
            if isinstance(p, PartGroup):
                n = p.get('number')
                partType = p.get('type')
                if partType == 'start':
                    coll = {}
                    coll['number'] = n
                    coll['scorePartIds'] = []
                    coll['partGroup'] = p
                    openParts.append(coll)
                elif partType  == 'stop':
                    for c in openParts:
                        if c['number'] == n:
                            openParts.remove(c)
                            closedParts.append(c)
                            break
            elif isinstance(p, ScorePart):
                for c in openParts: # add to all open collections
                    c['scorePartIds'].append(p.get('id'))
        return closedParts

    def getScorePart(self, partId):
        '''Get an instrument, as defined in a ScorePart object, from a Score. 

        
        >>> a = musicxml.mxObjects.Score()
        >>> a.setDefaults()
        >>> a.getScorePart('P3') == None
        True
        
        >>> from music21.musicxml import testPrimitive
        >>> from music21.musicxml import xmlHandler
        >>> b = xmlHandler.Document()
        >>> b.read(testPrimitive.pitches01a)
        >>> spIdList = sorted(list(b.score.partIdToNameDict().keys()))
        >>> b.score.getScorePart(spIdList[0])
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
        >>> from music21.musicxml import xmlHandler
        >>> b = xmlHandler.Document()
        >>> b.read(testPrimitive.ALL[0])
        >>> spIdList = sorted(list(b.score.partIdToNameDict().keys()))
        >>> c = b.score.getPart(spIdList[0])
        >>> c
        <part id=P1 <measure number=1 width=983 <print <system-layout...
        >>> isinstance(c, musicxml.mxObjects.Part)
        True
        >>> isinstance(c, stream.Part)
        False
        '''
        idFound = None
        partNames = self.partIdToNameDict()    
        if partId in partNames:
            idFound = partId
        else:
            for thisPartId in self.getPartIds():
                if thisPartId.lower() == partId.lower(): # assume always lower
                    idFound = thisPartId 
                    break
                # check for part name
                elif partId.lower() == partNames[thisPartId].lower(): 
                    idFound = thisPartId
                    break
        if idFound is None:
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
        
        >>> a = musicxml.mxObjects.Work()
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
        
        >>> a = musicxml.mxObjects.Identification()
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
        self._crossReference['encodingObj'] = ['encoding']


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
    # types: composer, lyricist, and arranger
    def __init__(self):
        '''
        
        >>> a = musicxml.mxObjects.Creator()
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

class Credit(MusicXMLElementList):
    '''The credit tag stores on or more credit-words tags, defining text positioned on a page. 
    '''
    #series of credit-words elements within a single credit element
    def __init__(self):
        '''
        
        >>> a = musicxml.mxObjects.Credit()
        >>> a.tag
        'credit'
        >>> a.setDefaults()
        >>> b = musicxml.mxObjects.CreditWords('testing')
        >>> a.append(b)
        >>> print(a)
        <credit page=1 <credit-words charData=testing>>
        '''
        MusicXMLElementList.__init__(self)
        self._tag = 'credit'
        # attributes
        self._attr['page'] = None
        # character data
        self.charData = None
        # elements
        self.componentList = [] # a list of partGroups and scoreParts
    
    def _getComponents(self):
        return self.componentList

    def setDefaults(self):
        self.set('page', 1)


class CreditWords(MusicXMLElement):
    def __init__(self, charData=None):
        '''
        
        >>> a = musicxml.mxObjects.CreditWords()
        >>> a.tag
        'credit-words'
        '''
        MusicXMLElement.__init__(self)
        self._tag = 'credit-words'
        # attributes
        self._attr['default-x'] = None
        self._attr['default-y'] = None
        self._attr['font-size'] = None
        self._attr['font-weight'] = None
        self._attr['justify'] = None
        self._attr['font-style'] = None
        self._attr['valign'] = None
        self._attr['halign'] = None
        # character data
        self.charData = charData # main content
    
    def setDefaults(self):
#         self.set('default-x', 500)
#         self.set('default-y', 500)
        self.set('font-size', 12)
#         self.set('justify', 'center')
#         self.set('halign', 'center')
#         self.set('valign', 'top')

class Encoding(MusicXMLElement):
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'encoding'
        # simple elements
        self.encodingDate = None
        # sub objects
        self.softwareList = [] # list of objects
        self.supportsList = []
    
    def _getComponents(self):
        c = []
        c = c + self.softwareList 
        c.append(('encoding-date', self.encodingDate))
        # encoder
        # encoding-description
        # supports
        c = c + self.supportsList
        return c


class Software(MusicXMLElement):
    '''
    Defines the Software that created this 
    MusicXML document.
    '''
    
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'software'
        self.charData = None # only content

    def setDefaults(self):
        self.set('charData', defaults.software)


class Supports(MusicXMLElement):
    '''
    Defines what sorts of notation this encoding
    supports
    '''
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'supports'
        self.charData = None # only content
        self._attr['attribute'] = None
        self._attr['element'] = None
        self._attr['type'] = None
        self._attr['value'] = None


#----------------------------------------
class PartList(MusicXMLElementList):
    '''
    The PartList defines the parts, as well as their names and abbreviations.
    
    It stores the parts in its `.componentList` list in order.
     
    Additionally, the order of this list is used as a way 
    specifying arrangements of brackets and/or braces that 
    group parts in partGroup objects. 
    
    The order of this list thus matters. 
    
    The PartList for a score is usually accessed from the 
    :class:`~music21.musicxml.Score` (`musicxml.Score`) object's
    `.partListObj` parameter.
    '''
    def __init__(self):
        MusicXMLElementList.__init__(self)
        self._tag = 'part-list'
        # list of objects
        self.componentList = [] # a list of partGroups and scoreParts

    def _getComponents(self):
        return self.componentList



class PartGroup(MusicXMLElement):
    '''The PartGroup tag is stored in the PartList, intermingled with ScorePart tags and other definitions.
    '''
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'part-group'
        # attributes
        self._attr['type'] = None # start or stop; one of each
        self._attr['number'] = None # id number used to link start/stop
        # simple elements
        self.groupName = None
        self.groupNameDisplay = None
        self.groupAbbreviation = None
        self.groupAbbreviationDisplay = None
        self.groupSymbol = None # bracket, line, brace
        self.groupBarline = None # yes, no
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
    '''Lives in a PartList
    '''
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'score-part'
        # attributes
        self._attr['id'] = None
        # simple elements
        self.partName = None
        self.partAbbreviation = None # used on subsequent lines
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
        # randomly generated in m21 object when needed
        #self.set('id', defaults.partId)


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
    '''
    This assumes a part-wise part
    '''
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
        pass
        # might need to do this a different way
        # randomly generated in m21 object when needed    
        #self.set('id', defaults.partId)

    def getStavesCount(self):
        '''
        Look ahead into the measure Attributes and return the highest number 
        of staves used in this part.
        '''
        maxStaves = 1
        for c in self.componentList:
            if c._tag == 'measure':
                if c.attributesObj is not None:
                    if c.attributesObj.staves is not None:
                        count = int(c.attributesObj.staves)
                        if count > maxStaves:
                            maxStaves = count
        return maxStaves


class Measure(MusicXMLElementList):
    def __init__(self):
        MusicXMLElementList.__init__(self)
        self._tag = 'measure'
        # not all measures store an attributes object
        # yet, a measure can refer to a divisons setting
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

        # in some cases we have multiple attribute objects in one measure
        # need to store and merge
        # store multiple attributes objects found in this Measure
        self._attributesObjList = []
        self._crossReference['attributesObj'] = ['attributes']

        # store unique voice index numbers
        self._voiceIndices = []

    def _getComponents(self):
        c = [] 
        c.append(self.attributesObj)
        #c += self.componentList
        for part in self.componentList:
            if isinstance(part, Print):
                # place print elements first, ahead of attributes
                c.insert(0, part)
            else:
                c.append(part)
        return c

    def setDefaults(self):
        self.set('number', 1)
        attributes = Attributes()
        attributes.setDefaults()
        self.set('attributes', attributes)
        self.external['divisions'] = attributes.get('divisions')

    def update(self):
        '''
        This method looks at all note, forward, and backup 
        objects and updates divisons and attributes 
        references.
        '''
        updateAttributes = False
        if len(self._attributesObjList) > 1:
            updateAttributes = True
            attrConsolidate = Attributes()
            # consolidate is necessary for some MusicXML files that define 
            # each attribute component in its own attribute container
            for attrObj in self._attributesObjList:
                #environLocal.printDebug(['found multiple Attributes', attrObj])
                attrConsolidate = attrConsolidate.merge(attrObj)
            #environLocal.printDebug(['Measure.updaate(); found multiple Attributes objects for a single measure', attrConsolidate])
            self.attributesObj = attrConsolidate
            self.external['attributes'] = self.attributesObj
            # must make sure that this is not None, as we may get an incomplete
            # attributes object here
            if self.attributesObj.divisions is not None:
                self.external['divisions'] = self.attributesObj.divisions
            # keep existing divisions

        #counter = 0
        #noteThis = None
        #noteNext = None
        for pos in range(len(self.componentList)):
            #environLocal.printDebug(['Measure.update()', counter])
            obj = self.componentList[pos]
            if obj.tag in ['note']:
                if obj.voice is not None:
                    if obj.voice not in self._voiceIndices:
                        self._voiceIndices.append(obj.voice)
                # may need to assign new, merged attributes obj to components
                if updateAttributes:
                    obj.external['attributes'] = self.attributesObj     
                    if self.attributesObj.divisions is not None:
                        obj.external['divisions'] = self.attributesObj.divisions     
        self._voiceIndices.sort()


    def getVoiceCount(self):
        '''Return the number of voices defined in this Measure; this must be called after update(). 
        '''
        return len(self._voiceIndices)

    def getVoiceIndices(self):
        '''Return a list of unique sorted voice ids. 
        '''
        return self._voiceIndices


class Attributes(MusicXMLElement):
    # store measure data; assuming that there is one per measure

    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'attributes'
        # simple elements
        self.divisions = None
        self.staves = None 
        # complex elements
        # there can be one key for each staff in a Part, and there can be
        # more than one staff per part
        self.keyList = [] 
        # more than one pair of beat and beat-type is used for composite signatures
        self.timeList = [] 
        self.clefList = []
        self.staffDetailsList = []
        self.transposeObj = None # needs to be an ojbect
        self.measureStyleObj = None # for slash notation, mult rests

        # not yet implemented
        #self.staffDetails = None # shows different stave styles
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
        c = c + self.staffDetailsList
        c.append(self.transposeObj)
        # directive
        c.append(self.measureStyleObj)
        return c

    def setDefaultDivisions(self):
        '''Utility to just set the divisions parameters
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

class StaffDetails(MusicXMLElement):
    # contains information about staff size, staff number, printing, etc.
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'staff-details'
        
        # attributes
        self._attr['number'] = None
        self._attr['print-object'] = 'yes'
        
        # elements     
        self.staffSize = None
        self.staffLines = 5
        
        self._crossReference['number'] = ['number']
        self._crossReference['print-object'] = ['print-object', 'printObject']

    def _getComponents(self):
        c = []
        c.append(('staff-size', self.staffSize))
        c.append(('staff-lines', self.staffLines))
        return c

    

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
        self._attr['number'] = None # number here refers to staff number
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
        self._attr['number'] = None # clef number refers to staff number
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
    object. Within the Direction object may be a number of objects, 
    including DirectionType, Sound.
    '''
    def __init__(self):
        MusicXMLElementList.__init__(self)
        self._tag = 'direction'
        # attributes
        # note that placement does not seem to make a difference for some types
        self._attr['placement'] = None
        # elements
        self.componentList = []
        self.staff = None # number, for parts w/ > 1 staff 
        # position of this direction can be configured with a number in
        # divisions. this is given within <direction> and after <direction-type>
        self.offset = None # number, in divisions.


    def _getComponents(self):
        # need to look for sound tags stored on componentList and place
        # them at the very end of all components, after offset
        c = []
        c.append(('staff', self.staff))

        soundTag = None
        for i, sub in enumerate(self.componentList):
            if isinstance(sub, Sound):
                soundTag = sub
            else: # store others in order
                c.append(sub)
        #c = c + self.componentList

        # this position is conventional, not necessarily the most common
        c.append(('offset', self.offset)) 
        # if there is a sound tag, it needs to go after offset
        if soundTag is not None:
            c.append(soundTag)

        return c


    def getDynamicMark(self):
        '''Search this direction and determine if it contains a dynamic mark, return, otherwise, return None

        
        >>> a = musicxml.mxObjects.Direction()
        >>> b = musicxml.mxObjects.DirectionType()
        >>> c = musicxml.mxObjects.Dynamics()
        >>> d = musicxml.mxObjects.DynamicMark('f')
        >>> c.append(d)
        >>> b.append(c)
        >>> a.append(b)
        >>> a.getDynamicMark() is not None
        True
        '''
        for directionType in self.componentList:
            # <sound> tags are the only ones that are in direction
            # that are not wrapped in a direction-type attribute
            if isinstance(directionType, Sound):
                continue 
            for obj in directionType:
                if isinstance(obj, Dynamics):
                    for subobj in obj:
                        if isinstance(subobj, DynamicMark):
                            return subobj
        return None

    def _getObjectsContainedInDirectionType(self, classMatch):
        '''Get one or more objects contained in a direction type stored in this Direction. 
        '''
        post = []
        for directionType in self.componentList:
            if isinstance(directionType, Sound):
                continue 
            for obj in directionType:
                if isinstance(obj, classMatch):
                    post.append(obj)
        return post

    def getMetronome(self):
        '''Search this direction and determine if it contains a dynamic mark.

        
        >>> a = musicxml.mxObjects.Direction()
        >>> b = musicxml.mxObjects.DirectionType()
        >>> c = musicxml.mxObjects.Metronome()
        >>> b.append(c)
        >>> a.append(b)
        >>> a.getMetronome() is not None
        True
        '''
        found = self._getObjectsContainedInDirectionType(Metronome)
        if len(found) > 0:
            return found[0] # only return one fo rnow
        return None

    def getWedge(self):
        '''Search this direction and determine if it contains a dynamic mark.

        
        >>> a = musicxml.mxObjects.Direction()
        >>> b = musicxml.mxObjects.DirectionType()
        >>> c = musicxml.mxObjects.Wedge('crescendo')
        >>> b.append(c)
        >>> a.append(b)
        >>> a.getWedge() is not None
        True
        '''
        found = self._getObjectsContainedInDirectionType(Wedge)
        if len(found) > 0:
            return found[0]
        return None

    def getWords(self):
        '''Search this direction and determine if it contains a Words entity.

        
        >>> a = musicxml.mxObjects.Direction()
        >>> b = musicxml.mxObjects.DirectionType()
        >>> c = musicxml.mxObjects.Words('crescendo')
        >>> b.append(c)
        >>> a.append(b)
        >>> a.getWords() == [c]
        True
        >>> a.getWords()[0].charData
        'crescendo'
        '''
        found = self._getObjectsContainedInDirectionType(Words)
        if len(found) > 0:
            return found # return the lost
        return None

    def getCoda(self):
        '''Search this direction and determine if it contains a coda mark.

        
        >>> a = musicxml.mxObjects.Direction()
        >>> b = musicxml.mxObjects.DirectionType()
        >>> c = musicxml.mxObjects.Coda()
        >>> b.append(c)
        >>> a.append(b)
        >>> a.getCoda() is not None
        True
        '''
        found = self._getObjectsContainedInDirectionType(Coda)
        if len(found) > 0:
            return found[0] 
        return None

    def getSegno(self):
        '''Search this direction and determine if it contains a segno mark.

        
        >>> a = musicxml.mxObjects.Direction()
        >>> b = musicxml.mxObjects.DirectionType()
        >>> c = musicxml.mxObjects.Segno()
        >>> b.append(c)
        >>> a.append(b)
        >>> a.getSegno() is not None
        True
        '''
        found = self._getObjectsContainedInDirectionType(Segno)
        if len(found) > 0:
            return found[0] 
        return None

    def getBracket(self):
        '''Search this direction and determine if it contains a segno mark.

        
        >>> a = musicxml.mxObjects.Direction()
        >>> b = musicxml.mxObjects.DirectionType()
        >>> c = musicxml.mxObjects.Bracket()
        >>> b.append(c)
        >>> a.append(b)
        >>> a.getBracket() is not None
        True
        '''
        found = self._getObjectsContainedInDirectionType(Bracket)
        if len(found) > 0:
            return found[0] 
        return None

    def getDashes(self):
        '''Search this direction and determine if it contains a segno mark.

        
        >>> a = musicxml.mxObjects.Direction()
        >>> b = musicxml.mxObjects.DirectionType()
        >>> c = musicxml.mxObjects.Dashes()
        >>> b.append(c)
        >>> a.append(b)
        >>> a.getDashes() is not None
        True
        '''
        found = self._getObjectsContainedInDirectionType(Dashes)
        if len(found) > 0:
            return found[0] 
        return None


class DirectionType(MusicXMLElementList):
    '''DirectionType stores objects like Pedal, dynamics, wedge, and words
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



class Words(MusicXMLElement):
    '''A direction type that can be used for arbitrary text expressions, and font formatting 
    '''
    def __init__(self, charData=None):
        MusicXMLElement.__init__(self)
        self._tag = 'words'
        # attributes
        self._attr['justify'] = None # left, center, right; where the text hangs
        # font family does not display a difference with finale reader
        self._attr['font-family'] = None # comma sep. list
        self._attr['font-style'] = None # italic, normal
        self._attr['font-size'] = None # in points
        self._attr['font-weight'] = None # normal, bold        
        self._attr['letter-spacing'] = None # not sure the units .5 is double
        self._attr['enclosure'] = None # rectangle, oval

        # postions all seem relative to the top line of the staff, regardless
        # of the direction position attribute
        self._attr['default-y'] = None # in 10ths of a staff
        self._attr['default-x'] = None

        # line-height does not seem to work w/ multiline text expressions
        # values can be normal, 100, 120 , etc
        self._attr['line-height'] = None # text leading, number is % of font     
        # not likely to be used
        self._attr['text-direction'] = None
        self._attr['print-style'] = None
        self._attr['halign'] = None
        self._attr['valign'] = None # top, middle, bottom

        # text-rotation and text-decoration did not seem work on finale reader
        # char data stores the text to be displayed
        self.charData = charData


class Metronome(MusicXMLElementList):
    '''A direction type used to store tempo indications, consisting of a <beat-unit> tag (a duration) as well as a <per-unit> tag (a number). Also used to store metric modulations. 

    
    >>> m = musicxml.mxObjects.Metronome()
    >>> bu1 = musicxml.mxObjects.BeatUnit('half')
    >>> m.append(bu1)
    >>> m.isMetricModulation()
    False
    '''
    def __init__(self, charData=None):
        MusicXMLElementList.__init__(self)
        self._tag = 'metronome'
        self.charData = charData # no char data is stored
        # attributes
        self._attr['parentheses'] = None # comma sep. list

        # elements; on the component list is stored pairs of 
        # <beat-unit> and <per-minute> tags; up to two may be stored
        # may also be a <beat-unit-dot> tag after <beat unit>
        # <metronome-beam>
        # a subgroup may be the following; these are not implemented
        # <metronome-note>
        #   <metronome-relation>
        self.componentList = []

    def isMetricModulation(self):
        '''Return True if this Metronome defines a metric modulation. If there are more than on <beat-unit> tag, than this is True

        
        >>> m = musicxml.mxObjects.Metronome()
        >>> bu1 = musicxml.mxObjects.BeatUnit('half')
        >>> bu2 = musicxml.mxObjects.BeatUnit('quarter')
        >>> m.append(bu1)
        >>> m.append(bu2)
        >>> m.isMetricModulation()
        True

        '''
        count = 0
        for c in self.componentList:
            if isinstance(c, BeatUnit):
                count += 1
                if count >= 2:
                    return True
        return False

class BeatUnit(MusicXMLElement):
    '''Part of <metronome> tags
    '''
    def __init__(self, charData=None):
        MusicXMLElement.__init__(self)
        self._tag = 'beat-unit'
        self.charData = charData # char data is quarter/half/etc
        # attributes

class BeatUnitDot(MusicXMLElement):
    '''Part of <metronome> tags
    '''
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'beat-unit-dot'
        # no char data, no attributes; many may be used for double dots

class PerMinute(MusicXMLElement):
    '''Part of <metronome> tags
    '''
    def __init__(self, charData=None):
        MusicXMLElement.__init__(self)
        self._tag = 'per-minute'
        self.charData = charData # char data is the per minute time




class Sound(MusicXMLElement):
    '''A direction type used to store a large variety of performance indications.

    These tags seem to be found most often in <direction> tags, usually following a symbolic definition. For example, MetronomeMark definitions are often followed by a <sound> definition.

    Other <sound> tags are found after the <attributes> tag in a measure, often defining tempo. 
    '''
    def __init__(self, charData=None):
        MusicXMLElement.__init__(self)
        self._tag = 'sound'
        
        self._attr['tempo'] = None # a number in bpm where beat is quarter
        self._attr['dynamics'] = None # can be a value 1 through 127
        self._attr['damper-pedal'] = None # can be yes/no
        # when used with a pizzicato attribute, can define a midi-instrument
        self._attr['pizzicato'] = None # can be yes/no



class Offset(MusicXMLElement):
    '''A musicxml <offset> element can be found defined in the <direction> element. the charData stores a number that is the shift in divisions from the location of the tag. 
    '''
    def __init__(self, charData=None):
        MusicXMLElement.__init__(self)
        self._tag = 'offset'
        self.charData = charData





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
        self._attr['location'] = None # right-left-middle
        # elements
        self.barStyle = None # varieties include light-heavy
        # store a single ending object; this is used to tag start and end
        # of repeat brackets
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
    '''Ending tags are stored in Barline tags to indicate the start ane end of a repeat bracket, used to designate an alternate repeat. 
    '''
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'ending'
        # attributes
        # note: not sure what difference between stop and discontinue is
        self._attr['type'] = None # can be start, stop, discontinue
        self._attr['number'] = None # this is displayed indication


class Segno(MusicXMLElement):
    def __init__(self, type=None): # @ReservedAssignment
        MusicXMLElement.__init__(self)
        self._tag = 'segno'
        # attributes
        self._attr['default-y'] = None
        self._attr['default-x'] = None

class Coda(MusicXMLElement):
    def __init__(self, type=None): # @ReservedAssignment
        MusicXMLElement.__init__(self)
        self._tag = 'coda'
        # attributes
        self._attr['default-y'] = None
        self._attr['default-x'] = None



class Repeat(MusicXMLElement):
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'repeat'
        # attributes
        self._attr['times'] = None # can be start or end
        self._attr['direction'] = None # backward or forward


class Note(MusicXMLElement):
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'note'
        # notes can optionally store a reference to the mesure object that 
        # contains them. 
        self.external['measure'] = None
        # notes can optional store a reference to the last encounted attributes
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
        self._attr['pizzicato'] = None # may be yes or no -- duplicates somewhat the sound pizzicato attribute
        self._attr['default-x'] = None # X positioning

        # simple elements
        self.chord = False # boolean, default is false
        # # number, in div per quarter; not defined for graces
        self.duration = None 
        self.voice = None # numbers

        # note: to configre note size options, Type can have an attribute for
        # cue or large, eg: <type size="cue">quarter</type>
        # this will require a Type class

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
        '''Provide handling of merging when given an object of a different class. This change is done in place. 
        '''
        if isinstance(other, Pitch): 
            # if local pitch is None
            if self.pitchObj is None:
                new.pitchObj = other
            # if local pitch is not None, new already has it from copy
            # only set of favorSelf is not true
            elif self.pitchObj is not None:
                if not favorSelf:
                    new.pitchObj = other



class Forward(MusicXMLElement):
    def __init__(self, type=None): # @ReservedAssignment
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
    def __init__(self, type=None): # @ReservedAssignment
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
    def __init__(self, type=None): # @ReservedAssignment
        MusicXMLElementList.__init__(self)
        self._tag = 'rest'
        self.componentList = [] # stores display-step, display-octave

    def _getComponents(self):
        return self.componentList 

    # temporary; this needs to be set based on clef
    # this could take a clef as an argument
    def setDefaults(self):
        pass
#        displayStep = DisplayStep()
#        displayStep.set('charData', 'B') # was D4
#        displayOctave = DisplayOctave()
#        displayOctave.set('charData', '4')
#        self.append(displayStep)
#        self.append(displayOctave)


class DisplayStep(MusicXMLElement):
    def __init__(self, type=None): # @ReservedAssignment
        MusicXMLElement.__init__(self)
        self._tag = 'display-step'
        self.charData = None # only content

class DisplayOctave(MusicXMLElement):
    def __init__(self, type=None): # @ReservedAssignment
        MusicXMLElement.__init__(self)
        self._tag = 'display-octave'
        self.charData = None # only content




class Notations(MusicXMLElementList):
    '''
    Notations contains many elements, including Ornaments.
    Most of these are stored in the .componentList
    '''
    def __init__(self, type=None): # @ReservedAssignment
        MusicXMLElementList.__init__(self)
        self._tag = 'notations'
        self.componentList = []  # objects that are part of this node

    def _getComponents(self):
        return self.componentList 

    def getTuplets(self):
        '''
        A quick way to get all tuplets; there is likely only one, but
        we return a list anyhow.
        '''
        post = []        
        for part in self.componentList:
            if isinstance(part, Tuplet):
                post.append(part)
        return post

    def getTieds(self):
        '''
        A quick way to get all tied objects; there is likely only one,
        but we return a list anyhow.
        '''
        post = []        
        for part in self.componentList:
            if isinstance(part, Tied):
                post.append(part)
        return post

    def getArticulations(self):
        '''
        A quick way to get all articulations objects; there may be more than 
        one.

        Returns a list of ArticulationMark objects
        '''
        post = []        
        for part in self.componentList:
            if isinstance(part, Articulations):
                # note: articulation marks are being stripped out
                post += part.componentList
        return post

    def getTechnical(self):
        '''
        A quick way to get all technical objects; there may be more than 
        one.

        Returns a list of TechnicalMark objects
        '''
        post = []        
        for part in self.componentList:
            if isinstance(part, Technical):
                # note: articulation marks are being stripped out
                post += part.componentList
        return post


    def getFermatas(self):
        '''
        Get all Fermatas from the componentList as a list
        '''
        post = []        
        for part in self.componentList:
            if isinstance(part, Fermata):
                post.append(part)
        return post

    def getSlurs(self):
        '''
        Get all Slurs from the componentList as a list
        '''
        post = []        
        for part in self.componentList:
            if isinstance(part, Slur):
                post.append(part)
        return post

    def getOrnaments(self):
        '''
        Get all ornament objects stored on componentList. 
        There can be more than one.
        '''
        post = []        
        for part in self.componentList:
            if isinstance(part, Ornaments):
                post.append(part)
        return post

    def getGlissandi(self):
        '''
        Get all glissandi objects stored on components. 
        There can be more than one.

        
        >>> g1 = musicxml.mxObjects.Glissando()
        >>> g2 = musicxml.mxObjects.Glissando()
        >>> n = musicxml.mxObjects.Notations()
        >>> n.append(g1)
        >>> n.append(g2)
        >>> n.getGlissandi()
        [<glissando >, <glissando >]
        '''
        post = []        
        for part in self.componentList:
            if isinstance(part, Glissando):
                post.append(part)
        return post

    def getWavyLines(self):
        '''Get one or more wavy line objects Stored in Ornaments

        
        >>> wl = musicxml.mxObjects.WavyLine()
        >>> o = musicxml.mxObjects.Ornaments()
        >>> n = musicxml.mxObjects.Notations()
        >>> o.append(wl)
        >>> n.append(o)
        >>> n.getWavyLines()
        [<wavy-line >]
        '''
        post = []        
        for part in self.componentList:
            if isinstance(part, Ornaments):
                for sub in part:
                    if isinstance(sub, WavyLine):
                        post.append(sub)
        return post


    def getTremolos(self):
        '''Get one or more tremolo line objects Stored in Ornaments

        
        >>> t = musicxml.mxObjects.Tremolo()
        >>> o = musicxml.mxObjects.Ornaments()
        >>> n = musicxml.mxObjects.Notations()
        >>> o.append(t)
        >>> n.append(o)
        >>> n.getTremolos()
        [<tremolo >]
        '''
        post = []        
        for part in self.componentList:
            if isinstance(part, Ornaments):
                for sub in part:
                    if isinstance(sub, Tremolo):
                        post.append(sub)
        return post


class Dynamics(MusicXMLElementList):
    def __init__(self, type=None): # @ReservedAssignment
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
    def __init__(self, type=None): # @ReservedAssignment
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
    '''
    Class for the <technical> musicxml mark which contains
    things like <up-bow> etc. objects
    '''
    
    def __init__(self, type=None): # @ReservedAssignment
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
    '''
    This is not an XML object, but a container for all XML articulation tags.
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
    '''
    This is not an XML object, but a container for all XML technical tags.
    '''
    def __init__(self, tag):
        MusicXMLElement.__init__(self)
        if tag not in TECHNICAL_MARKS and tag != 'other-technical':
            raise MusicXMLException('no known technical tag %s' % tag)
        self._tag = tag
        # attributes
        self._attr['type'] = None
        self._attr['placement'] = None
        # character data 
        self.charData = None # found in fingering, pluck, other-artic


class Grace(MusicXMLElement):
    def __init__(self, type=None): # @ReservedAssignment
        MusicXMLElement.__init__(self)
        self._tag = 'grace'
        # attributes
        self._attr['steal-time-previous'] = None
        self._attr['steal-time-following'] = None
        self._attr['make-time'] = None
        self._attr['slash'] = None



class Wedge(MusicXMLElement):
    '''
    
    >>> w = musicxml.mxObjects.Wedge()
    >>> w.tag
    'wedge'
    '''
    def __init__(self, type=None): # @ReservedAssignment
        MusicXMLElement.__init__(self)
        self._tag = 'wedge'
        # attributes
        self._attr['type'] = None # crescendo, stop, or diminuendo
        self._attr['number'] = None # used for id
        self._attr['spread'] = None # in tenths

        self._attr['default-x'] = None 
        self._attr['default-y'] = None 
        self._attr['relative-x'] = None
        self._attr['relative-y'] = None


class OctaveShift(MusicXMLElement):
    '''
    
    >>> os = musicxml.mxObjects.OctaveShift()
    >>> os.tag
    'octave-shift'
    '''
    def __init__(self, type=None): # @ReservedAssignment
        MusicXMLElement.__init__(self)
        self._tag = 'octave-shift'

        # attributes
        self._attr['type'] = None # up-down-stop
        self._attr['number'] = None # used for id
        self._attr['size'] = None # integer, 8 is default, 15 is two octaves


class Bracket(MusicXMLElement):
    '''
    
    >>> b = musicxml.mxObjects.Bracket()
    >>> b.tag
    'bracket'
    '''
    def __init__(self, type=None): # @ReservedAssignment
        MusicXMLElement.__init__(self)
        self._tag = 'bracket'

        # attributes
        self._attr['type'] = None # start/stop
        self._attr['number'] = None # used for id
        self._attr['line-end'] = None 
        self._attr['end-length'] = None 
        self._attr['line-type'] = None 

        self._attr['default-x'] = None 
        self._attr['default-y'] = None 
        self._attr['relative-x'] = None 
        self._attr['relative-y'] = None 


class WavyLine(MusicXMLElement):
    '''A wavy line that extends across many notes or measures.

    
    >>> wl = musicxml.mxObjects.WavyLine()
    >>> wl.tag
    'wavy-line'
    '''
    def __init__(self, type=None): # @ReservedAssignment
        MusicXMLElement.__init__(self)
        self._tag = 'wavy-line'
        # attributes
        self._attr['type'] = None # start/stop/continue
        self._attr['number'] = None # used for id
        self._attr['default-x'] = None 
        self._attr['default-y'] = None 
        self._attr['relative-x'] = None 
        self._attr['relative-y'] = None 
        self._attr['placement'] = None # above or below

class Glissando(MusicXMLElement):
    '''
    
    >>> g = musicxml.mxObjects.Glissando()
    >>> g.tag
    'glissando'
    '''
    def __init__(self, type=None): # @ReservedAssignment
        MusicXMLElement.__init__(self)
        self._tag = 'glissando'
        # attributes
        self._attr['type'] = None # start/stop
        self._attr['number'] = None # used for id
        self._attr['line-type'] = None # solid, dashed, dotted, wavy
        # character data: this is the glissando label, if present
        self.charData = None


class Dashes(MusicXMLElement):
    '''
    
    >>> d = musicxml.mxObjects.Dashes()
    >>> d.tag
    'dashes'
    '''
    def __init__(self, type=None): # @ReservedAssignment
        MusicXMLElement.__init__(self)
        self._tag = 'dashes'

        # attributes
        self._attr['type'] = None # start/stop
        self._attr['number'] = None # used for id
        self._attr['default-x'] = None 
        self._attr['default-y'] = None 
        self._attr['relative-x'] = None 
        self._attr['relative-y'] = None 


class Ornaments(MusicXMLElementList):
    '''The Ornaments tag wraps the following musicxml entities: trill-mark, turn, delayed-turn, inverted-turn, shake, wavy-line, mordent, inverted mordent, schleifer, tremolo, other-ornament. 

    Ornaments are stored on the notations object. 
    '''
    def __init__(self, type=None): # @ReservedAssignment
        MusicXMLElementList.__init__(self)
        self._tag = 'ornaments'
        self.componentList = []  # objects tt are part of this node

    def _getComponents(self):
        return self.componentList 


class TrillMark(MusicXMLElement):
    def __init__(self, type=None): # @ReservedAssignment
        MusicXMLElement.__init__(self)
        self._tag = 'trill-mark'
        self._attr['placement'] = None # above/below

class Mordent(MusicXMLElement):
    def __init__(self, type=None): # @ReservedAssignment
        MusicXMLElement.__init__(self)
        self._tag = 'mordent'
        self._attr['long'] = None # yes/no

class InvertedMordent(MusicXMLElement):
    def __init__(self, type=None): # @ReservedAssignment
        MusicXMLElement.__init__(self)
        self._tag = 'inverted-mordent'


class Turn(MusicXMLElement):
    def __init__(self, type=None): # @ReservedAssignment
        MusicXMLElement.__init__(self)
        self._tag = 'turn'

class DelayedTurn(MusicXMLElement):
    def __init__(self, type=None): # @ReservedAssignment
        MusicXMLElement.__init__(self)
        self._tag = 'delayed-turn'

class InvertedTurn(MusicXMLElement):
    def __init__(self, type=None): # @ReservedAssignment
        MusicXMLElement.__init__(self)
        self._tag = 'inverted-turn'

class AccidentalMark(MusicXMLElement):
    '''Used inside an ornament definition; chardata holds the
    accidental type
    '''
    def __init__(self, type=None): # @ReservedAssignment
        MusicXMLElement.__init__(self)
        self._tag = 'accidental-mark'

class Shake(MusicXMLElement):
    def __init__(self, type=None): # @ReservedAssignment
        MusicXMLElement.__init__(self)
        self._tag = 'shake'

class Schleifer(MusicXMLElement): # type of slide
    def __init__(self, type=None): # @ReservedAssignment
        MusicXMLElement.__init__(self)
        self._tag = 'schleifer'


class Tremolo(MusicXMLElement): 
    '''Tremolo may or may not extend over multiple notes.
    Char data may store integer number.
    '''
    def __init__(self, type=None): # @ReservedAssignment
        MusicXMLElement.__init__(self)
        self._tag = 'tremolo'
        self.charData = None
        # type may or may not be defined
        self._attr['type'] = None # start or stop; 
        #self._attr['number'] = None # for id

class Notehead(MusicXMLElement):
    def __init__(self, type=None): # @ReservedAssignment
        MusicXMLElement.__init__(self)
        self._tag = 'notehead'
        # attributes
        self._attr['filled'] = None
        self._attr['parentheses'] = None
        self._attr['color'] = None
        # character data: this is the notehead type/shape
        self.charData = None

# valid notehead values
#"slash", "triangle", "diamond", "square", "cross", "x" , "circle-x", "inverted triangle", "arrow down", "arrow up", "slashed", "back slashed", "normal", "cluster", "none", "do", "re", "mi", "fa", "so", "la", "ti" 

class Dot(MusicXMLElement):
    def __init__(self, type=None): # @ReservedAssignment
        MusicXMLElement.__init__(self)
        self._tag = 'dot'
    

class Tie(MusicXMLElement):
    def __init__(self, type=None): # @ReservedAssignment
        MusicXMLElement.__init__(self)
        self._tag = 'tie'
        # attributes
        self._attr['type'] = type


class Fermata(MusicXMLElement):
    def __init__(self, type=None): # @ReservedAssignment
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
        self.syllabic = None # begin, middle, end, or single
        self.text = None

    def filterLyric(self, text):
        '''
        Remove and fix character strings that cause problems in MusicXML
        '''
        # this results in incorrect encoding of </>
        #text = xml.sax.saxutils.escape(text)
        if (text is None):
            return None
        text = text.replace('>', six.unichr(62))
        text = text.replace('<', six.unichr(60))
        text = text.replace('&', six.unichr(38))

        # need to remove hyphens; but &mdash; and similar do not work
        text = text.replace('-', six.unichr(8211))
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


#-------------------------------------------------------------------------------
# Harmony and components
# tags/objects defined here:
# harmony, root, kind, bass, degree, degree-value, degree-alter, degree-type

# the following tags are simple entities:
# inversion, function,
# root-step, root-alter, bass-step, bass-alter,

class Harmony(MusicXMLElementList):
    '''A harmony tag stores a root, kind -- eventually becomes converted
    to a music21 ChordSymbol object (not Harmony; though ChordSymbol is a
    subclass of the music21 object called Harmony, which also deals with
    Figured bass and Roman Numerals.
    '''
    def __init__(self):
        MusicXMLElementList.__init__(self)
        self._tag = 'harmony'

        self.rootObj = None # object
        self.function = None # a string, I, II, iii
        self.kindObj = None # object
        self.inversion = None # non negative integer, 0 for root
        self.bassObj = None # object
        self.degreeObj = None # object
    
        self.componentList = [] # list of HarmonyChord objects?

        self._crossReference['kindObj'] = ['kind']
        self._crossReference['rootObj'] = ['root']
        self._crossReference['bassObj'] = ['bass']
        self._crossReference['degreeObj'] = ['degree']

    def _getComponents(self):
        c = []
        c = c + self.componentList
        c.append(self.rootObj)
        c.append(('function', self.function))
        c.append(self.kindObj)
        c.append(('inversion', self.inversion)) 
        c.append(self.bassObj)
        c.append(self.degreeObj)
        return c

class Root(MusicXMLElement):
    '''A root defines a pitch, with a step and an alter
    '''
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'root'
        # simple entities
        self.rootStep = None 
        self.rootAlter = None

    def _getComponents(self):
        c = []
        # as simple entities, must provide tag name here
        c.append(('root-step', self.rootStep))
        c.append(('root-alter', self.rootAlter))
        return c

class Bass(MusicXMLElement):
    '''A root defines a pitch, with a step and an alter
    '''
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'bass'
        # simple entities
        self.bassStep = None 
        self.bassAlter = None

    def _getComponents(self):
        c = []
        # as simple elements, must provide tag name here
        c.append(('bass-step', self.bassStep))
        c.append(('bass-alter', self.bassAlter))
        return c

class Kind(MusicXMLElement):
    '''A harmony tag stores a root, kind 
    '''
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'kind'
        # the type of chord, common values are 'dominant', 'major', etc
        self.charData = None 
        # The text attribute describes how the kind should be spelled if not using symbols
        self._attr['text'] = None # can be the text as displayed, like 7
        self._attr['use-symbols'] = None  # use or no
        self._attr['stack-degrees'] = None # yes or no
        self._attr['parentheses-degrees'] = None # yes or no
        self._attr['bracket-degrees'] = None # yes or no
        # not added: print-style, haligh, and valign attributeGroups

class Degree(MusicXMLElementList):
    '''The degree type is used to add, alter, or subtract individual notes in the chord.
    '''
    def __init__(self):
        MusicXMLElementList.__init__(self)
        self._tag = 'degree'
        self.componentList = [] # triples of degree value, alter, type

    def _getComponents(self):
        c = []
        c = c + self.componentList
        return c

class DegreeValue(MusicXMLElement):
    '''Stores 1 for root, 3 for third, etc
    '''
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'degree-value'
        self.charData = None # stores 

class DegreeAlter(MusicXMLElement):
    '''Chromatic alteration of current degree
    '''
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'degree-alter'
        self.charData = None # stores semitones values, 1, -1, etc
        # if +/- should be used instead of flat/sharp
        self._attr['plus-minus'] = None 

class DegreeType(MusicXMLElement):
    '''addition, alteration, subtraction relative to the kind of current chord
    '''
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'degree-type'
        self.charData = None # add, alter, subtract


#-------------------------------------------------------------------------------


class Tuplet(MusicXMLElement):
    '''Stored in notations object and governs presentation and bracket.
    '''
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



# Layout elements in a print statement only apply to the 
# current page, system, staff, or measure. Music that follows 
# continues to take the default values from the layout included in the defaults element.

class Defaults(MusicXMLElementList):
    def __init__(self):
        '''From the MusicXML schema:
        
        The defaults type specifies score-wide defaults for scaling, layout, and appearance::

            <xs:sequence>
                <xs:element name="scaling" type="scaling" minOccurs="0"/>
                <xs:group ref="layout"/>
                <xs:element name="appearance" type="appearance" minOccurs="0"/>
                <xs:element name="music-font" type="empty-font" minOccurs="0"/>
                <xs:element name="word-font" type="empty-font" minOccurs="0"/>
                <xs:element name="lyric-font" type="lyric-font" minOccurs="0" maxOccurs="unbounded"/>
                <xs:element name="lyric-language" type="lyric-language" minOccurs="0" maxOccurs="unbounded"/>
            </xs:sequence>

        Return defaults.
        '''
        MusicXMLElementList.__init__(self)
        self._tag = 'defaults'
        # attributes
        # elements
        self.scalingObj = None
        self.layoutList = []
        self.appearanceObj = None
        self.musicFontObj = None
        self.wordFontObj = None
        self.lyricFontObj = None
        self.lyricLanguage = None
        self.componentList = []
    
    def _getComponents(self):
        c = []
        c.append(self.scalingObj)
        c = c + self.layoutList
        c.append(self.appearanceObj)
        c.append(self.musicFontObj)
        c.append(self.wordFontObj)
        c.append(self.lyricFontObj)
        c.append(self.lyricLanguage)
        return c

class Scaling(MusicXMLElement):
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'scaling'
        # attributes
        self.millimeters = None
        self.tenths = None

    def _getComponents(self):
        c = [] 
        # place BEFORE for musicxml components
        c.append(('millimeters', self.millimeters))
        c.append(('tenths', self.tenths))
        return c



class Print(MusicXMLElementList):
    def __init__(self):
        '''
        from direction.mod:

            The print element contains general printing parameters,
            including the layout elements defined in the layout.mod
            file. The part-name-display and part-abbreviation-display
            elements used in the score.mod file may also be used here
            to change how a part name or abbreviation is displayed over
            the course of a piece. They take effect when the current
            measure or a succeeding measure starts a new system.
            
            The new-system and new-page attributes indicate whether
            to force a system or page break, or to force the current
            music onto the same system or page as the preceding music.
            Normally this is the first music data within a measure.
            If used in multi-part music, they should be placed in the
            same positions within each part, or the results are
            undefined. The page-number attribute sets the number of a
            new page; it is ignored if new-page is not "yes". Version
            2.0 adds a blank-page attribute. This is a positive integer
            value that specifies the number of blank pages to insert
            before the current measure. It is ignored if new-page is
            not "yes". These blank pages have no music, but may have
            text or images specified by the credit element. This is
            used to allow a combination of pages that are all text,
            or all text and images, together with pages of music.
        
            Staff spacing between multiple staves is measured in
            tenths of staff lines (e.g. 100 = 10 staff lines). This is
            deprecated as of Version 1.1; the staff-layout element
            should be used instead. If both are present, the
            staff-layout values take priority.
        
            Layout elements in a print statement only apply to the
            current page, system, staff, or measure. Music that
            follows continues to take the default values from the
            layout included in the defaults element.

            <!ELEMENT print (page-layout?, system-layout?, staff-layout*,
            measure-layout?, measure-numbering?, part-name-display?,
            part-abbreviation-display?)>
            <!ATTLIST print
            staff-spacing %tenths; #IMPLIED
            new-system %yes-no; #IMPLIED
            new-page %yes-no; #IMPLIED
            blank-page NMTOKEN #IMPLIED
            page-number CDATA #IMPLIED>

        Supported in music21: 
        page-layout
        system-layout
        new-system
        new-page
        page-number
        '''
        MusicXMLElementList.__init__(self)
        self._tag = 'print'
        # attributes
        self._attr['new-system'] = None # yes /no
        self._attr['new-page'] = None # yes/no
        self._attr['page-number'] = None # yes/no
        # elements
        self.componentList = [] # contains: page-layout, system-layout, measure-layout, numerous others


class PageLayout(MusicXMLElementList):
    def __init__(self):
        MusicXMLElementList.__init__(self)
        self._tag = 'page-layout'
        # elements
        self.pageHeight = None #
        self.pageWidth = None #
        self.componentList = [] # contains: page-margins

    def _getComponents(self):
        c = [] 
        # place BEFORE for musicxml components
        c.append(('page-height', self.pageHeight))
        c.append(('page-width', self.pageWidth))
        c += self.componentList
        return c

class PageMargins(MusicXMLElement):
    def __init__(self):
        '''
        Does not support the type = (odd|even|both) attribute
        '''
        MusicXMLElement.__init__(self)
        self._tag = 'page-margins'
        # simple elements
        self.leftMargin = None
        self.rightMargin = None
        self.topMargin = None
        self.bottomMargin = None

    def _getComponents(self):
        c = []
        c.append(('left-margin', self.leftMargin))
        c.append(('right-margin', self.rightMargin))
        c.append(('top-margin', self.topMargin))
        c.append(('bottom-margin', self.bottomMargin))
        return c


class SystemLayout(MusicXMLElementList):
    def __init__(self):
        MusicXMLElementList.__init__(self)
        self._tag = 'system-layout'
        # elements
        self.systemDistance = None #
        self.topSystemDistance = None
        self.componentList = [] # contains: system margins

    def _getComponents(self):
        c = [] 
        c += self.componentList
        # place after components
        c.append(('system-distance', self.systemDistance))
        if self.topSystemDistance is not None:
            c.append(('top-system-distance', self.topSystemDistance))
        return c

class SystemMargins(MusicXMLElement):
    def __init__(self):
        MusicXMLElement.__init__(self)
        self._tag = 'system-margins'
        # simple elements
        self.leftMargin = None
        self.rightMargin = None
        self.topMargin = None
        self.bottomMargin = None

    def _getComponents(self):
        c = []
        c.append(('left-margin', self.leftMargin))
        c.append(('right-margin', self.rightMargin))
        c.append(('top-margin', self.topMargin))
        c.append(('bottom-margin', self.bottomMargin))
        return c

class StaffLayout(MusicXMLElementList):
    def __init__(self):
        MusicXMLElementList.__init__(self)
        self._tag = 'staff-layout'
        # elements
        self.staffDistance = None #
        self.componentList = [] # contains: nothing?
        self._attr['number'] = None # staff number for multistaff parts

    def _getComponents(self):
        c = [] 
        c += self.componentList
        # place after components
        c.append(('staff-distance', self.staffDistance))
        return c


#-------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):
    '''Tests that require acces to external files
    '''
    def runTest(self):
        pass

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
        '''Test copying all objects defined in this module
        '''
        import types
        for part in sys.modules[self.__module__].__dict__:
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
                i = copy.copy(obj)
                j = copy.deepcopy(obj)

    def testTagLib(self):
        t = TagLib()
        # create some conditions that would trigger an error
        t['sign'].charData = 'G'
        t['pitch'].start()
        ok, unused_msg = t.audit()
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
        import xml.dom.minidom
        aParsed = xml.dom.minidom.parseString(a.xmlStr())
        aExpected = xml.dom.minidom.parseString(aExpected)
        self.assert_(self._compareParsed(aParsed.documentElement, 
                aExpected.documentElement))



    def testPrimitiveXMLOutA(self):
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



    def testPrimitiveXMLOutB(self):
        p = Print()
        p.set('new-system', 'yes')

        sl = SystemLayout()

        sm = SystemMargins()
        sm.set('leftMargin', 20)
        sm.set('rightMargin', 30)
        sm.set('topMargin', 40)
        sm.set('bottomMargin', 50)

        sl.append(sm) 
        # system distance contained in sys layout
        sl.systemDistance = 55

        p.append(sl)

        #print p.xmlStr()

        pExpected = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE score-partwise
  PUBLIC '-//Recordare//DTD MusicXML 2.0 Partwise//EN'
  'http://www.musicxml.org/dtds/partwise.dtd'>
<print new-system="yes">
  <system-layout>
    <system-margins>
      <left-margin>20</left-margin>
      <right-margin>30</right-margin>
      <top-margin>40</top-margin>
      <bottom-margin>50</bottom-margin>
    </system-margins>
    <system-distance>55</system-distance>
  </system-layout>
</print>'''
        self._compareXml(p, pExpected)



    def testPrimitiveXMLOutC(self):
        i = Lyric()
        i.set('number', 3)
        i.set('syllabic', 'single')
        i.set('text', 'Mai,')
        iExpected = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE score-partwise
  PUBLIC '-//Recordare//DTD MusicXML 2.0 Partwise//EN'
  'http://www.musicxml.org/dtds/partwise.dtd'>
<lyric number="3">
  <syllabic>single</syllabic>
  <text>Mai,</text>
</lyric>
'''
        self._compareXml(i, iExpected)


        k = Slur()
        k.set('number', 1)
        k.set('placement', 'below')
        k.set('type', 'start')
        kExpected = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE score-partwise
  PUBLIC '-//Recordare//DTD MusicXML 2.0 Partwise//EN'
  'http://www.musicxml.org/dtds/partwise.dtd'>
<slur number="1" placement="below" type="start"/>
'''
        self._compareXml(k, kExpected)



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
        for className in [Score, Work, Identification, Creator, Encoding, Software, PartList, 
                          PartGroup, ScorePart, ScoreInstrument, MIDIInstrument, Part, Measure, 
                          Attributes, Key, KeyStep, KeyAlter, KeyOctave, Transpose, Time, Clef, 
                          Direction, DirectionType, MeasureStyle, Barline, Ending, Repeat, Note, 
                          Forward, Backup, Notations, Dynamics, Articulations, Technical, Grace, 
                          Notehead, Dot, Tie, Fermata, Accidental, Slur, Tied, Beam, Lyric, Pitch, 
                          TimeModification, Tuplet]:

        # need args
        # DynamicMark, ArticulationMark, TechnicalMark
            a = className()
            a.setDefaults()

    def testMergeAttributes(self):
        a1 = Attributes()
        a2 = Attributes()
        
        a1.divisions = 10

        mxClef = Clef()
        mxClef.sign = 'G'
        a2.clefList.append(mxClef)
        self.assertEqual(a2.get('clefList'), [mxClef])

        ax = Attributes()
        ax = ax.merge(a1)
        ax = ax.merge(a2)

        self.assertEqual(ax.divisions, 10)
        self.assertEqual(ax.clefList[0].sign, 'G')

    def testMergeScore(self):

        mxScore1 = Score()
        mxScore1.set('movementTitle', 'mvt title')
        mxScore1.set('movementNumber', 'third')

        mxWork = Work()
        mxWork.set('workTitle', 'work title')
        mxScore1.set('workObj', mxWork)

        mxId = Identification()
        mxCreator = Creator()
        mxCreator.set('charData', 'creator name')
        mxCreator.set('type', 'composer')

        mxId.set('creatorList', [mxCreator])
        mxScore1.set('identificationObj', mxId)

        mxScore1XMLStr = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE score-partwise
  PUBLIC '-//Recordare//DTD MusicXML 2.0 Partwise//EN'
  'http://www.musicxml.org/dtds/partwise.dtd'>
<score-partwise>
  <work>
    <work-title>work title</work-title>
  </work>
  <movement-number>third</movement-number>
  <movement-title>mvt title</movement-title>
  <identification>
    <creator type="composer">creator name</creator>
  </identification>
</score-partwise>
"""
        self._compareXml(mxScore1, mxScore1XMLStr)
        mxScore2 = Score()
        self.assertEqual(mxScore2.get('movementNumber'), None)
        mxScore2 = mxScore2.merge(mxScore1)
        self.assertEqual(mxScore2.get('movementNumber'), 'third')


        #print mxScore2.xmlStr()
        # if we get the same thing out of the xml, we have merged
        self._compareXml(mxScore2, mxScore1XMLStr)


    def testHarmonyA(self):
        k = Kind()
        k.charData = 'major'
        k.set('text', ' ') # set as an empty string to hide

        r = Root()
        r.set('rootStep', 'B')
        r.set('rootAlter', '-1')

        b = Bass()
        b.set('bassStep', 'D')
        b.set('bassAlter', None)

        d = Degree()
        dv = DegreeValue()
        dv.set('charData', 5)
        da = DegreeAlter()
        da.set('charData', 1)
        dt = DegreeType() # add, alter, subtract
        dt.set('charData', 'alter')

        d.append(dv)
        d.append(da)
        d.append(dt)

        h = Harmony()       
        h.set('root', r)
        h.set('kind', k)
        h.set('bass', b)
        h.set('inversion', 1)
        h.set('degree', d)
        h.set('function', 'V')

        #print h.xmlStr()

        expected = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE score-partwise
  PUBLIC '-//Recordare//DTD MusicXML 2.0 Partwise//EN'
  'http://www.musicxml.org/dtds/partwise.dtd'>
<harmony>
  <root>
    <root-step>B</root-step>
    <root-alter>-1</root-alter>
  </root>
  <function>V</function>
  <kind text=" ">major</kind>
  <inversion>1</inversion>
  <bass>
    <bass-step>D</bass-step>
  </bass>
  <degree>
    <degree-value>5</degree-value>
    <degree-alter>1</degree-alter>
    <degree-type>alter</degree-type>
  </degree>
</harmony>
"""
        self._compareXml(h, expected)







#-------------------------------------------------------------------------------
if __name__ == "__main__":
    # this is a temporary hack to get encoding working right
    # this may not be the best way to do this
    if six.PY2:
        reload(sys) # @UndefinedVariable
        sys.setdefaultencoding("utf-8") # @UndefinedVariable

    import music21
    music21.mainTest(Test)

# 
# 
#     if len(sys.argv) != 2:
#         music21.mainTest(Test)
# 
# 
#     elif len(sys.argv) == 2:
#         #te = TestExternal()
#         t = Test()
#         t.testBarlineRepeat()
# 
# #         if os.path.isdir(sys.argv[1]): 
# #             pass
# #             #te.testInputDirectory(sys.argv[1])
# #         else: # assume it is a single file
# #             #te.testOpen(sys.argv[1])
# 
# 


#------------------------------------------------------------------------------
# eof

