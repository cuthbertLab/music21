# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         metadata.py
# Purpose:      music21 classes for representing score and work meta-data
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010, 2012 Michael Scott Cuthbert and the music21
# Project License:      LGPL, see license.txt
#-------------------------------------------------------------------------------
'''Classes and functions for creating and processing metadata associated with
scores, works, and fragments, such as titles, movements, authors, publishers,
and regions.

The :class:`~music21.metadata.Metadata` object is the main public interface to
metadata components. A Metadata object can be added to a Stream and used to set
common score attributes, such as title and composer. A Metadata object found at
offset zero can be accessed through a Stream's
:attr:`~music21.stream.Stream.metadata` property. 

The following example creates a :class:`~music21.stream.Stream` object, adds a
:class:`~music21.note.Note` object, and configures and adds the
:attr:`~music21.metadata.Metadata.title` and
:attr:`~music21.metadata.Metadata.composer` properties of a Metadata object. 

::

    >>> s = stream.Stream()
    >>> s.append(note.Note())
    >>> s.insert(metadata.Metadata())
    >>> s.metadata.title = 'title'
    >>> s.metadata.composer = 'composer'
    >>> #_DOCS_SHOW s.show()

.. image:: images/moduleMetadata-01.*
    :width: 600

'''

import datetime
import multiprocessing
import os
import pickle
import re
import time
import traceback
import unittest

from music21 import base
from music21 import common
from music21 import exceptions21
from music21 import freezeThaw
from music21 import text
from music21.metadata.primitives import *

from music21 import environment
_MOD = "metadata.py"
environLocal = environment.Environment(_MOD)

#-------------------------------------------------------------------------------


#-------------------------------------------------------------------------------
# utility dictionaries and conversion functions; used by objects defined in this
# module

# error can be designated with either symbol in string date representations


workIdAbbreviationDict = {
    'otl' : 'title',
    'otp' : 'popularTitle',
    'ota' : 'alternativeTitle',
    'opr' : 'parentTitle',
    'oac' : 'actNumber',

    'osc' : 'sceneNumber',
    'omv' : 'movementNumber',
    'omd' : 'movementName',
    'ops' : 'opusNumber',
    'onm' : 'number',

    'ovm' : 'volume',
    'ode' : 'dedication',
    'oco' : 'commission',
    'gtl' : 'groupTitle',
    'gaw' : 'associatedWork',

    'gco' : 'collectionDesignation',
    'txo' : 'textOriginalLanguage',
    'txl' : 'textLanguage',

    'ocy' : 'countryOfComposition',
    'opc' : 'localeOfComposition', # origin in abc
    }

# store a reference dictionary for quick lookup, with full attr names
# as keys
workIdLookupDict = {}
for key, value in workIdAbbreviationDict.items(): 
    workIdLookupDict[value.lower()] = key

# !!!OTL: Title. 
# !!!OTP: Popular Title.
# !!!OTA: Alternative title.
# !!!OPR: Title of larger (or parent) work 
# !!!OAC: Act number.
# !!!OSC: Scene number.
# !!!OMV: Movement number.
# !!!OMD: Movement designation or movement name. 
# !!!OPS: Opus number. 
# !!!ONM: Number.
# !!!OVM: Volume.
# !!!ODE: Dedication. 
# !!!OCO: Commission
# !!!GTL: Group Title. 
# !!!GAW: Associated Work. 
# !!!GCO: Collection designation. 
# !!!TXO: Original language of vocal/choral text. 
# !!!TXL: Language of the encoded vocal/choral text. 
# !!!OCY: Country of composition. 
# !!!OPC: City, town or village of composition. 


WORK_ID_ABBREVIATIONS = workIdAbbreviationDict.keys()
WORK_IDS = workIdAbbreviationDict.values()


def abbreviationToWorkId(value):
    '''Get work id abbreviations.

    ::

        >>> metadata.abbreviationToWorkId('otl')
        'title'

    ::

        >>> for id in metadata.WORK_ID_ABBREVIATIONS: 
        ...    post = metadata.abbreviationToWorkId(id)
        ...

    '''
    value = value.lower()
    if value in workIdAbbreviationDict:
        return workIdAbbreviationDict[value]
    else:
        raise exceptions21.MetadataException(
            'no such work id: %s' % value)

def workIdToAbbreviation(value):
    '''Get a work abbreviation from a string representation.

    ::

        >>> metadata.workIdToAbbreviation('localeOfComposition')
        'opc'

    ::

        >>> for n in metadata.WORK_IDS:
        ...     post = metadata.workIdToAbbreviation(n)
        ...

    '''
    # NOTE: this is a performance critical function
    try:
        # try direct access, where keys are already lower case
        return workIdLookupDict[value] 
    except KeyError:
        pass

    # slow approach
    for work_id in WORK_ID_ABBREVIATIONS:
        if value.lower() == workIdAbbreviationDict[work_id].lower():
            return work_id
    raise exceptions21.MetadataException(
        'no such work id: %s' % value)


#-------------------------------------------------------------------------------


