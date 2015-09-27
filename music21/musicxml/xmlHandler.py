# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         musicxml/xmlHandler.py
# Purpose:      Translate from MusicXML mxObjects to music21 objects
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Converts musicxml xml text to the intermediate mxObjects format.
'''
from music21.musicxml import mxObjects as musicxmlMod

import io
import sys
from music21.ext import six, chardet

# in order for sax parsing to properly handle unicode strings w/ unicode chars
# stored in StringIO.StringIO, this update is necessary
# http://stackoverflow.com/questions/857597/setting-the-encoding-for-sax-parser-in-python

# N.B. Without this change reload(sys) breaks IDLE!
if six.PY2:
    currentStdOut = sys.stdout
    currentStdIn = sys.stdin
    currentStdErr = sys.stderr
    try:
        reload(sys) # @UndefinedVariable
        sys.setdefaultencoding('utf-8') # @UndefinedVariable
    except: # Python3
        pass
    
    sys.stdout = currentStdOut
    sys.stdin = currentStdIn
    sys.stderr = currentStdErr

import copy
import os
import unittest

from music21.ext.six import StringIO, BytesIO

try:
    import cPickle as pickleMod # much faster.. on python2..
except ImportError:
    # in case we're on Jython, etc. or Py3
    import pickle as pickleMod

import xml.sax

from music21.base import VERSION

from music21 import environment
_MOD = 'musicxml/xmlHandler.py'
environLocal = environment.Environment(_MOD)


class MusicXMLHandlerException(musicxmlMod.MusicXMLException):
    pass

#-------------------------------------------------------------------------------
class Handler(xml.sax.ContentHandler):
    '''
    The SAX handler reads the MusicXML file and builds a 
    corresponding MusicXMLElement object structure.

    this is the main conversion handler for musicxml to mxObjects
    '''
   
    def __init__(self, tagLib=None):
        if tagLib == None:
            self.t = musicxmlMod.TagLib()
        else:
            self.t = tagLib
        #environLocal.printDebug(['creating Handler'])

        # this is in use in characters()
        self._currentTag = None # store current tag object

        self._mxObjs = {} # store by key
        # initialize all to None
        for k in self.t.keys():
            self._mxObjs[k] = None

        # all objects built in processing
        # scoreObj is returned as content, contains everything
        # stores version of m21 used to create this file
        self._mxObjs['score'] = musicxmlMod.Score(VERSION) 

        # component objects; these might be better stored
        # in a dictionary, where _activeTags['tagName'] = None

        self._parts = [] # added to score obj
        # need to store last attribute obj accross multiple measures
        self._attributesObjLast = None
        # need to store last divisions accross mulitple mesausers
        self._divisionsLast = None
        self._timeObjLast = None

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
        '''
        Because each _Handler sub-class defines its own _tags, 
        and because each Tag knows whether it is to receive character data or not, 
        this method can be found in the base-class and need not be defined for each sub-class.
        '''
        # in all but a very few cases self.t[tag].charData = charData is 
        # sufficient for getting charData. however, in a few cases this
        # will not gather all data and cause very unexpected results

        # the sax do cs explain why: The Parser will call this method to report each chunk of character data. SAX parsers may return all contiguous character data in a single chunk, or they may split it into several chunks


        # the new approach simply uses the currentTag reference:
        # this is much faster!
        # Note: must manually pass char data from the Tag to the object in the
        # handler. see 'words' for an example
        #environLocal.printDebug(['got charData', repr(charData), self._currentTag.tag])
        if self._currentTag.status:
            self.t[self._currentTag.tag].charData += charData
            #environLocal.printDebug(['added charData', self._currentTag.tag])


    #---------------------------------------------------------------------------
    def startElement(self, name, attrs):
        '''
        This handler method, in general, simply creates the 
        appropriate MusicXMLElement object and stores it (in the _mxObjs dict). 
        Attributes are loaded if necessary. For a few entities (note, measure) addtional 
        special handling is necessary. 
        '''
        #environLocal.printDebug([self._debugTagStr('start', name, attrs)])

        #if name in self.t.tagsAll:
        try:
            self._currentTag = self.t[name]
        except KeyError:
            #environLocal.printDebug(['unhandled start element', name])
            return 

        self._currentTag.start() 

        # note and measure require loading in additional references
        if name == 'note':
            self._mxObjs[name] = musicxmlMod.Note()      
            # store a reference to the measure containing
            self._mxObjs[name].external['measure'] = self._mxObjs['measure']
            self._mxObjs[name].external['attributes'] = self._attributesObjLast
            self._mxObjs[name].external['divisions'] = self._divisionsLast
            self._mxObjs[name].loadAttrs(attrs)
        elif name == 'measure':
            self._mxObjs[name] = musicxmlMod.Measure()
            self._mxObjs[name].external['attributes'] = self._attributesObjLast
            self._mxObjs[name].external['divisions'] = self._divisionsLast
            # some attributes definitions do store time, and refer only
            # to the last defined time value; store here for access
            self._mxObjs[name].external['time'] = self._timeObjLast
            self._mxObjs[name].loadAttrs(attrs)

        # special handling for these simple entities. 
        elif name in musicxmlMod.DYNAMIC_MARKS or name == 'other-dynamics':
            self._mxObjs['dynamic-mark'] = musicxmlMod.DynamicMark(name)

        elif name in musicxmlMod.ARTICULATION_MARKS or name == 'other-articulation':
            self._mxObjs['articulation-mark'] = musicxmlMod.ArticulationMark(name)
            self._mxObjs['articulation-mark'].loadAttrs(attrs)

        elif name in musicxmlMod.TECHNICAL_MARKS or name == 'other-technical':
            self._mxObjs['technical-mark'] = musicxmlMod.TechnicalMark(name)
            self._mxObjs['technical-mark'].loadAttrs(attrs)


        # special handling for these tags
        elif name == 'score-partwise':
            self._mxObjs['score'].loadAttrs(attrs)
            self._mxObjs['score'].format = 'score-partwise'

        elif name == 'score-timewise':
            self._mxObjs['score'].loadAttrs(attrs)
            self._mxObjs['score'].format = 'score-timewise'
            raise MusicXMLHandlerException('timewise is not supported')

        # generic handling for all other tag types
        else:
            mxClassName = self.t.getClassName(name)            
            # not all tags have classes; some are simple entities
            if mxClassName is not None:
                if mxClassName == 'StaffDetails':
                    pass
                self._mxObjs[name] = mxClassName()
                # loading attrs when none are defined is not a problem
                self._mxObjs[name].loadAttrs(attrs)


    #---------------------------------------------------------------------------
    def endElement(self, name):
        '''
        This handler method builds up the nested MusicXMLElement objects. 
        For simple entities, the charData or attributes might be assigned 
        directly to the attribute of another MusicXMLElement. In other cases, 
        the MusicXMLElement object stored (in the _mxObjs dict) is assigned 
        to another MusicXMLElement.

        After assigning the MusicXMLElement to wherever it resides, 
        the storage location (the _mxObjs dict) must be set to None.
        '''
        #environLocal.printDebug([self._debugTagStr('end', name)])

        # do not reset self._currentTag; set in startElement
        try: # just test to return if not handling
            self.t[name]
        except KeyError:
            #environLocal.printDebug(['unhandled end element', name])
            return 

        # place most commonly used tags first
        if name == 'note':
            self._mxObjs['measure'].componentList.append(self._mxObjs['note'])

        elif name == 'voice':
            if self._mxObjs['note'] is not None: # not a forward/backup tag
                self._mxObjs['note'].voice = self._currentTag.charData
            else: # inside of backup tag
                pass
                #environLocal.printDebug([' cannot deal with this voice', self._currentTag.charData])

        elif name == 'duration':
            if self._mxObjs['note'] is not None: # not a forward/backup tag
                self._mxObjs['note'].duration = self._currentTag.charData
            elif self._mxObjs['backup'] is not None:
                self._mxObjs['backup'].duration = self._currentTag.charData
            elif self._mxObjs['forward'] is not None:
                self._mxObjs['forward'].duration = self._currentTag.charData
            else: # ignoring figured-bass
                pass
                #raise MusicXMLHandlerException('cannot handle duration tag at: %s' % self._getLocation())

        elif name == 'type':
            self._mxObjs['note'].type = self._currentTag.charData

        elif name == 'stem':
            self._mxObjs['note'].stem = self._currentTag.charData

        elif name == 'beam':
            self._mxObjs['beam'].charData = self._currentTag.charData
            self._mxObjs['note'].beamList.append(self._mxObjs['beam'])

        elif name == 'pitch':
            self._mxObjs['note'].pitchObj = self._mxObjs['pitch']

        elif name == 'step':
            self._mxObjs['pitch'].step = self._currentTag.charData

        elif name == 'octave':
            self._mxObjs['pitch'].octave = self._currentTag.charData

        elif name == 'alter':
            self._mxObjs['pitch'].alter = self._currentTag.charData


        elif name == 'notations': 
            self._mxObjs['note'].notationsObj = self._mxObjs['notations']

        elif name == 'rest':
            self._mxObjs['note'].restObj = self._mxObjs['rest']

        elif name == 'measure': # in endElement
            # measures need to be stored in order; numbers may have odd values
            # update note start times w/ measure utility method
            self._mxObjs['measure'].update()
            self._mxObjs['part'].componentList.append(self._mxObjs['measure'])

        elif name == 'slur': 
            self._mxObjs['notations'].componentList.append(self._mxObjs['slur'])

        elif name == 'accidental':
            self._mxObjs['accidental'].charData = self._currentTag.charData
            self._mxObjs['note'].accidentalObj = self._mxObjs['accidental']

        elif name == 'tie':
            self._mxObjs['note'].tieList.append(self._mxObjs['tie'])


        elif name == 'tied':
            self._mxObjs['notations'].componentList.append(self._mxObjs['tied'])

        elif name == 'direction':
            # only append if direction has components
            if self._mxObjs['direction'].componentList != []:                    
                self._mxObjs['measure'].componentList.append(
                    self._mxObjs['direction'])

        elif name == 'direction-type': 
            # only append of direction-type has components
            if self._mxObjs['direction-type'].componentList != []:
                self._mxObjs['direction'].componentList.append(
                    self._mxObjs['direction-type'])

        elif name == 'chord':
            self._mxObjs['note'].chord = True            

        elif name == 'dot': 
            self._mxObjs['note'].dotList.append(self._mxObjs['dot'])

        elif name == 'dynamics': 
            if self._mxObjs['notations'] is not None: 
                self._mxObjs['notations'].componentList.append(
                    self._mxObjs['dynamics'])
            elif self._mxObjs['direction-type'] is not None: 
                self._mxObjs['direction-type'].componentList.append(
                    self._mxObjs['dynamics'])
            else:
                raise MusicXMLHandlerException('do not know where these dynamics go', self._mxObjs['dynamics'])

        elif name == 'lyric':
            if self._mxObjs['note'] is not None: # can be associtaed w/ harmony tag
                self._mxObjs['note'].lyricList.append(self._mxObjs['lyric'])
            else:
                environLocal.printDebug(['cannot deal with this lyric'])

        elif name == 'syllabic':
            self._mxObjs['lyric'].syllabic = self._currentTag.charData

        elif name == 'text':
            self._mxObjs['lyric'].text = self._currentTag.charData

        elif name == 'trill-mark': 
            self._mxObjs['ornaments'].append(self._mxObjs['trill-mark'])

        elif name == 'mordent': 
            self._mxObjs['ornaments'].append(self._mxObjs['mordent'])

        elif name == 'inverted-mordent': 
            self._mxObjs['ornaments'].append(self._mxObjs['inverted-mordent'])

        elif name == 'turn':
            self._mxObjs['ornaments'].append(self._mxObjs['turn'])
 
        elif name == 'delayed-turn':
            self._mxObjs['ornaments'].append(self._mxObjs['delayed-turn'])
 
        elif name == 'inverted-turn':
            self._mxObjs['ornaments'].append(self._mxObjs['inverted-turn'])
 
        elif name == 'accidental-mark':
            # accidental-mark can be found either after a turn in ornaments
            # or in notations by itself
            if self._mxObjs['ornaments'] is not None:
                self._mxObjs['ornaments'].append(
                    self._mxObjs['accidental-mark'])
            elif self._mxObjs['notations'] is not None:
                self._mxObjs['notations'].append(
                    self._mxObjs['accidental-mark'])
            else:
                raise MusicXMLHandlerException('cannot find destination for AccidentalMark object')

        elif name == 'shake':
            self._mxObjs['ornaments'].append(self._mxObjs['shake'])

        elif name == 'schleifer':
            self._mxObjs['ornaments'].append(self._mxObjs['schleifer'])

        elif name == 'tremolo':
            self._mxObjs['tremolo'].charData = self._currentTag.charData
            self._mxObjs['ornaments'].append(self._mxObjs['tremolo'])

        elif name == 'sound':
            # sound can be store either in a Measure (less common) or in a
            # <direction> (not a <direction-type>)
            # if a direction obj is open, add there
            if self._mxObjs['direction'] is not None:
                #environLocal.printDebug(['inserting <sound> into _directionObj'])
                self._mxObjs['direction'].componentList.append(
                    self._mxObjs['sound'])
            elif self._mxObjs['measure'] is not None:
                self._mxObjs['measure'].componentList.append(
                    self._mxObjs['sound'])
                #environLocal.printDebug(['inserting <sound> into _measureObj'])

        elif name == 'metronome':  # branch location not optimized
            if self._mxObjs['direction-type'] is not None: 
                #environLocal.printDebug(['closing Metronome'])
                self._mxObjs['direction-type'].componentList.append(
                    self._mxObjs['metronome'])
            else:
                raise MusicXMLHandlerException('missing a direction tyoe container for a Metronome: %s' % self._mxObjs['metronome'])

        elif name == 'beat-unit':  
            if self._mxObjs['metronome'] is not None: 
                self._mxObjs['beat-unit'].charData = self._currentTag.charData
                self._mxObjs['metronome'].componentList.append(
                    self._mxObjs['beat-unit'])
                #environLocal.printDebug(['adding <beat-unit> to metronome'])
            else:
                raise MusicXMLHandlerException('found a <beat-unit> tag without a metronome object to store it within: %s' % self._mxObjs['beat-unit'])

        elif name == 'beat-unit-dot':  
            # no char data
            if self._mxObjs['metronome'] is not None: 
                self._mxObjs['metronome'].componentList.append(
                    self._mxObjs['beat-unit-dot'])
            else:
                raise MusicXMLHandlerException('found a <beat-unit-dot> tag without a metronome object to store it within: %s' % self._mxObjs['beat-unit'])

        elif name == 'per-minute':
            if self._mxObjs['metronome'] is not None: 
                self._mxObjs['per-minute'].charData = self._currentTag.charData
                self._mxObjs['metronome'].componentList.append(
                    self._mxObjs['per-minute'])
            else:
                raise MusicXMLHandlerException('found a <per-minute> tag without a metronome object to store it within: %s' % self._mxObjs['per-minute'])

        elif name == 'time-modification': 
            self._mxObjs['note'].timeModificationObj = self._mxObjs[
                                                      'time-modification']

        elif name == 'actual-notes': 
            self._mxObjs['time-modification'].actualNotes = self._currentTag.charData

        elif name == 'normal-notes': 
            self._mxObjs['time-modification'].normalNotes = self._currentTag.charData

        elif name == 'normal-type':
            self._mxObjs['time-modification'].normalType = self._currentTag.charData

        elif name == 'normal-dot': 
            self._mxObjs['time-modification'].normalDot = self._currentTag.charData

        elif name == 'tuplet': 
            self._mxObjs['notations'].componentList.append(
                self._mxObjs['tuplet'])

        elif name == 'attributes': # in endElement
            self._mxObjs['measure']._attributesObjList.append(
                self._mxObjs['attributes'])
            # this is the most recently found atttributes obj; not the final
            self._mxObjs['measure'].attributesObj = self._mxObjs['attributes']
            # update last found
            self._attributesObjLast = copy.deepcopy(self._mxObjs['attributes'])
            # remove current, as loaded into measure

        elif name == 'divisions':
            self._mxObjs['attributes'].divisions = self._currentTag.charData
            self._divisionsLast = self._currentTag.charData

        elif name == 'staff-details':
            self._mxObjs['attributes'].staffDetailsList.append(self._mxObjs['staff-details'])

        elif name == 'staff-size':
            self._mxObjs['staff-details'].staffSize = self._currentTag.charData
    
    
        elif name == 'staff-lines':
            self._mxObjs['staff-details'].staffLines = self._currentTag.charData

    
        elif name == 'forward':
            self._mxObjs['measure'].componentList.append(
                self._mxObjs['forward'])

        elif name == 'backup':
            self._mxObjs['measure'].componentList.append(self._mxObjs['backup'])

        elif name == 'grace':
            self._mxObjs['note'].graceObj = self._mxObjs['grace']

        # harmony and related objects
        elif name == 'harmony':
            self._mxObjs['measure'].componentList.append(
                self._mxObjs['harmony'])

        elif name == 'root':
            self._mxObjs['harmony'].rootObj = self._mxObjs['root']
        elif name == 'root-step':
            self._mxObjs['root'].rootStep = self._currentTag.charData
        elif name == 'root-alter':
            self._mxObjs['root'].rootAlter = self._currentTag.charData

        elif name == 'inversion':
            self._mxObjs['harmony'].inversion = self._currentTag.charData
        elif name == 'function':
            self._mxObjs['harmony'].function = self._currentTag.charData

        elif name == 'bass':
            self._mxObjs['harmony'].bassObj = self._mxObjs['bass']
        elif name == 'bass-step':
            self._mxObjs['bass'].bassStep = self._currentTag.charData
        elif name == 'bass-alter':
            self._mxObjs['bass'].bassAlter = self._currentTag.charData

        elif name == 'kind':
            self._mxObjs['kind'].charData = self._currentTag.charData
            self._mxObjs['harmony'].kindObj = self._mxObjs['kind']

        elif name == 'degree':
            self._mxObjs['harmony'].degreeObj = self._mxObjs['degree']
        elif name == 'degree-value':
            self._mxObjs['degree-value'].charData = self._currentTag.charData
            self._mxObjs['degree'].componentList.append(
                self._mxObjs['degree-value'])
        elif name == 'degree-alter':
            self._mxObjs['degree-alter'].charData = self._currentTag.charData
            self._mxObjs['degree'].componentList.append(
                self._mxObjs['degree-alter'])
        elif name == 'degree-type':
            self._mxObjs['degree-type'].charData = self._currentTag.charData
            self._mxObjs['degree'].componentList.append(
                self._mxObjs['degree-type'])



        # the position of print through sys-dist may not be optimized
        elif name == 'scaling':
            if self._mxObjs['defaults'] is not None:
                self._mxObjs['defaults'].scalingObj = self._mxObjs['scaling']
        elif name == 'millimeters': # simple element in scaling
            if self._mxObjs['scaling'] is not None:
                self._mxObjs['scaling'].millimeters = self._currentTag.charData
        elif name == 'tenths': # simple element in scaling
            if self._mxObjs['scaling'] is not None:
                self._mxObjs['scaling'].tenths = self._currentTag.charData
        
        elif name == 'print':
            # print are stored in Measure, before attributes
            if self._mxObjs['measure'] is not None: 
                self._mxObjs['measure'].componentList.append(
                    self._mxObjs['print'])

        elif name == 'page-layout':
            # has no attrs
            if self._mxObjs['print'] is not None: 
                self._mxObjs['print'].componentList.append(
                    self._mxObjs['page-layout'])
            elif self._mxObjs['defaults'] is not None:
                self._mxObjs['defaults'].layoutList.append(self._mxObjs['page-layout'])

        elif name == 'page-margins':
            if self._mxObjs['page-layout'] is not None: 
                self._mxObjs['page-layout'].componentList.append(
                    self._mxObjs['page-margins'])

        elif name == 'page-height': # simple element
            if self._mxObjs['page-layout'] is not None: 
                self._mxObjs['page-layout'].pageHeight = self._currentTag.charData

        elif name == 'page-width': # simple element
            if self._mxObjs['page-layout'] is not None:
                self._mxObjs['page-layout'].pageWidth = self._currentTag.charData

        elif name == 'system-layout':
            # has no attrs
            if self._mxObjs['print'] is not None: 
                self._mxObjs['print'].componentList.append(
                    self._mxObjs['system-layout'])
            elif self._mxObjs['defaults'] is not None:
                self._mxObjs['defaults'].layoutList.append(self._mxObjs['system-layout'])

        elif name == 'system-margins':
            if self._mxObjs['system-layout'] is not None:
                self._mxObjs['system-layout'].componentList.append(
                    self._mxObjs['system-margins'])

        elif name == 'left-margin': # simple element
            if self._mxObjs['system-margins'] is not None: 
                self._mxObjs['system-margins'].leftMargin = self._currentTag.charData
            elif self._mxObjs['page-margins'] is not None: 
                self._mxObjs['page-margins'].leftMargin = self._currentTag.charData

        elif name == 'right-margin': # simple element
            if self._mxObjs['system-margins'] is not None: 
                self._mxObjs['system-margins'].rightMargin = self._currentTag.charData
            elif self._mxObjs['page-margins'] is not None: 
                self._mxObjs['page-margins'].rightMargin = self._currentTag.charData

        elif name == 'top-margin': # simple element
            if self._mxObjs['system-margins'] is not None: 
                self._mxObjs['system-margins'].topMargin = self._currentTag.charData
            elif self._mxObjs['page-margins'] is not None: 
                self._mxObjs['page-margins'].topMargin = self._currentTag.charData

        elif name == 'bottom-margin': # simple element
            if self._mxObjs['system-margins'] is not None: 
                self._mxObjs['system-margins'].bottomMargin = self._currentTag.charData
            elif self._mxObjs['page-margins'] is not None: 
                self._mxObjs['page-margins'].bottomMargin = self._currentTag.charData

        elif name == 'system-distance': # simple element
            if self._mxObjs['system-layout'] is not None: 
                self._mxObjs['system-layout'].systemDistance = self._currentTag.charData

        elif name == 'top-system-distance': # simple element
            if self._mxObjs['system-layout'] is not None: 
                self._mxObjs['system-layout'].topSystemDistance = self._currentTag.charData

        elif name == 'staff-distance': # simple element
            if self._mxObjs['staff-layout'] is not None:
                self._mxObjs['staff-layout'].staffDistance = self._currentTag.charData
        elif name == 'staff-layout':
            # has optional attr number
            if self._mxObjs['print'] is not None: 
                self._mxObjs['print'].componentList.append(
                    self._mxObjs['staff-layout'])
            elif self._mxObjs['defaults'] is not None:
                self._mxObjs['defaults'].layoutList.append(self._mxObjs['staff-layout'])
        #----------------------

        elif name == 'notehead':
            self._mxObjs['notehead'].charData = self._currentTag.charData
            self._mxObjs['note'].noteheadObj = self._mxObjs['notehead']

        elif name == 'articulations': 
            self._mxObjs['notations'].componentList.append(
                self._mxObjs['articulations'])

        elif name == 'technical': 
            self._mxObjs['notations'].componentList.append(
                self._mxObjs['technical'])

        elif name == 'offset':
            if self._mxObjs['direction'] is not None:
                #environLocal.printDebug(['got an offset tag for a directionObj', self._currentTag.charData])
                self._mxObjs['direction'].offset = self._currentTag.charData
            else: # ignoring figured-bass
                environLocal.printDebug(['got an offset tag but no open directionObj', self._currentTag.charData])

        elif name == 'words':
            if self._mxObjs['direction-type'] is not None: 
                #environLocal.printDebug(['closing Words', 'self._mxObjs['words'].charData',  self._mxObjs['words'].charData])
                # must manually attach collected charData
                self._mxObjs['words'].charData = self._currentTag.charData
                self._mxObjs['direction-type'].componentList.append(
                                        self._mxObjs['words'])
            else:
                raise MusicXMLHandlerException('missing a container for a Words: %s' % self._mxObjs['words'])


        elif name == 'wedge': 
            if self._mxObjs['direction-type'] is not None: 
                self._mxObjs['direction-type'].componentList.append(
                    self._mxObjs['wedge'])
            else:
                raise MusicXMLHandlerException('missing direction type container: %s' % self._mxObjs['wedge'])


        elif name == 'octave-shift': 
            if self._mxObjs['direction-type'] is not None: 
                self._mxObjs['direction-type'].componentList.append(
                    self._mxObjs['octave-shift'])
            else:
                raise MusicXMLHandlerException('missing direction type container: %s' % self._mxObjs['octave-shift'])

        elif name == 'bracket': 
            if self._mxObjs['direction-type'] is not None: 
                self._mxObjs['direction-type'].componentList.append(
                    self._mxObjs['bracket'])
            else:
                raise MusicXMLHandlerException('missing direction type container: %s' % self._mxObjs['bracket'])

        elif name == 'wavy-line': 
            # goes in ornaments, which is in notations
            self._mxObjs['ornaments'].append(self._mxObjs['wavy-line'])

        elif name == 'glissando': 
            # goes in notations
            self._mxObjs['glissando'].charData = self._currentTag.charData            
            self._mxObjs['notations'].append(self._mxObjs['glissando'])

        elif name == 'dashes': 
            if self._mxObjs['direction-type'] is not None: 
                self._mxObjs['direction-type'].componentList.append(
                    self._mxObjs['dashes'])
            else:
                raise MusicXMLHandlerException('missing direction type container: %s' % self._mxObjs['dashes'])

        elif name == 'segno':
            if self._mxObjs['direction-type'] is not None: 
                #environLocal.printDebug(['closing Segno'])
                self._mxObjs['direction-type'].componentList.append(
                    self._mxObjs['segno'])
            else:
                raise MusicXMLHandlerException('missing a container for a Segno: %s' % self._mxObjs['segno'])

        elif name == 'coda':
            if self._mxObjs['direction-type'] is not None: 
                self._mxObjs['direction-type'].componentList.append(
                    self._mxObjs['coda'])
            else:
                raise MusicXMLHandlerException('missing a container for a Coda: %s' % self._mxObjs['coda'])


        elif name == 'ornaments': 
            self._mxObjs['notations'].append(self._mxObjs['ornaments'])


        # these tags are used in a group manner, where a pseudo-tag is
        # used to hold the mx object. 

        elif name in musicxmlMod.DYNAMIC_MARKS:
            self._mxObjs['dynamics'].componentList.append(
                self._mxObjs['dynamic-mark'])
            self._mxObjs['dynamic-mark'] = None # must do here, not below

        elif name == 'other-dynamics':
            self._mxObjs['dynamic-mark'].charData = self._currentTag.charData            
            self._mxObjs['dynamics'].componentList.append(
                self._mxObjs['dynamic-mark'])
            self._mxObjs['dynamic-mark'] = None # must do here, not below

        elif name in musicxmlMod.ARTICULATION_MARKS:
            self._mxObjs['articulations'].componentList.append(
                self._mxObjs['articulation-mark'])
            self._mxObjs['articulation-mark'] = None # must do here, not below

        elif name == 'other-articulation':
            self._mxObjs['articulation-mark'].charData = self._currentTag.charData            
            self._mxObjs['articulations'].componentList.append(
                self._mxObjs['articulation-mark'])
            self._mxObjs['articulation-mark'] = None # must do here, not below

        elif name in musicxmlMod.TECHNICAL_MARKS:
            if self._mxObjs['technical'] is not None:
                self._mxObjs['technical'].componentList.append(
                    self._mxObjs['technical-mark'])
            else: # could be w/n <frame-note>
                pass
            self._mxObjs['technical-mark'] = None # must do here, not below

        elif name == 'other-technical':
            self._mxObjs['technical-mark'].charData = self._currentTag.charData            
            self._mxObjs['technical'].componentList.append(
                self._mxObjs['technical-mark'])
            self._mxObjs['technical-mark'] = None # must do here, not below


        elif name == 'fermata':
            self._mxObjs['fermata'].charData = self._currentTag.charData  
            self._mxObjs['notations'].componentList.append(
                self._mxObjs['fermata'])

        # formerly part of handler score
        elif name == 'movement-title':
            self._mxObjs['score'].movementTitle = self._currentTag.charData

        elif name == 'movement-number':
            self._mxObjs['score'].movementNumber = self._currentTag.charData

        elif name == 'work':
            self._mxObjs['score'].workObj = self._mxObjs['work']

        elif name == 'work-title':
            self._mxObjs['work'].workTitle = self._currentTag.charData

        elif name == 'work-number':
            self._mxObjs['work'].workNumber = self._currentTag.charData

        elif name == 'identification':
            self._mxObjs['score'].identificationObj = self._mxObjs['identification']

        elif name == 'defaults':
            self._mxObjs['score'].defaultsObj = self._mxObjs['defaults']

        elif name == 'rights':
            self._mxObjs['identification'].rights = self._currentTag.charData

        elif name == 'creator':
            self._mxObjs['creator'].charData = self._currentTag.charData
            self._mxObjs['identification'].creatorList.append(
                self._mxObjs['creator'])

        elif name == 'credit':
            self._mxObjs['score'].creditList.append(self._mxObjs['credit'])

        elif name == 'credit-words':
            self._mxObjs['credit-words'].charData = self._currentTag.charData
            self._mxObjs['credit'].append(self._mxObjs['credit-words'])

        elif name == 'encoding':
            self._mxObjs['identification'].encodingObj = self._mxObjs['encoding']

        elif name == 'software':
            self._mxObjs['software'].charData = self._currentTag.charData
            self._mxObjs['encoding'].softwareList.append(
                self._mxObjs['software'])

        elif name == 'encoding-date':
            self._mxObjs['encoding'].encodingDate = self._currentTag.charData

        elif name == 'supports':
            self._mxObjs['encoding'].supportsList.append(
                self._mxObjs['supports'])


        # formerly part of handler part list
        elif name == 'part-group':
            self._mxObjs['part-list'].componentList.append(
                self._mxObjs['part-group'])

        elif name == 'group-name':
            self._mxObjs['part-group'].groupName = self._currentTag.charData

        elif name == 'group-symbol':
            self._mxObjs['part-group'].groupSymbol = self._currentTag.charData

        elif name == 'group-barline':
            self._mxObjs['part-group'].groupBarline = self._currentTag.charData

        elif name == 'score-instrument':
            self._mxObjs['score-part'].scoreInstrumentList.append(
                self._mxObjs['score-instrument'])

        elif name == 'instrument-name':
            self._mxObjs['score-instrument'].instrumentName = self._currentTag.charData

        elif name == 'instrument-abbreviation':
            self._mxObjs['score-instrument'].instrumentAbbreviation = self._currentTag.charData

        elif name == 'score-part':
            self._mxObjs['part-list'].componentList.append(
                self._mxObjs['score-part'])

        elif name == 'part-name':
            # copy completed character data and clear
            self._mxObjs['score-part'].partName = self._currentTag.charData

        elif name == 'score-instrument':                
            self._mxObjs['score-part'].scoreInstrumentList.append(
                self._mxObjs['score-instrument'])

        elif name == 'midi-instrument':                
            if self.t['score-part'].status: # may be in a <sound> def
                self._mxObjs['score-part'].midiInstrumentList.append( 
                    self._mxObjs['midi-instrument'])
             
        elif name == 'midi-channel':
            if self.t['score-part'].status:
                self._mxObjs['midi-instrument'].midiChannel = self._currentTag.charData

        elif name == 'midi-program':
            if self.t['score-part'].status:
                self._mxObjs['midi-instrument'].midiProgram = self._currentTag.charData

        # formerly part of handler part
        elif name == 'part':
            #environLocal.printDebug(['got part:', self._mxObjs['part']])
            self._parts.append(self._mxObjs['part']) # outermost container

        elif name == 'key':
            self._mxObjs['attributes'].keyList.append(self._mxObjs['key'])

        elif name == 'fifths':
            self._mxObjs['key'].fifths = self._currentTag.charData

        elif name == 'mode':
            self._mxObjs['key'].mode = self._currentTag.charData

        elif name == 'cancel':
            self._mxObjs['key'].cancel = self._currentTag.charData

        elif name == 'key-step':
            self._mxObjs['key-step'].charData = self._currentTag.charData
            self._mxObjs['key'].nonTraditionalKeyList.append(
                                    self._mxObjs['key-step'])

        elif name == 'key-alter':
            self._mxObjs['key-alter'].charData = self._currentTag.charData
            self._mxObjs['key'].nonTraditionalKeyList.append(
                    self._mxObjs['key-alter'])

        elif name == 'key-octave':
            self._mxObjs['key-octave'].charData = self._currentTag.charData
            self._mxObjs['key'].nonTraditionalKeyList.append(
                self._mxObjs['key-octave'])

        elif name == 'transpose':
            self._mxObjs['attributes'].transposeObj = self._mxObjs['transpose']

        elif name == 'diatonic':
            self._mxObjs['transpose'].diatonic = self._currentTag.charData

        elif name == 'chromatic':
            self._mxObjs['transpose'].chromatic = self._currentTag.charData

        elif name == 'octave-change':
            self._mxObjs['transpose'].octaveChange = self._currentTag.charData

        elif name == 'double': 
            self._mxObjs['transpose'].double = self._currentTag.charData

        elif name == 'time':
            self._mxObjs['attributes'].timeList.append(self._mxObjs['time'])
            self._timeObjLast = copy.deepcopy(self._mxObjs['time'])

        elif name == 'staves':
            self._mxObjs['attributes'].staves = self._currentTag.charData

        elif name == 'beats':
            self._mxObjs['time'].componentList.append(
                musicxmlMod.Beats(self._currentTag.charData))

        elif name == 'beat-type':
            self._mxObjs['time'].componentList.append(
                musicxmlMod.BeatType(self._currentTag.charData))

        elif name == 'clef':
            if len(self._mxObjs['measure']) == 0:
                # clef at beginning of measure into attributes
                self._mxObjs['attributes'].clefList.append(self._mxObjs['clef'])
            else:
                # mid-measure clefs into measure-components
                self._mxObjs['measure'].componentList.append(self._mxObjs['clef'])

        elif name == 'multiple-rest':
            self._mxObjs['measure-style'].multipleRest = self._currentTag.charData

        elif name == 'measure-style':
            self._mxObjs['attributes'].measureStyleObj = self._mxObjs['measure-style']

        elif name == 'sign':
            self._mxObjs['clef'].sign = self._currentTag.charData

        elif name == 'line':
            self._mxObjs['clef'].line = self._currentTag.charData

        elif name == 'clef-octave-change':
            self._mxObjs['clef'].clefOctaveChange = self._currentTag.charData

        elif name == 'display-step':
            # chara data loaded in object
            self._mxObjs['rest'].componentList.append(
                self._mxObjs['display-step'])

        elif name == 'display-octave':
            self._mxObjs['rest'].componentList.append(
                self._mxObjs['display-octave'])

        elif name == 'staff': 
            if self._mxObjs['note'] is not None: # not a forward/backup tag
                self._mxObjs['note'].staff = self._currentTag.charData
            # not a forward/backup tag
            elif self._mxObjs['direction'] is not None: 
                self._mxObjs['direction'].staff = self._currentTag.charData
            else:
                pass
                #environLocal.printDebug([' cannot deal with this staff', self._currentTag.charData])

        elif name == 'barline': 
            self._mxObjs['measure'].componentList.append(
                self._mxObjs['barline'])

        elif name == 'ending':
            self._mxObjs['barline'].endingObj = self._mxObjs['ending']

        elif name == 'bar-style': 
            self._mxObjs['barline'].barStyle = self._currentTag.charData

        elif name == 'repeat': 
            self._mxObjs['barline'].repeatObj = self._mxObjs['repeat']


        # after assigning the mxobj, it needs to be set back to None
        # can do this for all tags that are defined once closed
        if name != 'part-list':
            try:
                self._mxObjs[name] = None
            except KeyError:
                pass

        # clear and end
#         if name in self.t.tagsAll:
        self.t[name].clear() 
        self.t[name].end() 

        # do not do this!
        # self._currentTag = None


    #---------------------------------------------------------------------------
    def getContent(self):
        #environLocal.printDebug(["self._mxObjs['part-list']", self._mxObjs['part-list']])
        self._mxObjs['score'].partListObj = self._mxObjs['part-list']
        self._mxObjs['score'].componentList = self._parts
        return self._mxObjs['score']



#-------------------------------------------------------------------------------
class Document(object):
    '''Represent a MusicXML document, 
    importing and writing'''

    def __init__(self):
        # create one tagLib for efficiency
        self.tagLib = musicxmlMod.TagLib()
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

    def _load(self, fileLike, isFile=True, audit=False):
        saxparser = self._getParser()
        #t = common.Timer()
        #t.start()
        # call the handler with tagLib
        h = Handler(self.tagLib) 
        saxparser.setContentHandler(h)

        if not isFile:
            # StringIO.StringIO is supposed to handle unicode
            try:
                fileLikeOpen = StringIO(fileLike)
            except TypeError:
                raise

        else: 
            
            fileLikeOpen = io.open(fileLike, encoding='utf-8')

        # the file always needs to be closed, otherwise
        # subsequent parsing operations produce an unclosed token error
        try:
            saxparser.parse(fileLikeOpen)
        except Exception as e:
            # try a bunch of things to work with UTF-16 files...
            fileLikeOpen.close()
            if not isFile:
                raise e
            with io.open(fileLike, 'rb') as fileBinary:
                fileContentsBinary = fileBinary.read()
                encodingGuess = chardet.detect(fileContentsBinary)['encoding']
            fileLikeOpen2 = io.open(fileLike, encoding=encodingGuess)
            fileContentsUnicode = fileLikeOpen2.read()
            fileLikeOpen2.close()
            fileBytes = fileContentsUnicode.encode(encodingGuess)
            if six.PY3:  # remove BOM
                if fileBytes[0:2] in (b'\xff\xfe', b'\xfe\xff'):
                    fileBytes = fileBytes[2:]                
            else:
                if fileBytes[0:2] in ('\xff\xfe', '\xfe\xff'):
                    fileBytes = fileBytes[2:]                                
            
            fileLikeOpen = BytesIO(fileBytes)
            try:
                saxparser.parse(fileLikeOpen)
            except Exception as e:
# This may be useful for fixing incorrect XML encoding declarations
#                 uTop = u[0:1000]
#                 print(uTop)
#                 if 'encoding=' in uTop:
#                     m = re.search("encoding=[\'\"](.*?)[\'\"]", uTop)
#                     encodingType = m.group(1).lower()
                fileLikeOpen.close()
                raise e
        fileLikeOpen.close()

        #t.stop()
        #environLocal.printDebug(['parsing time:', t])
        if audit:
            ok, msg = self.tagLib.audit() # audit tags
            if not ok:
                raise musicxmlMod.DocumentException(msg)
            else:
                environLocal.printDebug(msg)
        # this is a MusicXML Score object
        self.score = h.getContent()
        if audit:
            self.tagLib.statRun()
            self.tagLib.statClear()


    def read(self, xmlString, audit=False):
        '''Load MusicXML from a string, instead of from a file.
        '''
        self._load(xmlString, False, audit)

    def open(self, fp, audit=False):
        self._load(fp, True, audit)

    #---------------------------------------------------------------------------        
    # convenience routines to get meta-data
    def getBestTitle(self):
        '''title may be stored in more than one place'''
        if self.score.movementTitle is not None:
            title = self.score.movementTitle
        elif self.score.workObj is not None:
            title = self.score.workObj.workTitle
        else:
            title = None
        return title

    #---------------------------------------------------------------------------        
    def repr(self):
        self.reprTest()

    def reprTest(self):
        '''Basic display for testing'''
        bestTitle = self.getBestTitle() or ""
        print(('+'*20 + ' ' + bestTitle))
        print((self.score))
        print()
        print((self.score.toxml(None, None, True)))

    #---------------------------------------------------------------------------
    def write(self, fp):
        msg = self.score.toxml(None, None, True)
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


class TestExternal(unittest.TestCase):
    '''Tests that require acces to external files
    '''
    def runTest(self):
        pass

    def testOpen(self, fp=None):    
        from music21 import corpus
        if fp == None:
            fp = corpus.getWork('trecento/Fava_Dicant_nunc_iudei')
        c = Document()
        c.open(fp, audit=True)
        c.repr()

    def testCompareFile(self, fpIn=None, fpOut=None):
        '''
        input a file and write it back out as xml 
        -- ONLY WORKS ON XML not MXL... make sure file is in that Forman
        '''
        from music21 import corpus
        if fpIn == None: # get Schumann
            fpIn = corpus.getWork('trecento/Fava_Dicant_nunc_iudei')

        if fpOut == None:
            fpOut = environLocal.getTempFile('.xml')

        c = Document()
        c.open(fpIn, audit=True)
        c.write(fpOut)
        environLocal.printDebug([_MOD, 'wrote:', fpOut])


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


    def testTestFiles(self):
        # note: this import path will likel change
        from music21.musicxml import testFiles
        #for score in testFiles.ALL[:1]: # @UndefinedVariable
        for score in testFiles.ALL: # @UndefinedVariable
            a = Document()
            a.read(score)
            
    def testStaffLines(self):
        # note: this import path will likel change
        from music21.musicxml import testFiles
        data = testFiles.ALL[5] # TabFile # @UndefinedVariable
        a = Document()
        a.read(data)
        self.assertEqual(a.score.componentList[0][0].attributesObj.staffDetailsList[0].staffLines, '6')

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

    def testMergeAttributes(self):
        # makes sure that we get a merged attributes obj
        from music21.musicxml import testPrimitive
        d = Document()
        d.read(testPrimitive.multipleAttributesPerMeasures)
        mxMeasure = d.score.componentList[0][0] # first part, first measure
        mxAttributes = mxMeasure.attributesObj
        self.assertEqual(mxAttributes.clefList[0].sign, 'F')
        self.assertEqual(mxAttributes.divisions, '4')

    def testBarlineRepeat(self):
        from music21 import corpus
        fp = corpus.getWork('opus18no1/movement3', fileExtensions=('.xml'))
        d = Document()
        
        # Compressed MXL file instead of regular XML file. Extract XML file.
        import zipfile
        mxl = zipfile.ZipFile(fp, 'r')
        d.open(mxl.extract('movement3.xml'))
        mxl.close()
        
        self.assertEqual(d.score is not None, True)
        
        mxScore = d.score
        mxParts = mxScore.componentList
        p1 = mxParts[0]      
        measures = p1.componentList  
        for m in measures:
            for c in m.componentList:
                if isinstance(c, musicxmlMod.Barline):
                    if c.repeatObj is not None:
                        self.assertEqual('times' in c.repeatObj._attr, True)
                        self.assertEqual(c.repeatObj.get('direction'), 'backward')
                        self.assertEqual(c.repeatObj.get('times'), None)
                        #print c.repeatObj.direction
        unused_s = corpus.parse('opus18no1/movement3', fileExtensions=('.xml'))
        os.remove('movement3.xml')

    def testUnicodeCharsA(self):
        from music21.musicxml import testPrimitive
        from music21 import converter
        from music21.musicxml import m21ToString
        
        # low level musicxml object test
        d = Document()
        d.read(testPrimitive.unicodeStrWithNonAscii)
        # make sure that unicode char is passed through
        match = d.score.identificationObj.creatorList[0].charData
        self.assertEqual(u'© Someone Else', match)
        
        # the ultimate round trip test
        s = converter.parse(testPrimitive.unicodeStrWithNonAscii)
        raw = m21ToString.fromMusic21Object(s)
        s = converter.parse(raw)
        self.assertEqual(u'© Someone Else', s.metadata.composer)

    def testDirectionsA(self):
        from music21.musicxml import testPrimitive
        wedgeCount = 0
        octaveShiftCount = 0
        dashesCount = 0
        bracketCount = 0

        d = Document()
        d.read(testPrimitive.directions31a)
        for m in d.score[0]: # get each raw measure
            for sub in m:
                if isinstance(sub, musicxmlMod.Direction):
                    for dType in sub:
                        for d in dType:
                            if isinstance(d, musicxmlMod.Dashes):
                                dashesCount += 1
                            if isinstance(d, musicxmlMod.OctaveShift):
                                octaveShiftCount += 1
                            if isinstance(d, musicxmlMod.Wedge):
                                wedgeCount += 1
                            if isinstance(d, musicxmlMod.Bracket):
                                bracketCount += 1
        self.assertEqual(dashesCount, 2)
        self.assertEqual(octaveShiftCount, 2)
        self.assertEqual(bracketCount, 2)
        self.assertEqual(wedgeCount, 4)
                        

    def testSpannersA(self):
        from music21.musicxml import testPrimitive
        glissCount = 0
        wavyCount = 0

        d = Document()
        d.read(testPrimitive.spanners33a)
        for m in d.score[0]: # get each raw measure
            for sub in m:
                if isinstance(sub, musicxmlMod.Note):
                    if sub.notationsObj is not None:
                        for n in sub.notationsObj:
                            if isinstance(n, musicxmlMod.Glissando):
                                glissCount += 1
                            if isinstance(n, musicxmlMod.Ornaments):
                                for o in n:
                                    if isinstance(o, musicxmlMod.WavyLine):
                                        wavyCount += 1
        self.assertEqual(glissCount, 2)
        self.assertEqual(wavyCount, 4)

#-------------------------------------------------------------------------------
if __name__ == "__main__":
    # this is a temporary hack to get encoding working right
    # this may not be the best way to do this
    if six.PY2:
        reload(sys) # @UndefinedVariable
        sys.setdefaultencoding("utf-8") # @UndefinedVariable

    import music21
    #music21.converter.parse('/Users/Cuthbert/Dropbox/EMMSAP/MusicXML In/PMFC_05_34-Bon_Bilgrana_de_Valor.xml', forceSource=True)
    music21.mainTest(Test) #, TestExternal)

#------------------------------------------------------------------------------
# eof
