# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         build.py
# Purpose:      music21 documentation builder
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#-------------------------------------------------------------------------------

from __future__ import unicode_literals


import unittest
import os, sys, webbrowser, re
import shutil
import types, inspect
#import codecs

import music21
from music21 import exceptions21

from music21.abc import base as abc
from music21.abc import translate as abcTranslate
#from music21 import abj
from music21.abj import translate as abjTranslate

from music21.analysis import correlate as analysisCorrelate
from music21.analysis import discrete as analysisDiscrete
from music21.analysis import metrical as analysisMetrical
from music21.analysis import patel as analysisPatel
from music21.analysis import reduction as analysisReduction
from music21.analysis import search as analysisSearch
from music21.analysis import windowed as analysisWindowed

from music21 import articulations

from music21.audioSearch import base as audioSearch
from music21.audioSearch import recording as audioSearchRecording
from music21.audioSearch import transcriber as audioSearchTranscriber

from music21 import bar
from music21 import base
from music21 import beam

from music21.braille import basic as brailleBasic
from music21.braille import examples as brailleExamples
from music21.braille import segment as brailleSegment
from music21.braille import text as brailleText
from music21.braille import translate as brailleTranslate

#chant
from music21 import chord
#chordTables
#classCache
from music21 import clef
from music21 import common

#from music21 import composition
from music21.composition import phasing as compositionPhasing

from music21 import contour
from music21 import converter

from music21.corpus import base as corpus
from music21.corpus import chorales as corpusChorales

from music21.counterpoint import species as counterpointSpecies

# demos
# defaults
# derivation
# doc folder
from music21 import duration
from music21 import dynamics
from music21 import editorial
from music21 import environment
from music21 import expressions
# ext folder

from music21.features import base as features
from music21.features import jSymbolic as featuresJSymbolic
from music21.features import native as featuresNative

from music21.figuredBass import checker as figuredBassChecker
from music21.figuredBass import examples as figuredBassExamples
from music21.figuredBass import fbPitch as figuredBassFbPitch
from music21.figuredBass import notation as figuredBassNotation
from music21.figuredBass import possibility as figuredBassPossibility
from music21.figuredBass import realizer as figuredBassRealizer
from music21.figuredBass import realizerScale as figuredBassRealizerScale
from music21.figuredBass import resolution as figuredBassResolution
from music21.figuredBass import rules as figuredBassRules
from music21.figuredBass import segment as figuredBassSegment

from music21 import graph

from music21 import harmony

from music21 import humdrum
from music21.humdrum import spineParser as humdrumSpineParser

from music21 import instrument
from music21 import interval
from music21 import intervalNetwork

from music21 import key

from music21 import layout
from music21.lily import lilyObjects as lilyLilyObjects
from music21.lily import translate as lilyTranslate

from music21 import medren
from music21 import metadata
from music21 import meter

from music21.midi import base as midi
from music21.midi import realtime as midiRealtime
from music21.midi import translate as midiTranslate

from music21.musedata import base as musedata
from music21.musedata import translate as musedataTranslate
from music21.musedata import base40 as musedataBase40

from music21.musicxml import base as musicxmlBase
from music21.musicxml import m21ToString as musicxmlM21ToString
from music21.musicxml import fromMxObjects as musicxmlFromMxObjects
from music21.musicxml import toMxObjects as musicxmlToMxObjects

from music21 import note

#no docs
#from music21.noteworthy import base as noteworthyBase
from music21.noteworthy import translate as noteworthyTranslate

from music21.romanText import base as romanText
from music21.romanText import clercqTemperley as romanTextClercqTemperley
from music21.romanText import translate as romanTextTranslate

from music21 import pitch
from music21 import roman
from music21 import repeat

from music21.scala import base as scala

from music21 import scale
from music21 import search
from music21 import serial
from music21 import sieve
from music21 import spanner
from music21 import stream

from music21 import tempo

from music21.test import test
from music21.test import multiprocessTest as testMultiprocessTest

from music21 import text

from music21.theoryAnalysis import theoryAnalyzer as theoryAnalysisTheoryAnalyzer

from music21 import tie
from music21 import tinyNotation

from music21.trecento import cadencebook as trecentoCadencebook
from music21.trecento import polyphonicSnippet as trecentoPolyphonicSnippet
from music21.trecento import tonality as trecentoTonality

from music21 import variant

from music21.vexflow import base as vexflow
from music21 import voiceLeading
from music21 import volume

from music21.webapps import base as webapps
#from music21.webapps import music21wsgiapp as webappsMusic21WsgiApp
from music21 import xmlnode


#from music21 import environment #redundant
_MOD = "doc.build.py"
environLocal = environment.Environment(_MOD)


MOCK_RE = re.compile('') # for testing against instance


INDENT = ' '*4
OMIT_STR = 'OMIT_FROM_DOCS'
HIDE_LINE_STR = '#_DOCS_HIDE'
SHOW_LINE_STR = '#_DOCS_SHOW'
# used in rst doc-tests to avoid calling .show(), etc; remove comment
DOC_TEST_SKIP = '# doctest: +SKIP'

FORMATS = ['html', 'latex', 'pdf']

# this is added to generated files
WARN_EDIT = '.. WARNING: DO NOT EDIT THIS FILE: AUTOMATICALLY GENERATED. Edit the .py file directly\n\n'

# string for no documentation
NO_DOC = 'No documentation.'

# In order of ORIGINAL names
MODULES = [
    abc,
    abcTranslate,
    
    abjTranslate,

    # analysis.
    analysisCorrelate,
    analysisDiscrete,
    analysisMetrical,
    analysisPatel,
    analysisReduction,
    analysisSearch,
    analysisWindowed,
    
    articulations,

    audioSearch,
    audioSearchRecording,
    audioSearchTranscriber,
    
    bar,
    base,
    beam,
    
    brailleBasic,
    brailleExamples,
    brailleSegment,
    brailleText,
    brailleTranslate,

    chord, 
    clef, 
    common,
    #composition
    compositionPhasing,

    contour,
    converter,
    
    corpus, 
    corpusChorales,

    counterpointSpecies,

    duration, 
    dynamics,

    editorial,
    environment, 
    expressions,
    
    features,
    featuresJSymbolic,
    featuresNative,
    
    figuredBassChecker,
    figuredBassExamples,
    figuredBassFbPitch,
    figuredBassNotation,
    figuredBassPossibility,
    figuredBassRealizer,
    figuredBassRealizerScale,
    figuredBassResolution,
    figuredBassRules,
    figuredBassSegment,
    
    graph,
    
    harmony,

    humdrum,
    humdrumSpineParser,
    
    instrument,
    interval, 
    intervalNetwork,
    
    key,

    layout,

    lilyLilyObjects,
    lilyTranslate,

    medren,
    metadata,
    meter, 
    
    midi,
    midiRealtime,
    midiTranslate,
    
    musedata,
    musedataTranslate,
    musedataBase40,
    
    musicxmlBase,
    musicxmlM21ToString,
    musicxmlFromMxObjects,
    musicxmlToMxObjects,

    note, 
    
#    noteworthyBase,
    noteworthyTranslate,

    pitch,

    repeat,
    roman, 

    romanText,
    romanTextTranslate,
    romanTextClercqTemperley,

    scala,

    scale,     
    search,
    serial,     
    sieve,   
    spanner,
    stream,     
  
    tempo, 
    
    test,
    testMultiprocessTest,
        
    text,
    
    theoryAnalysisTheoryAnalyzer,
    
    tie,
    tinyNotation,
    # trecento
    trecentoCadencebook,
    trecentoPolyphonicSnippet,
    trecentoTonality,

    variant,
    vexflow,
    voiceLeading,
    volume,

    webapps,
#    webappsMusic21WsgiApp,
    
    xmlnode, 
    
]



# sphinx notes:

# cross references:
# http://sphinx.pocoo.org/markup/inline.html?highlight=method