class Metadata(base.Music21Object):
    '''
    
    Metadata represent data for a work or fragment, including title, composer,
    dates, and other relevant information.

    Metadata is a :class:`~music21.base.Music21Object` subclass, meaing that it
    can be positioned on a Stream by offset and have a
    :class:`~music21.duration.Duration`.

    In many cases, each Stream will have a single Metadata object at the zero
    offset position.

    ::

        >>> md = metadata.Metadata(title='Concerto in F')
        >>> md.title
        'Concerto in F'
    
    ::

        >>> md = metadata.Metadata(otl='Concerto in F') # can use abbreviations
        >>> md.title
        'Concerto in F'

    ::

        >>> md.setWorkId('otl', 'Rhapsody in Blue')
        >>> md.otl
        'Rhapsody in Blue'

    ::

        >>> md.title
        'Rhapsody in Blue'

    '''

    ### CLASS VARIABLES ###

    classSortOrder = -10 

    ### INITIALIZER ###

    def __init__(self, *args, **keywords):
        base.Music21Object.__init__(self)

        # a list of Contributor objects
        # there can be more than one composer, or any other combination
        self._contributors = []
        self._date = None

        # store one or more URLs from which this work came; this could
        # be local file paths or otherwise
        self._urls = []

        # TODO: need a specific object for copyright and imprint
        self._imprint = None
        self._copyright = None

        # a dictionary of Text elements, where keys are work id strings
        # all are loaded with None by default
        self._workIds = {}
        for abbr, work_id in workIdAbbreviationDict.items():
            #abbr = workIdToAbbreviation(id)
            if work_id in keywords:
                self._workIds[work_id] = Text(keywords[work_id])
            elif abbr in keywords:
                self._workIds[work_id] = Text(keywords[abbr])
            else:
                self._workIds[work_id] = None

        # search for any keywords that match attributes 
        # these are for direct Contributor access, must have defined
        # properties
        for attr in ['composer', 'date', 'title']:
            if attr in keywords:
                setattr(self, attr, keywords[attr])
        
        # used for the search() methods to determine what attributes
        # are made available by default; add more as properties/import 
        # exists
        self._searchAttributes = [
            'date', 
            'title', 
            'alternativeTitle', 
            'movementNumber', 
            'movementName', 
            'number', 
            'opusNumber', 
            'composer', 
            'localeOfComposition',
            ]

    ### SPECIAL METHODS ###

    def __getattr__(self, name):
        '''Utility attribute access for attributes that do not yet have property definitions. 
        '''
        match = None
        for abbr, work_id in workIdAbbreviationDict.items():
        #for id in WORK_IDS:
            #abbr = workIdToAbbreviation(id)
            if name == work_id:
                match = work_id 
                break
            elif name == abbr:
                match = work_id 
                break
        if match is None:
            raise AttributeError('object has no attribute: %s' % name)
        post = self._workIds[match]
        # always return string representation for now
        return str(post)

    ### PUBLIC METHODS ###

    def addContributor(self, c):
        '''
        Assign a :class:`~music21.metadata.Contributor` object to this
        Metadata.

        ::

            >>> md = metadata.Metadata(title='Third Symphony')
            >>> c = metadata.Contributor()
            >>> c.name = 'Beethoven, Ludwig van'
            >>> c.role = 'composer'
            >>> md.addContributor(c)
            >>> md.composer
            'Beethoven, Ludwig van'

        ::

            >>> md.composer = 'frank'
            >>> md.composers
            ['Beethoven, Ludwig van', 'frank']

        '''
        if not isinstance(c, Contributor):
            raise exceptions21.MetadataException(
                'supplied object is not a Contributor: %s' % c)
        self._contributors.append(c)

    def getContributorsByRole(self, value):
        '''
        Return a :class:`~music21.metadata.Contributor` if defined for a
        provided role. 
        
        ::

            >>> md = metadata.Metadata(title='Third Symphony')

        ::

            >>> c = metadata.Contributor()
            >>> c.name = 'Beethoven, Ludwig van'
            >>> c.role = 'composer'
            >>> md.addContributor(c)
            >>> cList = md.getContributorsByRole('composer')
            >>> cList[0].name
            'Beethoven, Ludwig van'
        
        Some musicxml files have contributors with no role defined.  To get
        these contributors, search for getContributorsByRole(None).  N.B. upon
        output to MusicXML, music21 gives these contributors the generic role
        of "creator"
        
        ::

            >>> c2 = metadata.Contributor()
            >>> c2.name = 'Beth Hadley'
            >>> md.addContributor(c2)
            >>> noRoleList = md.getContributorsByRole(None)
            >>> len(noRoleList)
            1

        ::

            >>> noRoleList[0].role
            >>> noRoleList[0].name
            'Beth Hadley'
        
        '''
        post = [] # there may be more than one per role
        for c in self._contributors:
            if c.role == value:
                post.append(c)
        if len(post) > 0:
            return post 
        else:
            return None

    def search(self, query, field=None):
        '''
        Search one or all fields with a query, given either as a string or a
        regular expression match.

        ::

            >>> md = metadata.Metadata()
            >>> md.composer = 'Beethoven, Ludwig van'
            >>> md.title = 'Third Symphony'

        ::

            >>> md.search('beethoven', 'composer')
            (True, 'composer')
        
        ::

            >>> md.search('beethoven', 'compose')
            (True, 'composer')

        ::

            >>> md.search('frank', 'composer')
            (False, None)

        ::

            >>> md.search('frank')
            (False, None)

        ::

            >>> md.search('third')
            (True, 'title')

        ::

            >>> md.search('third', 'composer')
            (False, None)

        ::

            >>> md.search('third', 'title')
            (True, 'title')

        ::

            >>> md.search('third|fourth')
            (True, 'title')

        ::

            >>> md.search('thove(.*)')
            (True, 'composer')

        '''
        valueFieldPairs = []
        if field != None:
            match = False
            try:
                value = getattr(self, field)
                valueFieldPairs.append((value, field))
                match = True
            except AttributeError:
                pass
            if not match:
                for f in self._searchAttributes:
                    #environLocal.printDebug(['comparing fields:', f, field])
                    # look for partial match in all fields
                    if field.lower() in f.lower():
                        value = getattr(self, f)
                        valueFieldPairs.append((value, f))
                        match = True
                        break
            # if cannot find a match for any field, return 
            if not match:
                return False, None
        else: # get all fields
            for f in self._searchAttributes:
                value = getattr(self, f)
                valueFieldPairs.append((value, f))
        # for now, make all queries strings
        # ultimately, can look for regular expressions by checking for
        # .search
        useRegex = False
        if hasattr(query, 'search'):
            useRegex = True
            reQuery = query # already compiled
        # look for regex characters
        elif common.isStr(query) and \
            any(character in query for character in '*.|+?{}'):
            useRegex = True
            reQuery = re.compile(query, flags=re.I) 
        if useRegex:
            for v, f in valueFieldPairs:
                # re.I makes case insensitive
                match = reQuery.search(str(v))
                if match is not None:
                    return True, f
        else:
            query = str(query)
            for v, f in valueFieldPairs:
                if common.isStr(v):
                    if query.lower() in v.lower():
                        return True, f
                elif query == v: 
                    return True, f
        return False, None
            
    def setWorkId(self, idStr, value):
        '''
        Directly set a workd id, given either as a full string name or as a
        three character abbreviation. The following work id abbreviations and
        their full id string are given as follows. In many cases the Metadata
        object support properties for convenient access to these work ids. 

        Id abbreviations and strings: otl / title, otp / popularTitle, ota /
        alternativeTitle, opr / parentTitle, oac / actNumber, osc /
        sceneNumber, omv / movementNumber, omd / movementName, ops /
        opusNumber, onm / number, ovm / volume, ode / dedication, oco /
        commission, gtl / groupTitle, gaw / associatedWork, gco /
        collectionDesignation, txo / textOriginalLanguage, txl / textLanguage,
        ocy / countryOfComposition, opc / localeOfComposition.
        
        ::

            >>> md = metadata.Metadata(title='Quartet')
            >>> md.title
            'Quartet'

        ::

            >>> md.setWorkId('otl', 'Trio')
            >>> md.title
            'Trio'

        ::

            >>> md.setWorkId('sdf', None)
            Traceback (most recent call last):
            MetadataException: no work id available with id: sdf

        '''
        idStr = idStr.lower()
        match = False
        for abbr, work_id in workIdAbbreviationDict.items():
        #for id in WORK_IDS:
            #abbr = workIdToAbbreviation(id)
            if work_id.lower() == idStr:
                self._workIds[work_id] = Text(value)
                match = True
                break
            elif abbr == idStr:
                self._workIds[work_id] = Text(value)
                match = True
                break
        if not match:
            raise exceptions21.MetadataException(
                'no work id available with id: %s' % idStr)

    ### PUBLIC PROPERTIES ###

    @apply
    def alternativeTitle(): # @NoSelf
        def fget(self):
            '''
            Get or set the alternative title. 
            
            ::

                >>> md = metadata.Metadata(popularTitle='Eroica')
                >>> md.alternativeTitle = 'Heroic Symphony'
                >>> md.alternativeTitle
                'Heroic Symphony'

            '''
            post = self._workIds['alternativeTitle']
            if post == None:
                return None
            return str(self._workIds['alternativeTitle'])
        def fset(self, value):
            self._workIds['alternativeTitle'] = Text(value)
        return property(**locals())

    @apply
    def composer(): # @NoSelf
        def fget(self):
            '''
            Get or set the composer of this work. More than one composer may be
            specified.

            The composer attribute does not live in Metadata, but creates a
            :class:`~music21.metadata.Contributor` object in the Metadata
            object.
            
            ::

                >>> md = metadata.Metadata(
                ...     title='Third Symphony',
                ...     popularTitle='Eroica', 
                ...     composer='Beethoven, Ludwig van',
                ...     )
                >>> md.composer
                'Beethoven, Ludwig van'

            '''
            post = self.getContributorsByRole('composer')
            if post == None:
                return None
            # get just the name of the first composer
            return str(post[0].name)
        def fset(self, value):
            c = Contributor()
            c.name = value
            c.role = 'composer'
            self._contributors.append(c)
        return property(**locals())

    @property
    def composers(self):
        '''
        Get a list of all :class:`~music21.metadata.Contributor` objects
        defined as composer of this work.
        '''
        post = self.getContributorsByRole('composer')
        if post == None:
            return None
        # get just the name of the first composer
        return [x.name for x in post]

    @apply
    def date(): # @NoSelf
        def fget(self):
            '''
            Get or set the date of this work as one of the following date objects:
            :class:`~music21.metadata.DateSingle`,
            :class:`~music21.metadata.DateRelative`,
            :class:`~music21.metadata.DateBetween`,
            :class:`~music21.metadata.DateSelection`, 
            
            ::

                >>> md = metadata.Metadata(
                ...     title='Third Symphony', 
                ...     popularTitle='Eroica', 
                ...     composer='Beethoven, Ludwig van',
                ...     )
                >>> md.date = '2010'
                >>> md.date
                '2010/--/--'

            ::

                >>> md.date = metadata.DateBetween(['2009/12/31', '2010/1/28'])
                >>> md.date
                '2009/12/31 to 2010/01/28'

            '''
            return str(self._date)
        def fset(self, value):
            if isinstance(value, DateSingle): # all inherit date single
                self._date = value
            else:
                ds = DateSingle(value) # assume date single; could be other sublcass
                self._date = ds
        return property(**locals())

    @apply
    def localeOfComposition():  # @NoSelf
        def fget(self):
            '''
            Get or set the locale of composition, or origin, of the work. 
            '''
            post = self._workIds['localeOfComposition']
            if post == None:
                return None
            return str(self._workIds['localeOfComposition'])
        def fset(self, value):
            self._workIds['localeOfComposition'] = Text(value)
        return property(**locals())

    @apply
    def movementName(): # @NoSelf
        def fget(self):
            '''
            Get or set the movement title. 
            
            Note that a number of pieces from various MusicXML datasets have the piece title as the movement title.
            For instance, the Bach Chorales, since they are technically movements of larger cantatas.
            '''
            post = self._workIds['movementName']
            if post == None:
                return None
            return str(self._workIds['movementName'])
        def fset(self, value):
            self._workIds['movementName'] = Text(value)
        return property(**locals())

    @apply
    def movementNumber(): # @NoSelf
        def fget(self):
            '''
            Get or set the movement number. 
            '''
            post = self._workIds['movementNumber']
            if post == None:
                return None
            return str(self._workIds['movementNumber'])
        def fset(self, value):
            self._workIds['movementNumber'] = Text(value)
        return property(**locals())

    @apply
    def number(): # @NoSelf
        def fget(self):
            '''
            Get or set the number of the work.  
            
            TODO: Explain what this means...
            '''
            post = self._workIds['number']
            if post == None:
                return None
            return str(self._workIds['number'])
        def fset(self, value):
            self._workIds['number'] = Text(value)
        return property(**locals())

    @apply
    def opusNumber(): # @NoSelf
        def fget(self):
            '''
            Get or set the opus number. 
            '''
            post = self._workIds['opusNumber']
            if post == None:
                return None
            return str(self._workIds['opusNumber'])
        def fset(self, value):
            self._workIds['opusNumber'] = Text(value)
        return property(**locals())

    @apply
    def title(): # @NoSelf
        def fget(self):
            '''
            Get the title of the work, or the next-matched title string
            available from a related parameter fields. 

            ::

                >>> md = metadata.Metadata(title='Third Symphony')
                >>> md.title
                'Third Symphony'
            
            ::

                >>> md = metadata.Metadata(popularTitle='Eroica')
                >>> md.title
                'Eroica'
            
            ::

                >>> md = metadata.Metadata(
                ...     title='Third Symphony', 
                ...     popularTitle='Eroica',
                ...     )
                >>> md.title
                'Third Symphony'

            ::

                >>> md.popularTitle
                'Eroica'

            ::

                >>> md.otp
                'Eroica'

            '''
            searchId = ['title', 'popularTitle', 'alternativeTitle', 'movementName']
            post = None
            for key in searchId:
                post = self._workIds[key]
                if post != None: # get first matched
                    # get a string from this Text object
                    # get with normalized articles
                    return self._workIds[key].getNormalizedArticle()
        def fset(self, value):
            self._workIds['title'] = Text(value)
        return property(**locals())


