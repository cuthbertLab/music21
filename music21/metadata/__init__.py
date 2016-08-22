# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         metadata.py
# Purpose:      music21 classes for representing score and work meta-data
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010, 2012 Michael Scott Cuthbert and the music21
#               Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------
'''
Classes and functions for creating and processing metadata associated with
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

>>> s = stream.Score()
>>> p = stream.Part()
>>> m = stream.Measure()
>>> m.append(note.Note())
>>> p.append(m)
>>> s.append(p)
>>> s.insert(0, metadata.Metadata())
>>> s.metadata.title = 'title'
>>> s.metadata.composer = 'composer'
>>> #_DOCS_SHOW s.show()

.. image:: images/moduleMetadata-01.*
    :width: 600

'''
from collections import OrderedDict
import os
import re
import unittest

from music21 import base
from music21 import common
from music21 import freezeThaw
from music21 import exceptions21

from music21.ext import six

from music21.metadata import bundles
from music21.metadata import caching
from music21.metadata import primitives
from music21.metadata.primitives import (Date, DateSingle, DateRelative, DateBetween,
                                         DateSelection, Text, Contributor, Creator,
                                         Imprint, Copyright)

from music21.metadata import testMetadata 
#------------------------------------------------------------------------------


from music21 import environment
environLocal = environment.Environment(os.path.basename(__file__))


#------------------------------------------------------------------------------