#-------------------------------------------------------------------------------
class PartitionedName(object):  
    '''Object to store and manage names (functions, methods, attributes, properties) within a name space. 
    '''
    def __init__(self, srcNameEval=None):

        self.srcNameEval = srcNameEval
        self.names = []

        try:
            self.srcObj = self.srcNameEval()
        except TypeError:
            self.srcObj = None
        


    def getElement(self, partName):
        return None

    def getSignature(self, partName):
        '''Get the signatures (the calling arguments) for a method or property

        >>> from music21 import pitch, meter, duration
        
        `pitch.Pitch().midi` is a property so it returns u''
        
        >>> a = PartitionedClass(pitch.Pitch)
        >>> a.getSignature('midi')
        u''

        `meter.MeterSequence.load()` takes a required argument and has three default arguments.

        >>> a = PartitionedClass(meter.MeterSequence)
        >>> a.getSignature('load')
        u'(value, partitionRequest=None, autoWeight=False, targetWeight=None)'


        `duration.Duration()` can take \*arguments or \*\*keywords.

        >>> a = PartitionedClass(duration.Duration)
        >>> a.getSignature('__init__')
        u'(*arguments, **keywords)'


        '''
        element = self.getElement(partName)
        if element.kind in ['method', 'function']:
            try:
                data = inspect.getargspec(element.object)
            except TypeError:
                environLocal.printDebug(['cannot get signature from element', element])
                return ''
            #data = inspect.formatargspec()
            argStr = []
            # defaults is an ordered list in same order as args
            # varargs and keywords are the names of * and ** args respectively
            args, varargs, keywords, defaults = data 
            # get index offset to when defaults start
            if defaults != None:
                offset = len(args) - len(defaults)
            else:
                offset = 0

            # iterate through defined args
            for p in range(len(args)): # these are required, include self
                arg = args[p]
                if arg == 'self': continue
                
                if defaults != None and p >= offset:
                    default = defaults[p-offset]
                    if isinstance(default, basestring):
                        argStr.append('%s=\'%s\'' % (arg, default))
                    else:
                        argStr.append('%s=%s' % (arg, default))
                else:
                    argStr.append('%s' % (arg))
            # add position/keyword args 
            if varargs != None:
                argStr.append('*%s' % varargs)
            if keywords != None:
                argStr.append('**%s' % keywords)

            msg = '(%s)' % ', '.join(argStr)

        elif element.kind == 'property':
            msg = ''
        elif element.kind == 'data':
            msg = ''
        return msg


#-------------------------------------------------------------------------------
class PartitionedModule(PartitionedName):
    '''Given a module name, manage and present data.
    '''
    def __init__(self, srcNameEval):
        PartitionedName.__init__(self, srcNameEval)
        self.srcNameStr = self.srcNameEval.__name__
        self.namesOrdered = [] # any defined order for names
        if hasattr(self.srcNameEval, '_DOC_ORDER'):
            # these are evaluated class names, not strings
            for orderedObj in self.srcNameEval._DOC_ORDER:
                if hasattr(orderedObj, 'func_name'):
                    orderedName = orderedObj.func_name  
                elif hasattr(orderedObj, '__name__'):
                    orderedName = orderedObj.__name__ 
                else: #assume class-level method
                    orderedName = orderedObj
                    #environLocal.printDebug(['cannot get a string name of object:', orderedObj])
                    #continue
                
                self.namesOrdered.append(orderedName)

        else:
            environLocal.printDebug('module %s missing _DOC_ORDER' % 
                                    self.srcNameStr)
        self.names = dir(self.srcNameEval)
        self._data = self._fillData()
        self._sort()

    def _fillData(self):
        '''
        >>> from music21 import pitch
        >>> a = PartitionedModule(pitch)
        >>> len(a.names) == len(a._data)
        True
        >>> a.namesOrdered
        ['Pitch', 'Accidental']
        >>> a.names[0]
        'Pitch'
        >>> a.names[0] == a._data[0].name
        True
        '''
        post = []

        for name in self.names:
            objName = '%s.%s' % (self.srcNameStr, name)
            obj = eval(objName)

            # skip for now
            homecls = self.srcNameEval
            if hasattr(obj, '__module__'):
                if self.srcNameStr not in obj.__module__:
                    homecls = obj.__module__

            # get kind
            if isinstance(obj, types.ModuleType):
                kind = 'module'
            elif (isinstance(obj, types.StringTypes) or 
                isinstance(obj, types.DictionaryType) or 
                isinstance(obj, types.ListType) or 
                common.isNum(obj) or common.isListLike(obj) or 
                isinstance(obj, type(MOCK_RE))): 
                kind = 'data'

            elif isinstance(obj, types.FunctionType):
                kind = 'function'
            elif isinstance(obj, types.TypeType):
                kind = 'class'
            elif isinstance(obj, environment.Environment):
                kind = 'data' # skip environment object
            else:
                environLocal.printDebug(['cannot process module level name: %s' % self.srcNameStr])
                kind = None

            post.append(inspect.Attribute(name, kind, homecls, obj))

        return post


    def _sort(self):
        namesSupply = self.names[:]
        names = []
        _data = []

        for name in self.namesOrdered:
            if name not in namesSupply:
                environLocal.warn('module %s does not have name %s' % (self.srcNameStr, name))
                continue
            junk = namesSupply.pop(namesSupply.index(name))
    
            i = self.names.index(name)
            names.append(self.names[i])
            _data.append(self._data[i])

        # get all others that are not defined
        for name in namesSupply:
            i = self.names.index(name)
            names.append(self.names[i])
            _data.append(self._data[i])

        self.names = names
        self._data = _data


    def getElement(self, partName):
        '''
        '''
        if partName not in self.names:
            raise Exception('cannot find %s name in %s' % (partName,    
                                     self.srcNameEval))
        return self._data[self.names.index(partName)]


    def getNames(self, nameKind, public=True, local=True):
        '''Local determines if the name is from this module or imported.

        >>> from music21 import pitch
        >>> a = PartitionedModule(pitch)
        >>> a.getNames('classes')
        ['Pitch', 'Accidental', 'Microtone']
        >>> a.getNames('functions')    
        ['convertCentsToAlterAndCents', 'convertFqToPs', 'convertHarmonicToCents', 'convertNameToPitchClass', 'convertNameToPs', 'convertPitchClassToNumber', 'convertPitchClassToStr', 'convertPsToFq', 'convertPsToOct', 'convertPsToStep', 'convertStepToPs']
        '''
        post = []
        if nameKind.lower() in ['classes', 'class']:
            nameKind = 'class'
        elif nameKind.lower() in ['modules', 'imports', 'module']:
            nameKind = 'module'
        elif nameKind.lower() in ['functions', 'function']:
            nameKind = 'function'
        elif nameKind.lower() in ['data', 'attributes', 'attribute']:
            nameKind = 'data'

        for name in self.names:
            element = self.getElement(name)
            if local:
                # this is really defining module
                if element.defining_class != self.srcNameEval:
                    continue
            if public:
                if name.startswith('__'): # ignore private variables
                    continue
                if name.startswith('_'): # ignore private variables
                    continue
                elif 'Test' in name: # ignore test classes
                    continue
                elif 'Exception' in name: # ignore exceptions
                    continue
            if not element.kind == nameKind:
                continue
            post.append(name)
        return post

    def getDoc(self, partName):
        element = self.getElement(partName)
        if element.kind in ['class', 'function']:
            return element.object.__doc__