#-------------------------------------------------------------------------------


class RichMetadata(Metadata):
    '''

    RichMetadata adds to Metadata information about the contents of the Score
    it is attached to. TimeSignature, KeySignature and related analytical is
    stored.  RichMetadata are generally only created in the process of creating
    stored JSON metadata. 

    ::

        >>> rmd = metadata.RichMetadata(title='Concerto in F')
        >>> rmd.title
        'Concerto in F'

    ::

        >>> rmd.keySignatureFirst = key.KeySignature(-1)
        >>> 'keySignatureFirst' in rmd._searchAttributes
        True

    '''

    ### INITIALIZER ###

    def __init__(self, *args, **keywords):
        Metadata.__init__(self, *args, **keywords)
        self.ambitus = None
        self.keySignatureFirst = None
        self.keySignatures = []
        self.noteCount = None
        self.pitchHighest = None
        self.pitchLowest = None
        self.quarterLength = None
        self.tempoFirst = None
        self.tempos = []
        self.timeSignatureFirst = None
        self.timeSignatures = []
        # append to existing search attributes from Metdata
        self._searchAttributes += [
            'keySignatureFirst', 'timeSignatureFirst', 'pitchHighest', 
            'pitchLowest', 'noteCount', 'quarterLength',
            ]

    ### PUBLIC METHODS ###

    def merge(self, other, favorSelf=False):
        '''
        Given another Metadata or RichMetadata object, combine
        all attributes and return a new object.

        ::

            >>> md = metadata.Metadata(title='Concerto in F')
            >>> md.title
            'Concerto in F'

        ::

            >>> rmd = metadata.RichMetadata()
            >>> rmd.merge(md)
            >>> rmd.title
            'Concerto in F'

        '''
        # specifically name attributes to copy, as do not want to get all
        # Metadata is a m21 object
        localNames = [
            '_contributors', '_date', '_urls', '_imprint', '_copyright', 
            '_workIds',
            ]
        environLocal.printDebug(['RichMetadata: calling merge()'])
        for name in localNames: 
            localValue = getattr(self, name)
            # if not set, and favoring self, then only then set
            # this will not work on dictionaries
            if localValue != None and favorSelf:
                continue
            else:
                try:
                    if other is not None:
                        otherValue = getattr(other, name)
                        if otherValue is not None:
                            setattr(self, name, otherValue)
                except AttributeError:
                    pass

    def update(self, streamObj):
        '''
        Given a Stream object, update attributes with stored objects. 
        '''
        environLocal.printDebug(['RichMetadata: update(): start'])
        
        # clear all old values
        self.keySignatureFirst = None
        #self.keySignatures = []
        self.timeSignatureFirst = None
        #self.timeSignatures = []
        self.tempoFirst = None
        #self.tempos = []

        self.noteCount = None
        self.quarterLength = None

        self.ambitus = None
        self.pitchHighest = None
        self.pitchLowest = None

        # get flat sorted stream
        flat = streamObj.flat.sorted

        tsStream = flat.getElementsByClass('TimeSignature')
        if len(tsStream) > 0:
            # just store the string representation  
            # re-instantiating TimeSignature objects is expensive
            self.timeSignatureFirst = tsStream[0].ratioString
        
        # this presently does not work properly b/c ts comparisons are not
        # built-in; need to add __eq__ methods to MeterTerminal