class Metadata(base.Music21Object):
    r'''
    Metadata represent data for a work or fragment, including title, composer,
    dates, and other relevant information.

    Metadata is a :class:`~music21.base.Music21Object` subclass, meaing that it
    can be positioned on a Stream by offset and have a
    :class:`~music21.duration.Duration`.

    In many cases, each Stream will have a single Metadata object at the zero
    offset position.

    >>> md = metadata.Metadata(title='Concerto in F')
    >>> md.title
    'Concerto in F'

    >>> md = metadata.Metadata(otl='Concerto in F') # can use abbreviations
    >>> md.title
    'Concerto in F'

    >>> md.setWorkId('otl', 'Rhapsody in Blue')
    >>> md.otl
    'Rhapsody in Blue'

    >>> md.title
    'Rhapsody in Blue'

    >>> md.composer = 'Gershwin, George'

    These are used by .search() methods to determine what attributes are
    made available by default.

    >>> md.searchAttributes
    ('alternativeTitle', 'composer', 'date', 'localeOfComposition', 
     'movementName', 'movementNumber', 'number', 'opusNumber', 'title')
    
    All contributors are stored in a .contributors list:
     
    >>> md.contributors
    [<music21.metadata.primitives.Contributor composer:Gershwin, George>]
    '''

    ### CLASS VARIABLES ###

    classSortOrder = -30

    # add more as properties/import exists
    searchAttributes = (
        'alternativeTitle',
        'composer',
        'date',
        'localeOfComposition',
        'movementName',
        'movementNumber',
        'number',
        'opusNumber',
        'title',
        )

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

    workIdAbbreviationDict = {
        'gaw': 'associatedWork',
        'gco': 'collectionDesignation',
        'gtl': 'groupTitle',
        'oac': 'actNumber',
        'oco': 'commission',
        'ocy': 'countryOfComposition',
        'ode': 'dedication',
        'omd': 'movementName',
        'omv': 'movementNumber',
        'onm': 'number',
        'opc': 'localeOfComposition',  # origin in abc
        'opr': 'parentTitle',
        'ops': 'opusNumber',
        'osc': 'sceneNumber',
        'ota': 'alternativeTitle',
        'otl': 'title',
        'otp': 'popularTitle',
        'ovm': 'volume',
        'txl': 'textLanguage',
        'txo': 'textOriginalLanguage',
        }

    workIdLookupDict = {}
    for key, value in workIdAbbreviationDict.items():
        workIdLookupDict[value.lower()] = key

    ### INITIALIZER ###

    def __init__(self, *args, **keywords):
        base.Music21Object.__init__(self)

        # a list of Contributor objects
        # there can be more than one composer, or any other combination
        self.contributors = [] # use addContributor to add.
        self._date = None

        # store one or more URLs from which this work came; this could
        # be local file paths or otherwise
        self._urls = []

        # TODO: need a specific object for copyright and imprint
        self._imprint = None
        self._copyright = None

        # a dictionary of Text elements, where keys are work id strings
        # all are loaded with None by default
        self._workIds = OrderedDict()
        for abbreviation, workId in self.workIdAbbreviationDict.items():
            #abbreviation = workIdToAbbreviation(id)
            if workId in keywords:
                self._workIds[workId] = Text(keywords[workId])
            elif abbreviation in keywords:
                self._workIds[workId] = Text(keywords[abbreviation])
            else:
                self._workIds[workId] = None

        # search for any keywords that match attributes
        # these are for direct Contributor access, must have defined
        # properties
        for attr in ['composer', 'date', 'title']:
            if attr in keywords:
                setattr(self, attr, keywords[attr])

    ### SPECIAL METHODS ###
    def all(self, skipContributors=False):
        '''
        Returns all values (as strings) stored in this metadata as a sorted list of tuples.
        
        >>> c = corpus.parse('corelli/opus3no1/1grave')
        >>> c.metadata.all()
        [('arranger', 'Michael Scott Cuthbert'), 
         ('composer', 'Arcangelo Corelli'), 
         ('movementName', 'Sonata da Chiesa, No. I (opus 3, no. 1)')]

        Skip contributors is there to help with musicxml parsing -- there's no reason for it
        except that we haven't exposed enough functionality yet:
        
        >>> c.metadata.date = metadata.DateRelative('1689', 'onOrBefore')
        >>> c.metadata.localeOfComposition = 'Rome'
        >>> c.metadata.all(skipContributors=True)
        [('date', '1689/--/-- or earlier'), 
         ('localeOfComposition', 'Rome'), 
         ('movementName', 'Sonata da Chiesa, No. I (opus 3, no. 1)')]
        '''
        # pylint: disable=undefined-variable
        allOut = []
        for wid in self._workIds.keys():
            val = self._workIds[wid]
            if val is None:
                continue
            if six.PY3:
                t = (str(wid), str(val))
            else:
                try:
                    t = (str(wid), unicode(val)) # @UndefinedVariable
                except UnicodeDecodeError as ude:
                    print(val, repr(val), ude)
            allOut.append(t)
        if not skipContributors:
            for contri in self.contributors:
                for n in contri._names:
                    if six.PY3:
                        t = (str(contri.role), str(n))
                    else:
                        t = (str(contri.role), unicode(n)) # @UndefinedVariable
                    allOut.append(t)
        if self._date is not None:
            if six.PY3:
                t = ('date', str(self._date))
            else:
                t = ('date', unicode(self._date)) # @UndefinedVariable
            allOut.append(t)
        if self._copyright is not None:
            if six.PY3:
                t = ('copyright', str(self._copyright))
            else:
                t = ('copyright', unicode(self._copyright)) # @UndefinedVariable
            allOut.append(t)
            
        
        return sorted(allOut)

    def __getattr__(self, name):
        r'''
        Utility attribute access for attributes that do not yet have property
        definitions.
        '''
        match = None
        for abbreviation, workId in self.workIdAbbreviationDict.items():
        #for id in WORK_IDS:
            #abbreviation = workIdToAbbreviation(id)
            if name == workId:
                match = workId
                break
            elif name == abbreviation:
                match = workId
                break
        if match is None:
            raise AttributeError('object has no attribute: %s' % name)
        result = self._workIds[match]
        # always return string representation for now
        return str(result)

    ### PUBLIC METHODS ###

    @staticmethod
    def abbreviationToWorkId(abbreviation):
        '''Get work id abbreviations.

        >>> metadata.Metadata.abbreviationToWorkId('otl')
        'title'

        >>> for id in metadata.Metadata.workIdAbbreviationDict.keys():
        ...    result = metadata.Metadata.abbreviationToWorkId(id)
        ...

        '''
        abbreviation = abbreviation.lower()
        if abbreviation not in Metadata.workIdAbbreviationDict:
            raise exceptions21.MetadataException(
                'no such work id: %s' % abbreviation)
        return Metadata.workIdAbbreviationDict[abbreviation]

    def addContributor(self, c):
        r'''
        Assign a :class:`~music21.metadata.Contributor` object to this
        Metadata.

        >>> md = metadata.Metadata(title='Gaelic Symphony')
        >>> c = metadata.Contributor()
        >>> c.name = 'Beach, Amy'
        >>> c.role = 'composer'
        >>> md.addContributor(c)
        >>> md.composer
        'Beach, Amy'

        Add maiden name as an alternative composer name:

        >>> md.composer = 'Cheney, Amy Marcy'
        >>> md.composers
        ['Beach, Amy', 'Cheney, Amy Marcy']

        '''
        if not isinstance(c, Contributor):
            raise exceptions21.MetadataException(
                'supplied object is not a Contributor: %s' % c)
        self.contributors.append(c)

    def getContributorsByRole(self, value):
        r'''
        Return a :class:`~music21.metadata.Contributor` if defined for a
        provided role.

        >>> md = metadata.Metadata(title='Third Symphony')

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

        >>> c2 = metadata.Contributor()
        >>> c2.name = 'Beth Hadley'
        >>> md.addContributor(c2)
        >>> noRoleList = md.getContributorsByRole(None)
        >>> len(noRoleList)
        1

        >>> noRoleList[0].role
        >>> noRoleList[0].name
        'Beth Hadley'
        '''
        result = []  # there may be more than one per role
        for c in self.contributors:
            if c.role == value:
                result.append(c)
        if result:
            return result
        else:
            return None

    def search(self, query, field=None):
        r'''
        Search one or all fields with a query, given either as a string or a
        regular expression match.

        >>> md = metadata.Metadata()
        >>> md.composer = 'Joplin, Scott'
        >>> md.title = 'Maple Leaf Rag'

        >>> md.search(
        ...     'joplin',
        ...     field='composer',
        ...     )
        (True, 'composer')

        Note how the incomplete field name in the following example is still
        matched:

        >>> md.search(
        ...     'joplin',
        ...     field='compos',
        ...     )
        (True, 'composer')

        These don't work (Richard W. didn't have the rhythm...)

        >>> md.search(
        ...     'Wagner',
        ...     field='composer',
        ...     )
        (False, None)

        >>> md.search('Wagner')
        (False, None)

        >>> md.search('leaf')
        (True, 'title')

        >>> md.search(
        ...     'leaf',
        ...     field='composer',
        ...     )
        (False, None)

        >>> md.search(
        ...     'leaf',
        ...     field='title',
        ...     )
        (True, 'title')

        >>> md.search('leaf|entertainer')
        (True, 'title')

        >>> md.search('opl(.*)cott')
        (True, 'composer')
        '''
        valueFieldPairs = []
        if field is not None:
            match = False
            try:
                value = getattr(self, field)
                valueFieldPairs.append((value, field))
                match = True
            except AttributeError:
                pass
            if not match:
                for searchAttribute in self.searchAttributes:
                    #environLocal.printDebug(['comparing fields:', f, field])
                    # look for partial match in all fields
                    if field.lower() in searchAttribute.lower():
                        value = getattr(self, searchAttribute)
                        valueFieldPairs.append((value, searchAttribute))
                        match = True
                        break
            # if cannot find a match for any field, return
            if not match:
                return False, None
        else:  # get all fields
            for field in self.searchAttributes:
                value = getattr(self, field)
                valueFieldPairs.append((value, field))
        # for now, make all queries strings
        # ultimately, can look for regular expressions by checking for
        # .search
        useRegex = False
        if hasattr(query, 'search'):
            useRegex = True
            reQuery = query  # already compiled
        # look for regex characters
        elif (isinstance(query, six.string_types)
              and any(character in query for character in '*.|+?{}')):
            useRegex = True
            reQuery = re.compile(query, flags=re.I)
        if useRegex:
            for value, field in valueFieldPairs:
                # re.I makes case insensitive
                if isinstance(value, six.string_types):
                    match = reQuery.search(value)
                    if match is not None:
                        return True, field
        elif callable(query):
            for value, field in valueFieldPairs:
                if query(value):
                    return True, field
        else:
            for value, field in valueFieldPairs:
                if isinstance(value, six.string_types):
                    query = str(query)
                    if query.lower() in value.lower():
                        return True, field
                elif query == value:
                    return True, field
        return False, None

    def setWorkId(self, idStr, value):
        r'''
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

        >>> md = metadata.Metadata(title='Quartet')
        >>> md.title
        'Quartet'

        >>> md.setWorkId('otl', 'Trio')
        >>> md.title
        'Trio'

        >>> md.setWorkId('sdf', None)
        Traceback (most recent call last):
        music21.exceptions21.MetadataException: no work id available with id: sdf
        '''
        idStr = idStr.lower()
        match = False
        for abbreviation, workId in self.workIdAbbreviationDict.items():
        #for id in WORK_IDS:
            #abbreviation = workIdToAbbreviation(id)
            if workId.lower() == idStr:
                self._workIds[workId] = Text(value)
                match = True
                break
            elif abbreviation == idStr:
                self._workIds[workId] = Text(value)
                match = True
                break
        if not match:
            raise exceptions21.MetadataException(
                'no work id available with id: %s' % idStr)

    @staticmethod
    def workIdToAbbreviation(value):
        '''Get a work abbreviation from a string representation.

        >>> metadata.Metadata.workIdToAbbreviation('localeOfComposition')
        'opc'

        >>> for n in metadata.Metadata.workIdAbbreviationDict.values():
        ...     result = metadata.Metadata.workIdToAbbreviation(n)
        ...
        '''
        # NOTE: this is a performance critical function
        try:
            # try direct access, where keys are already lower case
            return Metadata.workIdLookupDict[value]
        except KeyError:
            pass

        # slow approach
        for workId in Metadata.workIdAbbreviationDict.keys():
            if value.lower() == Metadata.workIdAbbreviationDict[workId].lower():
                return workId
        raise exceptions21.MetadataException(
            'no such work id: %s' % value)

    ### PUBLIC PROPERTIES ###

    @property
    def alternativeTitle(self):
        r'''
        Get or set the alternative title.

        >>> md = metadata.Metadata(popularTitle='Eroica')
        >>> md.alternativeTitle = 'Heroic Symphony'
        >>> md.alternativeTitle
        'Heroic Symphony'
        '''
        result = self._workIds['alternativeTitle']
        if result is not None:
            return str(result)

    @alternativeTitle.setter
    def alternativeTitle(self, value):
        self._workIds['alternativeTitle'] = Text(value)

    @property
    def composer(self):
        r'''
        Get or set the composer of this work. More than one composer may be
        specified.

        The composer attribute does not live in Metadata, but creates a
        :class:`~music21.metadata.Contributor` object in the .contributors
        object.

        >>> md = metadata.Metadata(
        ...     title='Third Symphony',
        ...     popularTitle='Eroica',
        ...     composer='Beethoven, Ludwig van',
        ...     )
        >>> md.composer
        'Beethoven, Ludwig van'
        '''
        result = self.getContributorsByRole('composer')
        if result is not None:
            # get just the name of the first composer
            return str(result[0].name)

    @composer.setter
    def composer(self, value):
        c = Contributor()
        c.name = value
        c.role = 'composer'
        self.contributors.append(c)

    @property
    def composers(self):
        r'''
        Get a list of all :class:`~music21.metadata.Contributor` objects
        defined as composer of this work.
        '''
        result = self.getContributorsByRole('composer')
        if result is not None:
            # get just the name of the first composer
            return [x.name for x in result]

    @property
    def date(self):
        r'''
        Get or set the date of this work as one of the following date
        objects:

        :class:`~music21.metadata.DateSingle`,
        :class:`~music21.metadata.DateRelative`,
        :class:`~music21.metadata.DateBetween`,
        :class:`~music21.metadata.DateSelection`,

        >>> md = metadata.Metadata(
        ...     title='Third Symphony',
        ...     popularTitle='Eroica',
        ...     composer='Beethoven, Ludwig van',
        ...     )
        >>> md.date = '2010'
        >>> md.date
        '2010/--/--'

        >>> md.date = metadata.DateBetween(['2009/12/31', '2010/1/28'])
        >>> md.date
        '2009/12/31 to 2010/01/28'
        '''
        return str(self._date)

    @date.setter
    def date(self, value):
        # all inherit date single
        if isinstance(value, DateSingle):
            self._date = value
        else:
            # assume date single; could be other sublcass
            ds = DateSingle(value)
            self._date = ds

    @property
    def localeOfComposition(self):
        r'''
        Get or set the locale of composition, or origin, of the work.
        '''
        result = self._workIds['localeOfComposition']
        if result is not None:
            return str(result)

    @localeOfComposition.setter
    def localeOfComposition(self, value):
        self._workIds['localeOfComposition'] = Text(value)

    @property
    def movementName(self):
        r'''
        Get or set the movement title.

        Note that a number of pieces from various MusicXML datasets have
        the piece title as the movement title. For instance, the Bach
        Chorales, since they are technically movements of larger cantatas.

        '''
        result = self._workIds['movementName']
        if result is not None:
            return str(result)

    @movementName.setter
    def movementName(self, value):
        self._workIds['movementName'] = Text(value)

    @property
    def movementNumber(self):
        r'''
        Get or set the movement number.
        '''
        result = self._workIds['movementNumber']
        if result is not None:
            return str(result)

    @movementNumber.setter
    def movementNumber(self, value):
        self._workIds['movementNumber'] = Text(value)

    @property
    def number(self):
        r'''
        Get or set the number of the work within a collection of pieces.
        (for instance, the number within a collection of ABC files)
        '''
        result = self._workIds['number']
        if result is not None:
            return str(result)

    @number.setter
    def number(self, value):
        self._workIds['number'] = Text(value)

    @property
    def opusNumber(self):
        r'''
        Get or set the opus number.
        '''
        result = self._workIds['opusNumber']
        if result is not None:
            return str(result)

    @opusNumber.setter
    def opusNumber(self, value):
        self._workIds['opusNumber'] = Text(value)

    @property
    def title(self):
        r'''
        Get the title of the work, or the next-matched title string
        available from a related parameter fields.

        >>> md = metadata.Metadata(title='Third Symphony')
        >>> md.title
        'Third Symphony'

        >>> md = metadata.Metadata(popularTitle='Eroica')
        >>> md.title
        'Eroica'

        >>> md = metadata.Metadata(
        ...     title='Third Symphony',
        ...     popularTitle='Eroica',
        ...     )
        >>> md.title
        'Third Symphony'

        >>> md.popularTitle
        'Eroica'

        >>> md.otp
        'Eroica'
        '''
        searchId = (
            'title',
            'popularTitle',
            'alternativeTitle',
            'movementName',
            )
        result = None
        for key in searchId:
            result = self._workIds[key]
            if result is not None:  # get first matched
                # get a string from this Text object
                # get with normalized articles
                return self._workIds[key].getNormalizedArticle()

    @title.setter
    def title(self, value):
        self._workIds['title'] = Text(value)