#-------------------------------------------------------------------------------
class PartitionedClass(PartitionedName):
    '''
    Given an evaluated class name as an argument, manage and present
    All data for all attributes, methods, and properties.


    Note that this only gets data attributes that are defined outside
    of the __init__ definition of the Class. 
    '''
    def __init__(self, srcNameEval):
        '''
        >>> from music21 import pitch
        >>> a = PartitionedClass(pitch.Pitch)
        >>> len(a.names) > 30
        True
        >>> a.mro
        (<class 'music21.pitch.Pitch'>, <class 'music21.base.Music21Object'>, <class 'music21.base.JSONSerializer'>, <type 'object'>)

        '''
        PartitionedName.__init__(self, srcNameEval)

        self.mro = inspect.getmro(self.srcNameEval)
        self.mroLive = self._createMroLive()

        # store both a list of names as well as name/mro index pairs
        self.names = []
        self.namesMroIndex = []

        # this is not a complete list of names
        self.namesOrdered = [] # any defined order for names
        if hasattr(self.srcNameEval, '_DOC_ORDER'):
            self.namesOrdered += self.srcNameEval._DOC_ORDER

        # this will get much but not all data
        self._dataClassify = inspect.classify_class_attrs(self.srcNameEval)
        for element in self._dataClassify:
            # get mro index number
            self.names.append(element.name)
            mroIndexMatch = self.mro.index(element.defining_class)
            self.namesMroIndex.append((element.name, mroIndexMatch))

        # add dataLive after processing names from classify
        # this assures that names are not duplicated
        self._dataLive = self._fillDataLive()
        for element in self._dataLive:
            # get mro index number
            self.names.append(element.name)
            mroIndexMatch = self.mro.index(element.defining_class)            
            self.namesMroIndex.append((element.name, mroIndexMatch))

        # create a combined data storage
        # this will match the order in names, and namesMroIndex
        self._data = self._dataClassify + self._dataLive
        self._sort()

    def _sort(self):
        '''
        Sort _data, self.namesMroIndex, and self.names by placing anything 
        defined in self.srcNameEval first.
        '''
        namesSupply = self.names[:]

        names = []
        namesMroIndex = []
        _data = []

        # always put first
        for forceName in ['__init__']:
            if forceName in namesSupply:
                junk = namesSupply.pop(namesSupply.index(forceName))
                i = self.names.index(forceName)
                names.append(self.names[i])
                namesMroIndex.append(self.namesMroIndex[i])
                _data.append(self._data[i])

        for name in self.namesOrdered:
            if name in forceName:
                continue # already supplied
            # cannot be sure this is the same index as that in self.names
            junk = namesSupply.pop(namesSupply.index(name))

            i = self.names.index(name)
            names.append(self.names[i])
            namesMroIndex.append(self.namesMroIndex[i])
            _data.append(self._data[i])

        # get all others that are not defined
        for name in namesSupply:
            i = self.names.index(name)
            names.append(self.names[i])
            namesMroIndex.append(self.namesMroIndex[i])
            _data.append(self._data[i])

        self.names = names
        self.namesMroIndex = namesMroIndex
        self._data = _data


    def _createMroLive(self):
        '''
        Try to create the mro order but with live objects.


        >>> from music21 import pitch
        >>> a = PartitionedClass(pitch.Pitch)
        >>> len(a._createMroLive())
        4
        >>> print a._createMroLive()
        [C, <music21.base.Music21Object object at 0x...>, <music21.base.JSONSerializer object at 0x...>, <object object at 0x...>]
        '''
        post = []
        for entry in self.mro:
            try:
                obj = entry()
            except TypeError:
                obj = None
            post.append(obj)
        return post

    def _fillDataLive(self):
        post = []
        # we cannot get this data if the object cannot be instantiated
        if self.srcObj is None: 
            return post
        # dir(self.srcObj) will get all names
        # want only writable attributes: 
        for name in self.srcObj.__dict__.keys():
            if name in self.names:
                continue # already have all the info we need
            # using an attribute class to match the form given by 
            # inspect.classify_class_attrs
            obj = self.srcObj.__dict__[name]
            kind = 'data' # always from __dict__, it seems
            # go through live mroLive objects and try to find
            # this attribute
            mroIndices = self.mroIndices()
            mroIndices.reverse()
            homecls = None
            for mroIndex in mroIndices:
                if (hasattr(self.mroLive[mroIndex], '__dict__') and 
                    name in self.mroLive[mroIndex].__dict__.keys()):
                    # if found, set class name to heomcls
                    homecls = self.mro[mroIndex]
                    break
            if homecls == None:
                homecls = self.srcNameEval

            post.append(inspect.Attribute(name, kind, homecls, obj))
        return post

    def findMroIndex(self, partName):
        '''
        Given an partName, find from where (in the list of methods) 
        the part is derived. Returns an index number value.


        >>> from music21 import pitch
        >>> a = PartitionedClass(pitch.Pitch)
        >>> a.findMroIndex('midi')
        0
        >>> a.findMroIndex('id')
        1
        '''        
        i = self.names.index(partName)
        unused_name, mroIndex = self.namesMroIndex[i]
        return mroIndex

    def mroIndices(self):
        '''
        returns a list in the range of the length of self.mro
        '''
        return range(len(self.mro))

    def lastMroIndex(self):
        '''
        >>> from music21 import pitch
        >>> a = PartitionedClass(pitch.Pitch)
        >>> a.lastMroIndex()
        3
        '''
        return len(self.mro)-1

    def getElement(self, partName):
        '''
        >>> from music21 import pitch
        >>> a = PartitionedClass(pitch.Pitch)
        >>> a.getElement('midi')
        Attribute(name='midi', kind='property', defining_class=<class 'music21.pitch.Pitch'>, object=<property object...>)
        >>> a.getElement('id')
        Attribute(name='id', kind='data', defining_class=<class 'music21.base.Music21Object'>, object=None)
        >>> a.getElement('_getDiatonicNoteNum')
        Attribute(name='_getDiatonicNoteNum', kind='method', defining_class=<class 'music21.pitch.Pitch'>, object=<function...>)

        '''
        if partName not in self.names:
            raise Exception('cannot find %s name in %s' % (partName,    
                                     self.srcNameEval))
        return self._data[self.names.index(partName)]


    def getDefiningClass(self, partName):
        element = self.getElement(partName)
        return element.defining_class

    def getClassFromMroIndex(self, mroIndex):
        return self.mro[mroIndex]


    def getDoc(self, partName):
        r'''
        Get the documentation for
        an attribute or method and
        return it as a literal string.
        
        
        >>> from music21 import pitch
        >>> a = PartitionedClass(pitch.Pitch)
        >>> a.getDoc('__init__')[:15]
        'Create a Pitch.'


        >>> from music21 import editorial
        >>> b = PartitionedClass(editorial.Comment)
        >>> b.getDoc('__init__')
        u'No documentation.'


        >>> from music21.humdrum import spineParser
        >>> c = PartitionedClass(spineParser.SpineCollection)
        >>> c.getDoc('addSpine')
        '\n        creates a new spine in the collection and returns it.\n        \n        \n        By default, the underlying music21 class of the spine is\n        :class:`~music21.stream.Part`.  This can be...'

        '''
        element = self.getElement(partName)

        if hasattr(self.srcNameEval, '_DOC_ATTR'):
            docAttr = self.srcNameEval._DOC_ATTR
        else:
            docAttr = {}

        match = None
                
        if partName in docAttr.keys():
            match = docAttr[partName]
        # if its an undocumented public attribute and basic python
        # data structure, we do not want to show that documentation
        elif (element.kind in ['data'] and (
            common.isStr(element.object) or 
            common.isListLike(element.object) or
            common.isNum(element.object)
            )):
            pass
        else:
            try:
                match = element.object.__doc__
            except AttributeError:
                match = None

        # the object object returns by default 
        # x.__init__(...) initializes x; see x.__class__.__doc__ for signature
        # this should be returned as Documentation
        ifInitializes = False
        if not match is None:
            try:
                ifInitializes = match.startswith('x.__init__(...) initializes x')
            except UnicodeDecodeError: # this happens with some docs
                environLocal.pd(['cannot decode doc string, getting UnicodeDecodeError', partName])
                return NO_DOC

        if match is None or ifInitializes:
            return NO_DOC
        # default for a dictionary
        elif match.startswith('dict() -> new empty dictionary'):
            return NO_DOC
        else:
            return match

    def hasDoc(self, partName):
        post = self.getDoc(partName)
        if post == NO_DOC:
            return False
        else:
            return True


    def getNames(self, nameKind, mroIndex=None, public=True, getInit=True,
                getRe=False):
        '''Name type can be method, data, property

        >>> from music21 import pitch
        >>> a = PartitionedClass(pitch.Pitch)

        >>> len(a.getNames('property')) > 10
        True

        >>> len(a.getNames('method')) > 7
        True

        >>> a.getNames('method', mroIndex=0)
        ['__init__', 'convertMicrotonesToQuarterTones', 'convertQuarterTonesToMicrotones', 'getAllCommonEnharmonics', 'getCentShiftFromMidi', 'getEnharmonic', 'getHarmonic', 'getHarmonicChord', 'getHigherEnharmonic', 'getLowerEnharmonic', 'getMidiPreCentShift', 'harmonicAndFundamentalFromPitch', 'harmonicAndFundamentalStringFromPitch', 'harmonicFromFundamental', 'harmonicString', 'inheritDisplay', 'isEnharmonic', 'isTwelveTone', 'lilyNoOctave', 'setAccidentalDisplay', 'simplifyEnharmonic', 'transpose', 'transposeAboveTarget', 'transposeBelowTarget', 'updateAccidentalDisplay']
        >>> a.getNames('data', mroIndex=0)
        ['fundamental', 'implicitAccidental', 'defaultOctave']
        >>> a.getNames('data', mroIndex=1)
        ['classSortOrder', 'hideObjectOnPrint', 'id', 'isSpanner', 'isStream', 'groups']
        >>> a.getNames('data', mroIndex=a.lastMroIndex())
        []

        >>> from music21 import converter
        >>> a = PartitionedClass(converter.Converter)
        >>> a.getNames('methods')
        ['__init__', 'parseData', 'parseFile', 'parseURL']

        >>> from music21 import meter
        >>> a = PartitionedClass(meter.TimeSignature)
        >>> len(a.getNames('methods')) > 10
        True
        >>> a.getNames('attributes', 1)
        ['hideObjectOnPrint', 'id', 'isSpanner', 'isStream', 'groups']

        >>> from music21 import serial
        >>> a = PartitionedClass(serial.RowSchoenbergOp23No5)
        >>> a.getNames('attributes', 0)
        ['composer', 'opus', 'row', 'title']
        >>> a.getNames('data', 1) # returns empty b/c defined here
        []
        >>> a.mroLive[1]
        <music21.serial.HistoricalTwelveToneRow...>

        '''
        post = []
        if nameKind.lower() in ['properties', 'property']:
            nameKind = 'property'
        elif nameKind.lower() in ['methods', 'method']:
            nameKind = 'method'
        elif nameKind.lower() in ['data', 'attributes', 'attribute']:
            nameKind = 'data' # both doc and no doc
        elif nameKind.lower() in ['attributes-nodoc']:
            nameKind = 'data-nodoc'
        elif nameKind.lower() in ['attributes-doc']:
            nameKind = 'data-doc'

        for name in self.names:
            element = self.getElement(name)
            if public:
                # special handling for init methods
                if name == '__init__':
                    if not getInit:
                        continue
                elif name.startswith('__') or name.startswith('_'): 
                    continue

            if isinstance(element.object, type(MOCK_RE)):
                if not getRe:
                    continue

            #environLocal.printDebug(['kinds', name, element.kind])

            # filter out groups defined for doc/doc
            if element.kind == 'data' and nameKind.startswith('data-'): #either nodoc or doc
                if nameKind == 'data-doc':
                    if not self.hasDoc(name): # has documentation
                        continue
                elif nameKind == 'data-nodoc':
                    if self.hasDoc(name): # has documentation
                        continue
            elif not element.kind == nameKind: # if this is not the right kind
                continue

            if mroIndex != None: # select by mro
                #environLocal.printDebug(['mroindex', self.findMroIndex(name)])
                if mroIndex == self.findMroIndex(name):
                    post.append(name)
            else:
                post.append(name)
        return post