#         for ts in tsStream:
#             if ts not in self.timeSignatures:
#                 self.timeSignatures.append(ts)

        ksStream = flat.getElementsByClass('KeySignature')
        if len(ksStream) > 0:
            self.keySignatureFirst = str(ksStream[0])
#         for ks in ksStream:
#             if ks not in self.keySignatures:
#                 self.keySignatures.append(ts)

        self.noteCount = len(flat.notesAndRests)
        self.quarterLength = flat.highestTime

# commenting out temporarily due to memory error     
# with corpus/beethoven/opus132.xml
#         # must be a method-level import
#         from music21.analysis import discrete
   
#         environLocal.printDebug(['RichMetadata: update(): calling discrete.Ambitus(streamObj)'])
# 
#         analysisObj = discrete.Ambitus(streamObj)    
#         psRange = analysisObj.getPitchSpan(streamObj)
#         if psRange != None: # may be none if no pitches are stored
#             # presently, these are numbers; convert to pitches later
#             self.pitchLowest = str(psRange[0]) 
#             self.pitchHighest = str(psRange[1])
# 
#         self.ambitus = analysisObj.getSolution(streamObj)


#-------------------------------------------------------------------------------


class MetadataEntry(object):
    
    ### INITIALIZER ###
    
    def __init__(self, 
        accessPath=None,
        cacheTime=None,
        filePath=None, 
        number=None, 
        richMetadata=None, 
        ):
        self._accessPath = accessPath
        self._cacheTime = cacheTime
        self._filePath = filePath
        self._number = number
        self._richMetadata = richMetadata

    ### SPECIAL METHODS ###

    def __getnewargs__(self):
        return (
            self.accessPath,
            self.cacheTime,
            self.filePath,
            self.richMetadata,
            self.number,
            )

    def __repr__(self):
        return '<{0}.{1}: {2}>'.format(
            self.__class__.__module__,
            self.__class__.__name__,
            self.corpusPath,
            )

    ### PUBLIC METHODS ###

    def parse(self):
        from music21 import corpus
        if self.number is not None:
            return corpus.parse(self.filePath, number=self.number)
        else:
            return corpus.parse(self.filePath)

    def search(self, query, field=None):
        return self.richMetadata.search(query, field)

    ### PUBLIC PROPERTIES ###

    @apply
    def accessPath(): # @NoSelf
        def fget(self):
            return self._accessPath
        def fset(self, expr):
            self._accessPath = expr
        return property(**locals())

    @property
    def cacheTime(self):
        return self._cacheTime

    @property
    def corpusPath(self):
        return MetadataBundle.corpusPathToKey(self.filePath, self.number)

    @property
    def filePath(self):
        return self._filePath

    @property
    def richMetadata(self):
        return self._richMetadata

    @property
    def number(self):
        return self._number