#------------------------------------------------------------------------------


class RichMetadata(Metadata):
    r'''
    RichMetadata adds to Metadata information about the contents of the Score
    it is attached to. TimeSignature, KeySignature and related analytical is
    stored.  RichMetadata are generally only created in the process of creating
    stored JSON metadata.

    >>> richMetadata = metadata.RichMetadata(title='Concerto in F')
    >>> richMetadata.title
    'Concerto in F'

    >>> richMetadata.keySignatureFirst = key.KeySignature(-1)
    >>> 'keySignatureFirst' in richMetadata.searchAttributes
    True
    >>> richMetadata.searchAttributes
    ('alternativeTitle', 'ambitus', 'composer', 'date', 
     'keySignatureFirst', 'keySignatures', 'localeOfComposition', 
     'movementName', 'movementNumber', 'noteCount', 'number', 
     'opusNumber', 'pitchHighest', 'pitchLowest', 'quarterLength', 
     'tempoFirst', 'tempos', 'timeSignatureFirst', 'timeSignatures', 'title')


    '''

    ### CLASS VARIABLES ###

    searchAttributes = tuple(sorted(Metadata.searchAttributes + (
        'ambitus',
        'keySignatureFirst',
        'keySignatures',
        'noteCount',
        'pitchHighest',
        'pitchLowest',
        'quarterLength',
        'tempoFirst',
        'tempos',
        'timeSignatureFirst',
        'timeSignatures',
        )))

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

    ### PUBLIC METHODS ###

    def merge(self, other, favorSelf=False):
        r'''
        Given another Metadata or RichMetadata object, combine
        all attributes and return a new object.

        >>> md = metadata.Metadata(title='Concerto in F')
        >>> md.title
        'Concerto in F'

        >>> richMetadata = metadata.RichMetadata()
        >>> richMetadata.merge(md)
        >>> richMetadata.title
        'Concerto in F'

        '''
        # specifically name attributes to copy, as do not want to get all
        # Metadata is a m21 object
        localNames = [
            'contributors', '_date', '_urls', '_imprint', '_copyright',
            '_workIds',
            ]
        environLocal.printDebug(['RichMetadata: calling merge()'])
        for name in localNames:
            localValue = getattr(self, name)
            # if not set, and favoring self, then only then set
            # this will not work on dictionaries
            if localValue is not None and favorSelf:
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
        r'''
        Given a Stream object, update attributes with stored objects.
        '''
        from music21 import key
        from music21 import meter
        from music21 import tempo

        environLocal.printDebug(['RichMetadata: update(): start'])

        flat = streamObj.flat.sorted

        self.keySignatureFirst = None
        self.keySignatures = []
        self.tempoFirst = None
        self.tempos = []
        self.timeSignatureFirst = None
        self.timeSignatures = []

        # We combine element searching into a single loop to prevent
        # multiple traversals of the flattened stream.
        for element in flat:
            if isinstance(element, meter.TimeSignature):
                ratioString = element.ratioString
                if ratioString not in self.timeSignatures:
                    self.timeSignatures.append(ratioString)
            elif isinstance(element, key.KeySignature):
                keySignatureString = repr(element) # repr not str for key.Key objects
                if keySignatureString not in self.keySignatures:
                    self.keySignatures.append(keySignatureString)
            elif isinstance(element, tempo.TempoIndication):
                tempoIndicationString = str(element)
                if tempoIndicationString not in self.tempos:
                    self.tempos.append(tempoIndicationString)

        if len(self.timeSignatures):
            self.timeSignatureFirst = self.timeSignatures[0]
        if len(self.keySignatures):
            self.keySignatureFirst = self.keySignatures[0]
        if len(self.tempos):
            self.tempoFirst = self.tempos[0]