#-------------------------------------------------------------------------------
class RestructuredWriter(object):

    def __init__(self):
        pass

    def _heading(self, line, headingChar='=', indent=0):
        '''Format an RST heading. Indent is in number of spaces.
        '''
        indent = ' ' * indent
        #environLocal.printDebug(['got indent', indent])
        msg = []
        msg.append(indent + line)
        msg.append(indent + '\n')
        msg.append(indent + headingChar*len(line))
        msg.append(indent + '\n'*2)
        return msg

    def _para(self, doc):
        '''Format an RST paragraph.
        '''
        if doc == None:
            return []
        doc = doc.strip()
        msg = []
        msg.append('\n'*2)
        msg.append(doc)
        msg.append('\n'*2)
        return msg

    def _list(self, elementList, indent=''):
        '''Format an RST list.
        '''
        msg = []
        for item in elementList:
            item = item.strip()
            msg.append('%s+ ' % indent)
            msg.append(item)
            msg.append('\n'*1)
        msg.append('\n'*1)
        return msg

    def formatParent(self, mroEntry):
        '''Return a class name as a parent, showing module when necessary

        >>> from music21 import note
        >>> rw = RestructuredWriter()
        >>> post = rw.formatParent(inspect.getmro(note.Note)[1])
        >>> 'note.NotRest' in post      
        True
        >>> post = rw.formatParent(inspect.getmro(note.Note)[4])
        >>> 'object' in post      
        False
        '''
        modName = mroEntry.__module__
        className = mroEntry.__name__
        if modName == '__builtin__':
            return className
        else:
            return ':class:`~%s.%s`' % (modName, className)

    def formatXRef(self, partName, group, mroEntry):
        '''Given the name and a containing object, get a cross references
        '''
        modName = mroEntry.__module__
        className = mroEntry.__name__
        if group in ['attributes', 'properties', 'attributes-nodoc']:
            return ':attr:`~%s.%s.%s`' % (modName, className, partName)            
        elif group in ['methods']:
            return ':meth:`~%s.%s.%s`' % (modName, className, partName)

    def formatClassInheritance(self, mro):
        '''Given a list of classes from inspect.getmro, return a formatted
        String

        >>> from music21 import note
        >>> rw = RestructuredWriter()
        >>> post = rw.formatClassInheritance(inspect.getmro(note.Note))
        >>> 'note.GeneralNote' in post
        True
        >>> 'base.Music21Object' in post
        True
        '''
        msg = []
        msg.append('Inherits from:')
        sub = []
        for i in range(len(mro)):
            if i == 0: continue # first is always the class itself
            if i == len(mro) - 1: continue # last is object
            sub.append(self.formatParent(mro[i]))
        if len(sub) == 0:
            return ''

        msg.append(', '.join(sub))
        #msg.append(unichr(8594).join(sub))
        return u' '.join(msg)


    def formatDocString(self, doc, indent='', modName=None):
        r'''
        Given a docstring, clean it up for RST presentation.


        Note: can use inspect.getdoc() or inspect.cleandoc(); though
        we need customized approach demonstrated here.


        >>> rsw = RestructuredWriter()
        >>> rsw.formatDocString("hello #_DOCS_HIDE\n" +\
        ...                     "#_DOCS_SHOW there\n" +\
        ...                     "user!")
        u' there\nuser!\n\n'

        '''

        # TODO: need to remove lines as follow:
        # # doctest: +SKIP
        # <BLANKLINE>

        if doc == None:
            return ''
        else:
            # convert to unicode utf-8
            doc = common.toUnicode(doc)
            #return '%sNo documentation.\n' % indent
        # define the start of lines that should not be changed
        rstExclude = ['.. image::', ':width:']

        docTestImportPackage = '>>> from music21 import *'
        docTestImportPackageReplace = """>>> from music21 import *"""

        lines = doc.split('\n')
        baselineStrip = self.getBaselineStrip(lines)
        lenBaselineStrip = len(baselineStrip)

        sub = []
        for lineSrc in lines:
            line = lineSrc.rstrip()
            if line.startswith(baselineStrip):
                line = line[lenBaselineStrip:]

            if OMIT_STR in line: # permit blocking doctest examples
                break # do not gather any more lines
            elif HIDE_LINE_STR in line: # do not show in docs
                continue
            elif SHOW_LINE_STR in line: # do not show in docs
                lineNew = line.replace(' ' + SHOW_LINE_STR + ' ', ' ')
                if lineNew == line:
                    line = line.replace(SHOW_LINE_STR, ' ')
                else:
                    line = lineNew
            elif DOC_TEST_SKIP in line: # do not show in docs
                line = line.replace(DOC_TEST_SKIP, ' ')

            match = False
            for stub in rstExclude:
                if line.startswith(stub):
                    #environLocal.printDebug(['found rst in doc string:', repr(lineSrc)])

                    # was only rstripping and 
                    # prepending return carriages to keep indentation
                    # now, indentation is added below

                    if stub == '.. image::':
                        lineSrc = lineSrc.strip()
                        sub.append(lineSrc) # do not strip
                    elif stub == ':width:': # immediate follows
                        lineSrc = lineSrc.strip()
                        sub.append(lineSrc) # do not strip
                    else:
                        raise Exception('unexpected condition! %s' % sub)
                        #sub.append('\n' + lineSrc) # do not strip
                    match = True
                    break
            # else, add a stripped line
            if not match:
                sub.append(line)