class MetadataBundle(object):
    '''
    An object that provides access to, searches within, and stores and loads
    multiple Metadata objects.

    Additionally, multiple MetadataBundles can be merged for additional
    processing.  See corpus.metadata.metadataCache for the module that builds
    these.
    '''
    
    ### CLASS VARIABLES ###

    _DOC_ATTR = {
        'storage': 'A dictionary containing the Metadata objects that have '
            'been parsed.  Keys are strings',
        'name': 'The name of the type of MetadataBundle being made, can be '
            '"default", "corpus", or "virtual".  Possibly also "local".'
        }
    
    ### INITIALIZER ###

    def __init__(self, name='default'):
        # all keys are strings, all value are Metadata
        # there is apparently a performance boost for using all-string keys
        self.storage = {}
        # name is used to write storage file and access this bundle from multiple # bundles
        self.name = name
        # need to store local abs file path of each component
        # this will need to be refreshed after loading json data
        # keys are the same for self.storage
        self._accessPaths = {}

    ### SPECIAL METHODS ###

    def __getitem__(self, i):
        return self.storage.values()[i]

    def __len__(self):
        return len(self.storage)

    ### PRIVATE METHODS ###

    @property
    def filePath(self):
        filePath = None
        if self.name in ['virtual', 'core']:
            filePath = os.path.join(common.getMetadataCacheFilePath(), 
                self.name + '.json')
        elif self.name == 'local':
            # write in temporary dir
            filePath = os.path.join(environLocal.getRootTempDir(), 
                self.name + '.json')
        return filePath

    ### PUBLIC METHODS ###

    def addFromPaths(
        self, 
        paths, 
        printDebugAfter=0, 
        useCorpus=False,
        useMultiprocessing=True,
        ):
        '''
        Parse and store metadata from numerous files.

        If any files cannot be loaded, their file paths will be collected in a
        list that is returned.

        Returns a list of file paths with errors and stores the extracted
        metadata in `self.storage`.
        
        If `printDebugAfter` is set to an int, say 100, then after every 100
        files are parsed a message will be printed to stderr giving an update
        on progress.
        
        ::

            >>> metadataBundle = metadata.MetadataBundle()
            >>> metadataBundle.addFromPaths(
            ...     corpus.getWorkList('bwv66.6'),
            ...     useMultiprocessing=False,
            ...     )
            []

        ::

            >>> len(metadataBundle.storage)
            1

        '''
        import music21
        music21Path = music21.__path__[0]
        jobs = []
        accumulatedResults = []
        accumulatedErrors = []
        if self.filePath is not None and os.path.exists(self.filePath):
            metadataBundleModificationTime = os.path.getctime(self.filePath)
        else:
            metadataBundleModificationTime = time.time()
        environLocal.warn([
            'MetadataBundle Modification Time: {0}'.format(
                metadataBundleModificationTime)
            ])
        currentJobNumber = 0
        for filePath in paths:
            key = self.corpusPathToKey(filePath)
            if key in self.storage:
                metadataEntry = self.storage[key]  
                filePathModificationTime = os.path.getctime(filePath)
                if filePathModificationTime < metadataBundleModificationTime:
                    environLocal.warn([
                        'Skipping job: {0}; already in cache.'.format(
                            os.path.relpath(filePath)),
                        ])
                    continue
            environLocal.warn([
                'Preparing job: {0}'.format(os.path.relpath(filePath)),
                ])
            currentJobNumber += 1
            if filePath.startswith(music21Path):
                filePath = os.path.join(
                    'music21',
                    os.path.relpath(filePath, music21Path),
                    )
            job = MetadataCachingJob(
                filePath,
                jobNumber=currentJobNumber,
                useCorpus=useCorpus,
                )
            jobs.append(job)
        currentIteration = 0
        if useMultiprocessing:
            jobProcessor = JobProcessor.process_parallel
        else:
            jobProcessor = JobProcessor.process_serial
        for results, errors in jobProcessor(jobs):
            currentIteration += 1
            accumulatedResults.extend(results)
            accumulatedErrors.extend(errors)
            for metadataEntry in results:
                self.storage[metadataEntry.corpusPath] = metadataEntry
                #self.storage[corpusPath] = richMetadata
            if (currentIteration % 50) == 0:
                self.write()
        self.updateAccessPaths(paths)
        self.write()
        return accumulatedErrors

    @staticmethod
    def corpusPathToKey(filePath, number=None):
        '''Given a file path or corpus path, return the meta-data path
    
        ::

            >>> mb = metadata.MetadataBundle()
            >>> mb.corpusPathToKey('bach/bwv1007/prelude'
            ...     ).endswith('bach_bwv1007_prelude')
            True

        ::

            >>> mb.corpusPathToKey('/beethoven/opus59no1/movement1.xml'
            ...     ).endswith('beethoven_opus59no1_movement1_xml')
            True

        '''
        if 'corpus' in filePath and 'music21' in filePath:
            cp = filePath.split('corpus')[-1] # get filePath after corpus
        else:
            cp = filePath
    
        if cp.startswith(os.sep):
            cp = cp[1:]
    
        cp = cp.replace('/', '_')
        cp = cp.replace(os.sep, '_')
        cp = cp.replace('.', '_')
    
        # append name to metadata path
        if number == None:
            return cp
        else:
            # append work number
            return cp+'_%s' % number
    
    def delete(self):
        if self.filePath is not None:
            os.remove(self.filePath)
        return self

    @classmethod
    def fromCoreCorpus(cls):
        return cls('core').read()

    @classmethod
    def fromLocalCorpus(cls):
        return cls('local').read()

    @classmethod
    def fromVirtualCorpus(cls):
        return cls('virtual').read()

    def read(self, filePath=None):
        '''
        Load self from the file path suggested by the name 
        of this MetadataBundle.
        
        If filePath is None (typical), run self.filePath.
        '''
        timer = common.Timer()
        timer.start()
        if filePath is None:
            filePath = self.filePath
        if not os.path.exists(filePath):
            environLocal.warn('no metadata found for: %s; try building cache with corpus.cacheMetadata("%s")' % (self.name, self.name))
            return
        jst = freezeThaw.JSONThawer(self)
        jst.jsonRead(filePath)
        environLocal.printDebug([
            'MetadataBundle: loading time:', 
            self.name, 
            timer, 
            'md items:', 
            len(self.storage)
            ])
        return self

    def search(self, query, field=None, fileExtensions=None):
        '''
        Perform search, on all stored metadata, permit regular expression 
        matching. 

        ::

            >>> workList = corpus.getWorkList('ciconia')
            >>> metadataBundle = metadata.MetadataBundle()
            >>> metadataBundle.addFromPaths(
            ...     workList,
            ...     useMultiprocessing=False,
            ...     )
            []

        ::

            >>> updateCount = metadataBundle.updateAccessPaths(workList)
            >>> searchResult = metadataBundle.search('cicon', 'composer')
            >>> searchResult
            <music21.metadata.MetadataBundle object at 0x...>

        ::

            >>> len(searchResult)
            1

        ::

            >>> searchResult[0]
            <music21.metadata.MetadataEntry: ciconia_quod_jactatur_xml>

        ::

            >>> searchResult = metadataBundle.search('cicon', 'composer', 
            ...     fileExtensions=['.krn'])
            >>> len(searchResult) # no files in this format
            0

        ::

            >>> searchResult = metadataBundle.search('cicon', 'composer', 
            ...     fileExtensions=['.xml'])
            >>> len(searchResult)  # shouldn't this be 11?
            1   

        '''
        newMetadataBundle = MetadataBundle()
        for key in self.storage:
            metadataEntry = self.storage[key]
            # ignore stub entries
            if metadataEntry.richMetadata is None:
                continue
            if metadataEntry.search(query, field)[0]:
                include = False
                if fileExtensions is not None:
                    for fileExtension in fileExtensions:
                        if metadataEntry.accessPath.endswith(fileExtension):
                            include = True
                            break
                        elif fileExtension.endswith('xml') and \
                            metadataEntry.accessPath.endswith(('mxl', 'mx')):
                            include = True
                            break
                else:
                    include = True
                if include and key not in newMetadataBundle.storage:
                    newMetadataBundle.storage[key] = metadataEntry
        return newMetadataBundle

    def updateAccessPaths(self, pathList):
        r'''

        For each stored Metatadata object, create an entry in the dictionary
        ._accessPaths where each key is a simple version of the corpus name of
        the file and the value is the complete, local file path that returns
        this.

        Uses :meth:`~music21.metadata.MetadataBundle.corpusPathToKey` to
        generate the keys

        The `pathList` parameter is a list of all file paths on the users local
        system. 
        
        ::

            >>> mb = metadata.MetadataBundle()
            >>> mb.addFromPaths(
            ...     corpus.getWorkList('bwv66.6'),
            ...     useMultiprocessing=False,
            ...     )
            []

        ::

            >>> mb.updateAccessPaths(corpus.getWorkList('bwv66.6'))
            2

        ::

            >>> #_DOCS_SHOW print mb._accessPaths
            >>> print r"{u'bach_bwv66_6_mxl': u'D:\\eclipse_dev\\music21base\\music21\\corpus\\bach\\bwv66.6.mxl'}" #_DOCS_HIDE
            {u'bach_bwv66_6_mxl': u'D:\\eclipse_dev\\music21base\\music21\\corpus\\bach\\bwv66.6.mxl'}
        
        A slower (but not too slow test) that should do much more. This is what
        corpus._updateMetadataBundle() does.  Notice that many of our files
        contain multiple scores, so while there are 2,300 files, there are over
        13,000 scores.
        
        ::

            >>> coreCorpusPaths = corpus.getCorePaths()
            >>> #_DOCS_SHOW len(coreCorpusPaths)
            >>> if len(coreCorpusPaths) > 2200: print '2300' #_DOCS_HIDE
            2300

        ::

            >>> mdCoreBundle = metadata.MetadataBundle('core')
            >>> mdCoreBundle.read()
            <music21.metadata.MetadataBundle object at 0x...>

        ::

            >>> updateCount = mdCoreBundle.updateAccessPaths(coreCorpusPaths)
            >>> #_DOCS_SHOW updateCount
            >>> if updateCount > 10000: print '14158' #_DOCS_HIDE
            14158
        
        Note that some scores inside an Opus file may have a number in the key
        that is not present in the path:
        
        ::

            >>> #_DOCS_SHOW mdCoreBundle._accessPaths['essenFolksong_han1_abc_1']
            >>> print r"u'D:\\eclipse_dev\\music21base\\music21\\corpus\\essenFolksong\\han1.abc'" #_DOCS_HIDE
            u'D:\\eclipse_dev\\music21base\\music21\\corpus\\essenFolksong\\han1.abc'

        '''
        import music21
        music21Path = music21.__path__[0]
        # always clear first
        # create a copy to manipulate
        for metadataEntry in self.storage.viewvalues():
            metadataEntry.accessPath = None
        updateCount = 0
        for filePath in pathList:
            # this key may not be valid if it points to an Opus work that
            # has multiple numbers; thus, need to get a stub that can be 
            # used for conversion
            corpusPath = self.corpusPathToKey(filePath)
            accessPath = filePath
            if accessPath.startswith(music21Path):
                accessPath = os.path.join(
                    'music21',
                    os.path.relpath(filePath, music21Path),
                    )
            # a version of the path that may not have a work number
            if corpusPath in self.storage:
                self.storage[corpusPath].accessPath = accessPath
                updateCount += 1
                # get all but last underscore
                corpusPathStub = '_'.join(corpusPath.split('_')[:-1]) 
                for key in self.storage.viewkeys():
                    if key.startswith(corpusPathStub):
                        self.storage[key].accessPath = accessPath
                        updateCount += 1
        return updateCount

    def write(self):
        '''
        Write the JSON storage of all Metadata or 
        RichMetadata contained in this object. 

        TODO: Test!
        '''
        if self.filePath is not None:
            filePath = self.filePath
            environLocal.warn(['MetadataBundle: writing:', filePath])
            jsf = freezeThaw.JSONFreezer(self)
            return jsf.jsonWrite(filePath)
        return self