#        for element in flat:
#            pitches = ()
#            if isinstance(element, note.Note):
#                pitches = (element.pitch,)
#            elif isinstance(element, chord.Chord):
#                pitches = element.pitches
#            for pitch in pitches:
#                if self.pitchHighest is None:
#                    self.pitchHighest = pitch
#                if self.pitchLowest is None:
#                    self.pitchLowest = pitch
#                if pitch.ps < self.pitchLowest.ps:
#                    self.pitchLowest = pitch
#                elif self.pitchHighest.ps < pitch.ps:
#                    self.pitchHighest = pitch
#        self.pitchLowest = str(self.pitchLowest)
#        self.pitchHighest = str(self.pitchHighest)

        self.noteCount = len(flat.notesAndRests)
        self.quarterLength = flat.highestTime

# commenting out temporarily due to memory error
# with corpus/beethoven/opus132.xml
#         # must be a method-level import

#         environLocal.printDebug(
#             ['RichMetadata: update(): calling discrete.Ambitus(streamObj)'])
#
        from music21.analysis import discrete
        self.ambitus = None
        self.pitchHighest = None
        self.pitchLowest = None
        analysisObject = discrete.Ambitus(streamObj)
        psRange = analysisObject.getPitchSpan(streamObj)
        if psRange is not None:  # may be none if no pitches are stored
            # presently, these are numbers; convert to pitches later
            self.pitchLowest = str(psRange[0])
            self.pitchHighest = str(psRange[1])
        self.ambitus = analysisObject.getSolution(streamObj)

#------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
    

#------------------------------------------------------------------------------


_DOC_ORDER = ()

__all__ = [
    'Metadata',
    'RichMetadata',
    ]

if __name__ == "__main__":
    import music21
    music21.mainTest(Test)


#------------------------------------------------------------------------------