#                sub.append(lineSrc + '\n')

        # find double breaks in text
        post = []
        for i in range(len(sub)):
            line = sub[i]
            if line == '': #and i != 0 and sub[i-1] == '':
                post.append(None) # will be replaced with line breaks
            #elif line == '':
            #    pass
            else: 
                post.append(line)

        # create final message; add proper line breaks and indentation
        msg = [] # can add indent here
        inExamples = False # are we now in a code example?
        lookForTwoConsecutiveNewlines = False # have we found two newlines in a row, canceling inExamples
        addWordJoinerToPreviousLine = False
        for line in post:
            if line == None: # insert breaks from two spaces
                addWordJoinerToPreviousLine = False
                if inExamples == False or lookForTwoConsecutiveNewlines == True:
                    inExamples = False
                    lookForTwoConsecutiveNewlines = False
                    msg.append('\n') # can add indent here
                else:
                    lookForTwoConsecutiveNewlines = True
                    if inExamples == True:
                        addWordJoinerToPreviousLine = True
                    msg.append('\n') # can add indent here
#                    else: # in examples, allow for a line break that doesn't exit the text...en quad space
#                        msg.append(indent + u'\u2060 \n') # can add indent here
            elif line.startswith('>>>'): # python examples
                if addWordJoinerToPreviousLine == True:
                    msg[-1] = indent + u'\u2060 \n'
                    addWordJoinerToPreviousLine = False
                if inExamples == False:
                    space = '\n\n'
                    # if import is the module import, replace with package
                    if line.startswith(docTestImportPackage):
                        # can try to mark up import here
                        msg.append(space + indent + docTestImportPackageReplace + '\n')
                    else: # if no import is given, assume we need a mod import
                        # need only one return after first line
                        msg.append(space + indent + line + '\n')
                    inExamples = True
                else:
                    msg.append(indent + line + '\n')
            # images should be at the same indent level
            elif line.strip().startswith('.. image::'):
                # additional \n are necessary here; were added previously
                # above; indent is important here: if incorrect, the docutils
                # interprets as the end of the docs
                msg.append('\n\n\n' + indent + line + '\n')
                addWordJoinerToPreviousLine = False
                inExamples = False
            elif line.strip().startswith(':width:'):
                # width must be indented in an additional line
                msg.append(indent + '    ' + line + '\n\n')
                addWordJoinerToPreviousLine = False
                inExamples = False

            else: # continuing an existing line
                addWordJoinerToPreviousLine = False
                msg.append(indent + line + '\n')
        msg.append('\n')

        return ''.join(msg)

    def getBaselineStrip(self, lines):
        r'''
        returns a string of the number of spaces to remove from
        a docstring, which is the baseline of the number of indented
        characters at the beginning of a line.
        
        
        The baseline strip is the number of spaces before the first
        line of text, or if it is zero, the number of spaces after
        the second line of text.  This way both common ways of writing
        multiline docstrings is permitted.
        
        
        >>> rsw = RestructuredWriter()
        >>> lines = ['this is a doc', '    this is also a doc']
        >>> rsw.getBaselineStrip(lines)
        u'    '
        >>> lines = ['','        this docstring begins w/ 8 spaces', '              third is more indented']
        >>> rsw.getBaselineStrip(lines)
        u'        '
        >>> lines = ['this doc starts right away','','','  and after two blank lines gets going...']
        >>> rsw.getBaselineStrip(lines)
        u'  '

        '''
        lengthStrip = 0
        if len(lines) == 0:
            return ''
        elif len(lines) == 1:
            stripL0 = lines[0].lstrip()
            lengthStrip = len(lines[0]) - len(stripL0)
        else:
            stripL0 = lines[0].lstrip()
            if len(stripL0) > 0 and (len(lines[0]) - len(stripL0)) > 0:
                lengthStrip = len(lines[0]) - len(stripL0)
            if lengthStrip == 0:
                for i in range(1, len(lines)):
                    l = lines[i]
                    if l.strip() == "":
                        continue
                    stripL = l.lstrip()
                    lengthStrip = len(l) - len(stripL)
                    break
        returnLine = u''
        for i in range(lengthStrip):
            returnLine += u' '
        return returnLine


#-------------------------------------------------------------------------------
class CorpusDoc(RestructuredWriter):
    '''Provide a complete listing of works in the corpus
    '''
    def __init__(self):
        RestructuredWriter.__init__(self)
        self.fileName = 'referenceCorpus.rst'
        self.fileRef = 'referenceCorpus'

    def getRestructured(self):
        msg = []

        msg.append('.. _%s:\n\n' % self.fileRef)
        msg += self._heading('List of Works Found in the music21 Corpus' , '=')
        msg.append(WARN_EDIT)

        msg += self._para('''The following list shows all files available in the music21 corpus and available through the virtual corpus. To load a work from the corpus, provide the file path stub provided. For example::

        >>> from music21 import corpus
        >>> s = corpus.parse('bach/bwv108.6.xml')
        ''')

        refList = corpus.getWorkReferences(sort=True)
        for composerDict in refList:
            #work, title, composer, paths in []:
            msg += self._heading(composerDict['composer'], '-')
            #msg += self._heading(composerDict['composer'], '-')

            msg += self._para('''To get all works by %s, the :meth:`~music21.corpus.base.getComposer` function can be used to get all file paths. For example::

            >>> from music21 import corpus
            >>> paths = corpus.getComposer('%s')

            ''' % (composerDict['composer'], composerDict['composerDir']))

            for workKey in composerDict['sortedWorkKeys']:
                workDict = composerDict['works'][workKey]
                #msg += self._heading(workDict['title'], '~')

                strTitle = common.toUnicode(workDict['title'])
                if not workDict['virtual']: # if not virtual
                    msg += self._para(strTitle)
                else: # mark virtual sources
                    msg += self._para(strTitle + ' (*virtual*)')

                msg.append('\n'*1)

                if not workDict['virtual']: # if not virtual
                    fileList = []
                    for d in workDict['files']:
                        corpusPathNoSlash = d['corpusPath']
                        corpusPathNoSlash = re.sub('\\\\', '/', corpusPathNoSlash)
                        fileList.append('%s *(%s)*: `%s`' % (d['title'], 
                            d['format'], corpusPathNoSlash))
                else:
                    for d in workDict['files']:
                        dTitle = common.toUnicode(d['title'])
                        dFormat = common.toUnicode(d['format'])
                        dCorpusPath = common.toUnicode(d['corpusPath'])
                        dURL = common.toUnicode(d['url'])

                        fileList = ['%s *(%s)*: `%s`, source: %s' % (dTitle, 
                            dFormat, dCorpusPath, dURL)]

                msg += self._list(fileList)
                #msg += self._list(fileList, INDENT*2)
            msg.append('\n'*2)
        msg.append('\n'*1)
        return ''.join(msg) # return as tring not a list