#-------------------------------------------------------------------------------


class MetadataCacheException(exceptions21.Music21Exception):
    pass


def cacheMetadata(domains=('local', 'core', 'virtual')): 
    '''
    The core cache is all locally-stored corpus files. 
    '''
    from music21 import corpus, metadata

    if not common.isListLike(domains):
        domains = (domains,)

    timer = common.Timer()
    timer.start()

    # store list of file paths that caused an error
    failingFilePaths = []

    domainGetPathsProcedures = {
       'core': corpus.getCorePaths,
       'local': corpus.getLocalPaths,
       'virtual': corpus.getVirtualPaths,
       }

    # the core cache is based on local files stored in music21
    # virtual is on-line
    for domain in domains:
        # the domain passed here becomes the name of the bundle
        # determines the file name of the json bundle
        metadataBundle = metadata.MetadataBundle(domain)
        if domain not in domainGetPathsProcedures:
            raise MetadataCacheException('invalid domain provided: {0}'.format(
                domain))
        if os.path.exists(metadataBundle.filePath):
            metadataBundle.read()
        paths = domainGetPathsProcedures[domain]()
        environLocal.warn(
            'metadata cache: starting processing of paths: {0}'.format(
                len(paths)))
        # returns any paths that failed to load
        failingFilePaths += metadataBundle.addFromPaths(
            paths, printDebugAfter=1) 
        environLocal.warn(
            'cache: writing time: {0} md items: {1}'.format(
                timer, len(metadataBundle.storage)))
        del metadataBundle

    environLocal.warn('cache: final writing time: {0} seconds'.format(timer))
    for failingFilePath in failingFilePaths:
        environLocal.warn('path failed to parse: {0}'.format(failingFilePath))


class MetadataCachingJob(object):
    '''
    Parses one corpus path, and attempts to extract metadata from it:

    ::

        >>> job = metadata.MetadataCachingJob(
        ...     'bach/bwv66.6',
        ...     useCorpus=True,
        ...     )
        >>> job()
        ((<music21.metadata.MetadataEntry: bach_bwv66_6>,), ())
        >>> results = job.getResults()

    '''
    
    ### INITIALIZER ###

    def __init__(self, filePath, jobNumber=0, useCorpus=True):
        self.filePath = filePath
        self.filePathErrors = []
        self.jobNumber = int(jobNumber)
        self.results = []
        self.useCorpus = bool(useCorpus)

    ### SPECIAL METHODS ###

    def __call__(self):
        import gc
        self.results = []
        parsedObject = self._parseFilePath()
        if parsedObject is not None:
            if 'Opus' in parsedObject.classes:
                self._parseOpus(parsedObject)
            else:
                self._parseNonOpus(parsedObject)
        del parsedObject
        gc.collect()
        return self.getResults(), self.getErrors()

    ### PRIVATE METHODS ###

    def _parseFilePath(self):
        from music21 import converter
        from music21 import corpus
        parsedObject = None
        try:
            if self.useCorpus is False:
                parsedObject = converter.parse(
                    self.filePath, forceSource=True)
            else:
                parsedObject = corpus.parse(
                    self.filePath, forceSource=True)
        except Exception, e:
            environLocal.warn('parse failed: {0}, {1}'.format(
                self.filePath, str(e)))
            self.filePathErrors.append(self.filePath)
        return parsedObject

    def _parseNonOpus(self, parsedObject):
        try:
            corpusPath = MetadataBundle.corpusPathToKey(self.filePath)
            metadata = parsedObject.metadata
            if metadata is not None:
                richMetadata = RichMetadata()
                richMetadata.merge(metadata)
                richMetadata.update(parsedObject) # update based on Stream
                environLocal.printDebug(
                    'updateMetadataCache: storing: {0}'.format(corpusPath))
                metadataEntry = MetadataEntry(
                    cacheTime=time.time(),
                    filePath=self.filePath,
                    richMetadata=richMetadata,
                    )
            else:
                environLocal.warn(
                    'addFromPaths: got stream without metadata, '
                    'creating stub: {0}'.format(
                        os.path.relpath(self.filePath)))
                metadataEntry = MetadataEntry(
                    cacheTime=time.time(),
                    filePath=self.filePath,
                    richMetadata=None,
                    )
            self.results.append(metadataEntry)
        except Exception:
            environLocal.warn('Had a problem with extracting metadata '
            'for {0}, piece ignored'.format(self.filePath))
            traceback.print_exc()

    def _parseOpus(self, parsedObject):
        # need to get scores from each opus?
        # problem here is that each sub-work has metadata, but there
        # is only a single source file
        try:
            for scoreNumber, score in enumerate(parsedObject.scores):
                self._parseOpusScore(score, scoreNumber)
                del score # for memory conservation
        except Exception as exception:
            environLocal.warn(
                'Had a problem with extracting metadata for score {0} '
                'in {1}, whole opus ignored: {2}'.format(
                    scoreNumber, self.filePath, str(exception)))
            traceback.print_exc()
        else:
            # Create a dummy metadata entry, representing the entire opus.
            # This lets the metadata bundle know it has already processed this
            # entire opus on the next cache update.
            metadataEntry = MetadataEntry(
                cacheTime=time.time(),
                filePath=self.filePath,
                richMetadata=None,
                )
            self.results.append(metadataEntry)

    def _parseOpusScore(self, score, scoreNumber):
        try:
            metadata = score.metadata
            # updgrade metadata to richMetadata
            richMetadata = RichMetadata()
            richMetadata.merge(metadata)
            richMetadata.update(score) # update based on Stream
            if metadata is None or metadata.number is None:
                environLocal.warn(
                    'addFromPaths: got Opus that contains '
                    'Streams that do not have work numbers: '
                    '{0}'.format(self.filePath))
            else:
                # update path to include work number
                corpusPath = MetadataBundle.corpusPathToKey(
                    self.filePath, 
                    number=metadata.number,
                    )
                environLocal.printDebug(
                    'addFromPaths: storing: {0}'.format(
                        corpusPath))
                metadataEntry = MetadataEntry(
                    cacheTime=time.time(),
                    filePath=self.filePath,
                    number=scoreNumber,
                    richMetadata=richMetadata,
                    )
                self.results.append(metadataEntry)
        except Exception as exception:
            environLocal.warn(
                'Had a problem with extracting metadata '
                'for score {0} in {1}, whole opus ignored: '
                '{2}'.format(
                    scoreNumber, self.filePath, str(exception)))
            traceback.print_exc()

    ### PUBLIC METHODS ###

    def getErrors(self):
        return tuple(self.filePathErrors)

    def getResults(self):
        return tuple(self.results)


class JobProcessor(object):

    ### PUBLIC METHODS ###

    @staticmethod
    def process_parallel(jobs, processCount=None):
        processCount = processCount or multiprocessing.cpu_count() - 1
        if processCount < 1:
            processCount = 1
        remainingJobs = len(jobs)
        results = []
        filePathErrors = []
        job_queue = multiprocessing.JoinableQueue()
        result_queue = multiprocessing.Queue()
        workers = [WorkerProcess(job_queue, result_queue) 
            for i in range(processCount)]
        for worker in workers:
            worker.start()
        if jobs:
            for job in jobs:
                job_queue.put(pickle.dumps(job, protocol=0))
            for i in xrange(len(jobs)):
                job = pickle.loads(result_queue.get())
                results = job.getResults()
                errors = job.getErrors()
                remainingJobs -= 1
                JobProcessor.report(
                    len(jobs),
                    remainingJobs,
                    job.filePath,
                    len(filePathErrors),
                    )
                yield results, errors
        for worker in workers:
            job_queue.put(None)
        job_queue.join()
        result_queue.close()
        job_queue.close()
        for worker in workers:
            worker.join()
        raise StopIteration

    @staticmethod
    def process_serial(jobs):
        remainingJobs = len(jobs)
        results = []
        filePathErrors = []
        for i, job in enumerate(jobs):
            results, errors = job()
            remainingJobs -= 1
            JobProcessor.report(
                len(jobs),
                remainingJobs,
                job.filePath,
                len(filePathErrors),
                )
            yield results, errors
        raise StopIteration

    @staticmethod
    def report(totalJobs, remainingJobs, filePath, filePathErrorCount):
        message = 'updated {0} of {1} files; ' \
            'total errors: {2} ... last file: {3}'.format(
                totalJobs - remainingJobs,
                totalJobs,
                filePathErrorCount,
                os.path.relpath(filePath),
                )
        environLocal.warn(message)


class WorkerProcess(multiprocessing.Process):
    
    ### INITIALIZER ###

    def __init__(self, job_queue, result_queue):
        multiprocessing.Process.__init__(self)
        self.job_queue = job_queue
        self.result_queue = result_queue
        
    ### PUBLIC METHODS ###

    def run(self):
        while True:
            job = self.job_queue.get()
            # "Poison Pill" causes worker shutdown:
            if job is None:
                self.job_queue.task_done()
                break
            job = pickle.loads(job)
            job()
            self.job_queue.task_done()
            self.result_queue.put(pickle.dumps(job, protocol=0))
        return