#-------------------------------------------------------------------------------
class ClassDoc(RestructuredWriter):

    def __init__(self, className, modName=None):
        RestructuredWriter.__init__(self)

        # the class name provided is qualified, with all parts such as
        # music21.note.Note; we can then get the module name
        self.className = className
        self.classNameEval = eval(className)
        self.modName = modName
        self.partitionedClass = PartitionedClass(self.classNameEval)
        # this is a tuple of class instances that are in the order
        # of this class to base class
        self.mro = inspect.getmro(self.classNameEval)
        self.docCooked = self.formatDocString(self.classNameEval.__doc__, 
                                             INDENT, modName=self.modName)
        self.name = self.classNameEval.__name__

    #---------------------------------------------------------------------------

    def _fmtRstAttributeList(self, names):
        '''Given a list of attributes, return the RST. This assumes no docs or signatures. 
        '''
        msg = []
        for name in names:
            # this presently does not work; seems too need line breaks
            #msg.append('%s.. attribute:: %s' %  (INDENT, name))
            msg.append('`%s`' %  (name))

        return ', '.join(msg)


    def _fmtRstAttribute(self, name):
        #signature = self.partitionedClass.getSignature(name)
        msg = []
        msg.append('%s.. attribute:: %s\n\n' %  (INDENT*2, name))
        #msg.append('**%s%s**\n\n' % (nameFound, postfix))   
        docRaw = self.partitionedClass.getDoc(name)
        msg.append('%s\n' % self.formatDocString(docRaw, INDENT*3, 
                            modName=self.modName))
        return ''.join(msg)

    def _fmtRstMethod(self, name):
        signature = self.partitionedClass.getSignature(name)
        msg = []
        msg.append('%s.. method:: %s%s\n\n' %  (INDENT*2, name, signature))
        #msg.append('**%s%s**\n\n' % (nameFound, postfix))   
        # do not need indent as doc is already formatted with indent
        docRaw = self.partitionedClass.getDoc(name)
        msg.append('%s\n' % self.formatDocString(docRaw, INDENT*3, 
                  modName=self.modName))
        return ''.join(msg)


    def _isAllInherited(self):
        '''Try to determine if a class is all inherited, that is: all the attributes and methods are from a subclass, and the docs will look identical.
        '''
        post = True

        # some modules can define this attribute specifically
        if hasattr(self.classNameEval, '_DOC_ALL_INHERITED'):
            environLocal.printDebug(['found _DOC_ALL_INHERITED',
                self.classNameEval._DOC_ALL_INHERITED])
            return self.classNameEval._DOC_ALL_INHERITED

        for group in ['attributes', 'properties', 'methods']:    
            # in order for this to be all-inherited, it must have 
            # an inherited class that has all the same names just
            # one level up. 

            namesParent = []
            # get all that are not the first, which is zero
            #environLocal.printDebug([group, 'mroIndices', self.partitionedClass.mroIndices()[1:]])
            for i in self.partitionedClass.mroIndices()[1:]:
                # this returns unique names; we need all names!
                level = self.partitionedClass.getNames(group, 
                        i, public=True, getInit=False)
                #environLocal.printDebug(['mro group', i, level])
                namesParent += level
                # get all names if possible; this covers cases where
                # names are present but the are defined in the final class
                if self.partitionedClass.mroLive[i] != None:
                    namesParent += dir(self.partitionedClass.mroLive[i])

            names = self.partitionedClass.getNames(group, 
                    0, public=True, getInit=False)

            # no public names means that nothing new has been defined
            if len(names) == 0:
                continue
            # if all names defined here are in the parent, then it is also
            # still is all inherited
            namesParentSet = set(namesParent)
            namesSet = set(names)

            #environLocal.printDebug(['namesParentSet', namesParentSet])
            #environLocal.printDebug(['namesSet', namesSet])

            # TODO: may need to look at doc strings in order to be sure
            # that we are not cutting out original content
            if not namesSet.issubset(namesParentSet):
                post = False
                break

        return post


    def getRestructuredClass(self):
        '''Return a string of a complete RST specification for a class.
    
        >>> from music21 import duration
        >>> a = ClassDoc('duration.Duration')
        >>> post = a.getRestructuredClass()
        '''
        msg = []
        classNameStr = '%s' % self.name
        msg += self._heading(classNameStr, '-')

#         if not self._isAllInherited():
#             msg += [".. inheritance-diagram:: %s\n\n" % classNameStr]

        msg.append('%s\n\n' % (self.formatClassInheritance(self.mro)))

        # see if this class has __init__ documentation
        signature = self.partitionedClass.getSignature('__init__')
        titleStr = '.. class:: %s%s\n\n' % (self.name, signature)
        msg += titleStr
    
        # if we have __init__ documentation, place it with class documentation    
        docInitRaw = self.partitionedClass.getDoc('__init__')
        if docInitRaw != NO_DOC:
            docInitCooked = self.formatDocString(docInitRaw, INDENT, 
                            modName=self.modName)
        else:
            docInitCooked = None

        msg.append('%s\n' % self.docCooked)
        # add init doc after main class doc
        if docInitCooked != None:
            msg.append('%s\n' % docInitCooked)

#         msg.append('%s%s\n\n' % (INDENT, self.formatClassInheritance(self.mro)))

        # if all names are inherited (the are not newly defined) then skip
        # documentation of values
        if self._isAllInherited():
            #environLocal.printDebug([self.name, 'skipping detailed component documentation'])
            msg.append('\n'*1)
            return msg

        for group in ['attributes', 'properties', 'methods']:    
            msgGroup = []
            for mroIndex in self.partitionedClass.mroIndices():
                if mroIndex == self.partitionedClass.lastMroIndex(): continue
                names = self.partitionedClass.getNames(group, mroIndex,
                        public=True, getInit=False)
                if len(names) == 0: continue

                if mroIndex != 0: # inherited
                    parentSrc = self.formatParent(
                        self.partitionedClass.getClassFromMroIndex(mroIndex))
                    groupStr = group.title()
                    msgGroup.append('%s%s inherited from %s: ' % (INDENT*2, groupStr, parentSrc))
                    msgSub = []
                    for partName in names:
                        msgSub.append(self.formatXRef(partName, group,
                         self.partitionedClass.getClassFromMroIndex(mroIndex)))
                    msgGroup.append('%s\n\n' % ', '.join(msgSub))

                elif mroIndex == 0: # local
                    if group == 'attributes': # split only for local
                        groupSubList = ['attributes-doc', 'attributes-nodoc']
                    else:
                        groupSubList = [group]

                    for groupSub in groupSubList:
                        # get new names as we are dealing with sub groups
                        namesSub = self.partitionedClass.getNames(groupSub, 
                                mroIndex, public=True, getInit=False)
                        if len(namesSub) == 0: continue

                        if groupSub in ['attributes-nodoc']:
                            msgGroup.append(
                            '%sAttributes without Documentation: %s\n\n' % (
                             INDENT*2, self._fmtRstAttributeList(namesSub)))
                        for partName in namesSub:
                            if groupSub in ['attributes-doc', 'properties']:
                                msgGroup.append(self._fmtRstAttribute(partName))
                            elif groupSub == 'methods':
                                msgGroup.append(self._fmtRstMethod(partName))

            if len(msgGroup) > 0: # add the title for this group
                msg.append('%s**%s** **%s**\n\n' % (INDENT, 
                           classNameStr, group))
                msg.append(''.join(msgGroup))

        msg.append('\n'*1)
        return msg



#-------------------------------------------------------------------------------
class ModuleDoc(RestructuredWriter):
    def __init__(self, modNameEval):
        RestructuredWriter.__init__(self)

        self.partitionedModule = PartitionedModule(modNameEval)
        self.modNameEval = modNameEval
        self.modName = self.modNameEval.__name__

        self.docCooked = self.formatDocString(modNameEval.__doc__, 
                         modName=self.modName)

        def capFirst(stringVar): # not the same as .title()
            return stringVar[0].upper() + stringVar[1:]

        # file name for this module; leave off music21 part
        fn = self.modName.split('.')
        self.fileRef = 'module'
        for index in range(1,len(fn)):
            self.fileRef = self.fileRef + capFirst(fn[index])
            
#        if len(fn) == 2:
#            self.fileRef = 'module' + capFirst(fn[1])
#        elif len(fn) == 3:
#            self.fileRef = 'module' + capFirst(fn[1]) + capFirst(fn[2])
#        else:
#            raise Exception('cannot determine file name from module name: %s' % self.modName)

        self.fileName = self.fileRef + '.rst'
        # references used in rst table of contents

    def _fmtRstFunction(self, name, signature):
        msg = []
        msg.append('.. function:: %s%s\n\n' %  (name, signature))
        docRaw = self.partitionedModule.getDoc(name)
        msg.append('%s\n' % self.formatDocString(docRaw, INDENT*1, 
                         modName=self.modName))
        return ''.join(msg)

    def getRestructured(self):
        '''Produce RST documentation for a complete module.
        '''
        # produce a simple string name of module to tag top of rst file
        modNameStr = self.modName.replace('music21.', '')
        modNameStr = modNameStr[0].upper() + modNameStr[1:]

        msg = []
        # the heading needs to immediately follow the underscore identifier
        msg.append('.. _module%s:\n\n' % modNameStr)
        msg += self._heading(self.modName , '=')

        # add any global roles here
        #msg.append('.. roles:: import\n\n')

        msg.append(WARN_EDIT)
        # this defines this rst file as a module; does not create output
        # this should be a list?
        msg += '.. module:: %s\n\n' % self.modName
        msg += self.docCooked
        msg.append('\n\n')

        for group in ['functions', 'classes']:
            names = self.partitionedModule.getNames(group)
            if len(names) == 0: continue

            for partName in names:
                subMsg = [] 
                if group == 'functions':
                    signature = self.partitionedModule.getSignature(partName)
                    subMsg.append(self._fmtRstFunction(partName, signature))
                    #msg += '.. function:: %s()\n\n' % partName
                    #msg.append('%s\n' % self.functions[funcName]['doc'])
                if group == 'classes':
                    qualifiedName = '%s.%s' % (self.modName, partName)
                    classDoc = ClassDoc(qualifiedName, modName=self.modName)
                    subMsg += classDoc.getRestructuredClass()
                try:
                    subStr = ''.join(subMsg)
                except UnicodeDecodeError:
                    environLocal.warn(['cannot output due to unicode decode error', 'group', group, 'partName', partName])
                msg += [subStr]
        return ''.join(msg)





#-------------------------------------------------------------------------------
class Documentation(RestructuredWriter):

    def __init__(self):
        RestructuredWriter.__init__(self)

        self.titleMain = 'Music21 Documentation'

        # include additional rst files that are not auto-generated
        # order here is the order presented in text
        self.chaptersMain = ['what',
                             'quickStart',
                             'usersGuide_02_notes',
                             'usersGuide_03_pitches', 
                             'overviewStreams',
                             'usersGuide_06_chords', 
                             'overviewFormats', 
                             'overviewPostTonal', 
                             'overviewMeters', 
                             'examples', 
                             'install', 
                             'installMac', 
                             'installWindows', 
                             'installLinux', 
                             'installAdvanced', 
                             'installAdditional',
                             'tutorialFinaleMac', 
                             'about', 
                             'applications', 
                             'environment', 
                             'graphing', 
                             'advancedGraphing', 
                             ]
        self.chaptersDeveloper = ['documenting',
                                  'buildingDocumentation',
                                  'usingEclipse' 
                             ]
    
        self.chaptersModuleRef = [] # to be populated
        self.chaptersReference = ['faq',
                             'glossary',
                            ] # to be populated

        #self.titleAppendix = 'Indices and Tables'
        #self.chaptersAppendix = ['glossary']
    
        self.modulesToBuild = MODULES
        self.updateDirs()

    def copyStaticDocumentation(self):
        '''
        copy the static documentation from the staticDocs
        directory to the rst directory, along the way
        removing "# doctest: +SKIP" lines
        
        (and eventually everything else we don't want)
        '''
        staticDir = self.dirStatic
        outputDir = self.dirRst
        for fileName in os.listdir(staticDir):
            sourceFile = staticDir + os.sep + fileName
            destinationFile = outputDir + os.sep + fileName
            if not fileName.endswith('.rst') and not fileName.endswith('.html'):
                if not fileName.startswith('.svn'):
                    environLocal.warn('file %s is in staticDocs dir but is not an .rst or .html file' % (fileName))
            elif fileName.endswith('.html'):
                shutil.copy2(sourceFile, destinationFile)
            else: #rst
                inputFH = open(sourceFile, "r")
                outputFH = open(destinationFile, "w")
                outputFH.write(".. WARNING: DO NOT EDIT THIS FILE: AUTOMATICALLY GENERATED. Edit ../staticDocs/%s\n\n" % fileName)
                for line in inputFH:
                    line2 = re.sub('#\s+doctest: \+SKIP', '', line)
                    outputFH.write(line2)
                inputFH.close()
                outputFH.close()
                


    def updateDirs(self):
        '''Update file paths.
        '''
        self.dir = common.getBuildDocFilePath()
        self.parentDir = os.path.dirname(self.dir)
        parentContents = os.listdir(self.parentDir)
        # make sure we are in the the proper directory
        if (not self.dir.endswith("buildDoc") or 
            'music21' not in parentContents):
            raise Exception("not in the music21%sbuildDoc directory: %s" % (os.sep, self.dir))
    
        self.dirBuild = os.path.join(self.parentDir, 'music21', 'doc')
        environLocal.printDebug(['self.dirBuild', self.dirBuild])

        self.dirStatic = os.path.join(self.dir, 'staticDocs')
        self.dirRst = os.path.join(self.dir, 'rst')
        self.dirBuildHtml = os.path.join(self.dirBuild, 'html')
        #self.dirBuildLatex = os.path.join(self.dirBuild, 'latex')
        self.dirBuildPdf = os.path.join(self.dirBuild, 'pdf')
        self.dirBuildDoctrees = os.path.join(self.dir, 'doctrees')

        for fp in [self.dirBuild, self.dirBuildHtml, 
                  #self.dirBuildLatex,
                  self.dirBuildDoctrees]:
                    #self.dirBuildPdf]:
            if os.path.exists(fp):
                # delete old paths?
                pass
            else:
                os.mkdir(fp)

    def writeContents(self):
        '''This writes the main table of contents file, contents.rst. 
        '''
        msg = []
        msg.append('.. _contents:\n\n')
        msg += self._heading(self.titleMain, '=')

        msg.append(WARN_EDIT)
        # first toc has expanded tree
        msg.append('.. toctree::\n')
        msg.append('   :maxdepth: 2\n\n')
        for name in self.chaptersMain:
            msg.append('   %s\n' % name)        
        msg.append('\n\n')

        msg += self._heading('System Reference', '=')
        # second toc has collapsed tree
        msg.append('.. toctree::\n')
        msg.append('   :maxdepth: 1\n\n')
        for name in self.chaptersReference:
            msg.append('   %s\n' % name)        
        msg.append('\n\n')

        msg += self._heading('Module Reference', '=')
        # second toc has collapsed tree
        msg.append('.. toctree::\n')
        msg.append('   :maxdepth: 1\n\n')
        for name in self.chaptersModuleRef:
            msg.append('   %s\n' % name)        
        msg.append('\n\n')

        msg += self._heading('Developer Reference', '=')
        # second toc has collapsed tree
        msg.append('.. toctree::\n')
        msg.append('   :maxdepth: 2\n\n')
        for name in self.chaptersDeveloper:
            msg.append('   %s\n' % name)        
        msg.append('\n\n')

#         msg += self._heading(self.titleAppendix, '=')
#         for name in self.chaptersAppendix:
#             msg.append("* :ref:`%s`\n" % name)
#         msg.append('\n')

        fp = os.path.join(self.dirRst, 'contents.rst')
        f = open(fp, 'w')
        f.write(''.join(msg))
        f.close()


    def writeModuleReference(self):
        '''Write a .rst file for each module defined in modulesToBuild.
        Add the file reference to the list of chaptersModuleRef.
        '''
        totalModules = len(self.modulesToBuild)
        for i, module in enumerate(self.modulesToBuild):
            #environLocal.printDebug(['writing rst documentation:', module])

            a = ModuleDoc(module)
            # for debugging, can comment these three lines out and 
            # edit rst files directly
            percentageLength = int((i*100.0)/totalModules)
            
            print("writing module doc as .rst... [%3s%%] %s" % (percentageLength, a.fileName))
            f = open(os.path.join(self.dirRst, a.fileName), 'w')
            f.write(a.getRestructured().encode( "utf-8" ) )
            f.close()

            self.chaptersModuleRef.append(a.fileRef)


    def writeGeneratedChapters(self):
        '''Create generated chapters. 
        '''
        for obj in [CorpusDoc()]:
            f = open(os.path.join(self.dirRst, obj.fileName), 'w')

#            f.write(obj.getRestructured())

#             f.write(codecs.BOM_UTF8)
            f.write(obj.getRestructured().encode( "utf-8" ) )

            f.close()
            self.chaptersReference.append(obj.fileRef)



    #---------------------------------------------------------------------------
    def main(self, buildFormat):
        '''Create the documentation. 
        '''
        if buildFormat not in FORMATS:
            raise Exception, 'bad format'
        print ("Copying static documentation")
        self.copyStaticDocumentation()
        print ("Writing generated chapters (referenceCorpus)")
        self.writeGeneratedChapters()    
        print ("Writing module references")
        self.writeModuleReference()    
        print ("Writing contents")
        self.writeContents()    

        if buildFormat == 'html':
            dirOut = self.dirBuildHtml
            pathLaunch = os.path.join(self.dirBuildHtml, 'contents.html')
        elif buildFormat == 'latex':
            dirOut = self.dirBuildLatex
            #pathLaunch = os.path.join(dirBuildHtml, 'contents.html')
        elif buildFormat == 'pdf':
            dirOut = self.dirBuildPdf
        else:
            raise Exception('undefined format %s' % buildFormat)

        if common.getPlatform() in ['darwin', 'nix', 'win']:
            # -b selects the builder
            try:
                import sphinx
            except ImportError:
                raise BuildException("Building documentation requires the Sphinx toolkit. Download it by typing 'easy_install -U Sphinx' at the command line or at http://sphinx.pocoo.org/")
            sphinxList = ['sphinx', '-E', '-b', buildFormat, 
                         '-d', self.dirBuildDoctrees,
                         self.dirRst, dirOut] 
            unused_statusCode = sphinx.main(sphinxList)

        if buildFormat == 'html':
            if pathLaunch.find('\\'):
                pass
            else:
                if pathLaunch.startswith('/'):
                    pathLaunch = 'file://' + pathLaunch
            webbrowser.open(pathLaunch)

class BuildException(exceptions21.Music21Exception):
    pass





#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def setUp(self):
        pass

    def testFormatDocStringA(self):

        rw = RestructuredWriter()
        
        pre = '''
        Given a step (C, D, E, F, etc.) return the accidental
        for that note in this key (using the natural minor for minor)
        or None if there is none.

        >>> from music21 import *

        >>> g = key.KeySignature(1)
        >>> g.accidentalByStep("F")
        <accidental sharp>
        >>> g.accidentalByStep("G")

        >>> f = KeySignature(-1)
        >>> bbNote = note.Note("B-5")
        >>> f.accidentalByStep(bbNote.step)
        <accidental flat>     


        Fix a wrong note in F-major:

        
        >>> wrongBNote = note.Note("B#4")
        >>> if f.accidentalByStep(wrongBNote.step) != wrongBNote.accidental:
        ...    wrongBNote.accidental = f.accidentalByStep(wrongBNote.step)
        >>> wrongBNote
        <music21.note.Note B->
       

        .. image:: images/keyAccidentalByStep.*
            :width: 400


        Set all notes to the correct notes for a key using the note's Context::
        
            * fix this
            * fix that
        
        
        >>> from music21 import *
        >>> s1 = stream.Stream()
        >>> s1.append(key.KeySignature(4))  # E-major or C-sharp-minor
        >>> s1.append(note.HalfNote("C"))
        >>> s1.append(note.HalfNote("E-"))
        >>> s1.append(key.KeySignature(-4)) # A-flat-major or F-minor
        >>> s1.append(note.WholeNote("A"))
        >>> s1.append(note.WholeNote("F#"))
        >>> for n in s1.notesAndRests:
        ...    n.accidental = n.getContextByClass(key.KeySignature).accidentalByStep(n.step)
        >>> #_DOCS_SHOW s1.show()


        OMIT_FROM_DOCS
        >>> s1.show('text')
        {0.0} <music21.key.KeySignature of 4 sharps>
        {0.0} <music21.note.Note C#>
        {2.0} <music21.note.Note E>
        {4.0} <music21.key.KeySignature of 4 flats>
        {4.0} <music21.note.Note A->
        {8.0} <music21.note.Note F>
        
        
        Test to make sure there are not linked accidentals (fixed bug 22 Nov. 2010)
        
        >>> nB1 = note.WholeNote("B")
        >>> nB2 = note.WholeNote("B")
        >>> s1.append(nB1)
        >>> s1.append(nB2)
        >>> for n in s1.notesAndRests:
        ...    n.accidental = n.getContextByClass(key.KeySignature).accidentalByStep(n.step)
        >>> (nB1.accidental, nB2.accidental)
        (<accidental flat>, <accidental flat>)
        >>> nB1.accidental.name = 'sharp'
        >>> (nB1.accidental, nB2.accidental)
        (<accidental sharp>, <accidental flat>)
        
        '''

        post = rw.formatDocString(pre)
        #print post

        match = """Given a step (C, D, E, F, etc.) return the accidental
for that note in this key (using the natural minor for minor)
or None if there is none.



>>> from music21 import *
⁠ 
>>> g = key.KeySignature(1)
>>> g.accidentalByStep("F")
<accidental sharp>
>>> g.accidentalByStep("G")



>>> f = KeySignature(-1)
>>> bbNote = note.Note("B-5")
>>> f.accidentalByStep(bbNote.step)
<accidental flat>


Fix a wrong note in F-major:




>>> wrongBNote = note.Note("B#4")
>>> if f.accidentalByStep(wrongBNote.step) != wrongBNote.accidental:
...    wrongBNote.accidental = f.accidentalByStep(wrongBNote.step)
>>> wrongBNote
<music21.note.Note B->





.. image:: images/keyAccidentalByStep.*
        :width: 400



Set all notes to the correct notes for a key using the note's Context::

    * fix this
    * fix that




>>> from music21 import *
>>> s1 = stream.Stream()
>>> s1.append(key.KeySignature(4))  # E-major or C-sharp-minor
>>> s1.append(note.HalfNote("C"))
>>> s1.append(note.HalfNote("E-"))
>>> s1.append(key.KeySignature(-4)) # A-flat-major or F-minor
>>> s1.append(note.WholeNote("A"))
>>> s1.append(note.WholeNote("F#"))
>>> for n in s1.notesAndRests:
...    n.accidental = n.getContextByClass(key.KeySignature).accidentalByStep(n.step)
>>> s1.show()
"""
        self.maxDiff = None
        #print post.strip()
        #print match.strip()
        self.assertEqual(post.strip(), match.strip())



#-------------------------------------------------------------------------------
if __name__ == '__main__':
    #sys.argv.append('test')
    if len(sys.argv) == 2 and sys.argv[1] == 'test':
        music21.mainTest(Test)
        buildDoc = False
    elif len(sys.argv) == 2 and sys.argv[1] in FORMATS:
        formatList = [sys.argv[1]]
        buildDoc = True
    else:
        formatList = ['html']#, 'pdf']
        buildDoc = True

    if buildDoc:
        for fmt in formatList:
            a = Documentation()
            a.main(fmt)