#-------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testMetadataLoadCorpus(self):
        from music21.musicxml import xmlHandler
        from music21.musicxml import testFiles as mTF
        from music21.musicxml import fromMxObjects

        d = xmlHandler.Document()
        d.read(mTF.mozartTrioK581Excerpt) #@UndefinedVariable
        mxScore = d.score # get the mx score directly
        md = fromMxObjects.mxScoreToMetadata(mxScore)

        self.assertEqual(md.movementNumber, '3')
        self.assertEqual(md.movementName, 'Menuetto (Excerpt from Second Trio)')
        self.assertEqual(md.title, 'Quintet for Clarinet and Strings')
        self.assertEqual(md.number, 'K. 581')
        # get contributors directly from Metadata interface
        self.assertEqual(md.composer, 'Wolfgang Amadeus Mozart')

        d.read(mTF.binchoisMagnificat) # @UndefinedVariable
        mxScore = d.score # get the mx score directly
        md = fromMxObjects.mxScoreToMetadata(mxScore)
        self.assertEqual(md.composer, 'Gilles Binchois')

    def testJSONSerializationMetadata(self):
        from music21.musicxml import xmlHandler
        from music21.musicxml import fromMxObjects
        from music21.musicxml import testFiles
        from music21 import metadata # need to not be local...

        md = metadata.Metadata(title='Concerto in F', date='2010', composer='Frank')
        #environLocal.printDebug([str(md.json)])
        self.assertEqual(md.composer, 'Frank')

        #md.jsonPrint()

        mdNew = metadata.Metadata()
        
        jsonStr = freezeThaw.JSONFreezer(md).json
        freezeThaw.JSONThawer(mdNew).json = jsonStr

        self.assertEqual(mdNew.date, '2010/--/--')
        self.assertEqual(mdNew.composer, 'Frank')

        self.assertEqual(mdNew.title, 'Concerto in F')

        # test getting meta data from an imported source

        d = xmlHandler.Document()
        d.read(testFiles.mozartTrioK581Excerpt) # @UndefinedVariable
        mxScore = d.score # get the mx score directly

        md = fromMxObjects.mxScoreToMetadata(mxScore)

        self.assertEqual(md.movementNumber, '3')
        self.assertEqual(md.movementName, 'Menuetto (Excerpt from Second Trio)')
        self.assertEqual(md.title, 'Quintet for Clarinet and Strings')
        self.assertEqual(md.number, 'K. 581')
        self.assertEqual(md.composer, 'Wolfgang Amadeus Mozart')

        # convert to json and see if data is still there
        #md.jsonPrint()
        mdNew = metadata.Metadata()

        jsonStr = freezeThaw.JSONFreezer(md).json
        freezeThaw.JSONThawer(mdNew).json = jsonStr

        self.assertEqual(mdNew.movementNumber, '3')
        self.assertEqual(mdNew.movementName, 'Menuetto (Excerpt from Second Trio)')
        self.assertEqual(mdNew.title, 'Quintet for Clarinet and Strings')
        self.assertEqual(mdNew.number, 'K. 581')
        self.assertEqual(mdNew.composer, 'Wolfgang Amadeus Mozart')

    def testLoadRichMetadata(self):
        from music21 import corpus
        from music21 import metadata # need fully qualified

        s = corpus.parse('jactatur')
        self.assertEqual(s.metadata.composer, 'Johannes Ciconia')

        rmd = metadata.RichMetadata()
        rmd.merge(s.metadata)

        self.assertEqual(rmd.composer, 'Johannes Ciconia')
        # update rmd with stream
        rmd.update(s)

        self.assertEqual(rmd.keySignatureFirst, '<music21.key.KeySignature of 1 flat, mode major>')

        self.assertEqual(str(rmd.timeSignatureFirst), '2/4')

        #rmd.jsonPrint()
        rmdNew = metadata.RichMetadata()

        jsonStr = freezeThaw.JSONFreezer(rmd).json
        freezeThaw.JSONThawer(rmdNew).json = jsonStr
        
        self.assertEqual(rmdNew.composer, 'Johannes Ciconia')

        self.assertEqual(str(rmdNew.timeSignatureFirst), '2/4')
        self.assertEqual(str(rmdNew.keySignatureFirst), '<music21.key.KeySignature of 1 flat, mode major>')

#         self.assertEqual(rmd.pitchLowest, 55)
#         self.assertEqual(rmd.pitchHighest, 65)
#         self.assertEqual(str(rmd.ambitus), '<music21.interval.Interval m7>')

        s = corpus.parse('bwv66.6')
        rmd = metadata.RichMetadata()
        rmd.merge(s.metadata)

        rmd.update(s)
        self.assertEqual(str(rmd.keySignatureFirst), '<music21.key.KeySignature of 3 sharps, mode minor>')
        self.assertEqual(str(rmd.timeSignatureFirst), '4/4')

        jsonStr = freezeThaw.JSONFreezer(rmd).json
        freezeThaw.JSONThawer(rmdNew).json = jsonStr

        self.assertEqual(str(rmdNew.timeSignatureFirst), '4/4')
        self.assertEqual(str(rmdNew.keySignatureFirst), '<music21.key.KeySignature of 3 sharps, mode minor>')

        # test that work id values are copied
        o = corpus.parse('essenFolksong/teste')
        self.assertEqual(len(o), 8)

        s = o.getScoreByNumber(4)
        self.assertEqual(s.metadata.localeOfComposition, 'Asien, Ostasien, China, Sichuan')

        rmd = metadata.RichMetadata()
        rmd.merge(s.metadata)
        rmd.update(s)

        self.assertEqual(rmd.localeOfComposition, 'Asien, Ostasien, China, Sichuan')

    def testMetadataSearch(self):
        from music21 import corpus
        s = corpus.parse('ciconia')
        self.assertEqual(s.metadata.search('quod', 'title'), (True, 'title'))
        self.assertEqual(s.metadata.search('qu.d', 'title'), (True, 'title'))
        self.assertEqual(s.metadata.search(re.compile('(.*)canon(.*)')), (True, 'title'))

    def testRichMetadataA(self):
        from music21 import corpus, metadata

        s = corpus.parse('bwv66.6')
        rmd = metadata.RichMetadata()
        rmd.merge(s.metadata)
        rmd.update(s)

        self.assertEqual(rmd.noteCount, 165)
        self.assertEqual(rmd.quarterLength, 36.0)
        versionRepr = repr(list(base.VERSION))
        
        jsonStr = freezeThaw.JSONFreezer(rmd).json

        self.assertEqual(jsonStr, '{"__attr__": {"_urls": [], "quarterLength": 36.0, "noteCount": 165, "_contributors": [], "timeSignatureFirst": "4/4", "keySignatureFirst": "<music21.key.KeySignature of 3 sharps, mode minor>", "_workIds": {"movementName": {"__attr__": {"_data": "bwv66.6.mxl"}, "__class__": "music21.metadata.Text"}}}, "__version__": ' + versionRepr + ', "__class__": "music21.metadata.RichMetadata"}')


#-------------------------------------------------------------------------------
            

_DOC_ORDER = (
    Metadata, 
    )


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof

