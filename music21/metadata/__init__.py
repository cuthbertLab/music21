# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         metadata.py
# Purpose:      music21 classes for representing score and work metadata
#
# Authors:      Christopher Ariza
#               Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2010, 2012 Michael Scott Asato Cuthbert and the music21
#               Project
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
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
>>> s.metadata['title'] = 'title'
>>> s.metadata['composer'] = 'composer'
>>> #_DOCS_SHOW s.show()

.. image:: images/moduleMetadata-01.*
    :width: 600

    A guide to the 2022 Dublin Core implementation:

    The guts of class Metadata are completely rewritten to support the new
    Dublin Core functionality, but all of Metadata's previous APIs are still in
    place and are all backward compatible. There are new APIs (md[], md.add et
    al) to access the new functionality.

    The previous metadata implementation had a list of supported workIds, and also
    a list of standard contributor roles.  You could have more than one of each
    contributor role, but only one of each workId.

    In the new implementation, contributor roles are treated the same as other
    non-contributor metadata.  I have a list of supported property terms, which are
    pulled from Dublin Core (namespace = 'dcterms'), MARC Relator codes (a.k.a.
    contributor roles, namespace = 'marcrel'), and Humdrum (namespace = 'humdrum').
    Each metadata property can be specified by 'namespace:name' or by 'uniqueName'.
    For example: md['marcrel:CMP'] and md['composer'] are equivalent, as
    are md['dcterms:alternative'] and md['alternativeTitle'].
    You can have more than one of any such item (not just contributors). That
    implies that there must be two APIs for adding a new piece of metadata.  One
    that overwrites any existing metadata items of that name, and one that simply
    adds the new item(s) to the existing list.  They are: add() and set().  add()
    adds the new item to the (possibly empty) list of values, and set() removes
    any current value(s) before adding the item.

    Primitives: primitives.Text has been updated to add whether or not the text has
    been translated, as well as a specified encoding scheme (a.k.a. what standard
    should I use to parse this string).

    Metadata does not explicitly support client-specified namespaces, but there
    are a few APIs (getCustom, addCustom, setCustom) with which clients can set
    anything they want. A parser could use this to set (say) 'humdrum:XXX' metadata
    that doesn't map to any standard metadata property, and a writer that understood
    'humdrum' metadata could then write it back to a file.  Custom metadata can also
    include things that are free-form, and very specific to a particular workflow.
    e.g. setCustom('widget analysis complete through measure number', 1000).
    Custom metadata like this can also be written to various file formats, as long
    as there is a place for it (e.g. '<miscellaneous>' in MusicXML).

'''
from collections import OrderedDict, namedtuple
from dataclasses import dataclass
import os
import pathlib
import re
import copy
import datetime
import unittest
import typing as t

from music21 import base
from music21 import common
from music21 import defaults
from music21 import exceptions21

from music21.metadata import properties
from music21.metadata.properties import PropertyDescription
from music21.metadata import bundles
from music21.metadata import caching
from music21.metadata import primitives
from music21.metadata.primitives import (Date, DateSingle, DateRelative, DateBetween,
                                         DateSelection, Text, Contributor, Creator,
                                         Imprint, Copyright)

from music21.metadata import testMetadata
# -----------------------------------------------------------------------------

__all__ = [
    'Metadata',
    'RichMetadata',
    'AmbitusShort',
]

from music21 import environment
environLocal = environment.Environment(os.path.basename(__file__))

AmbitusShort = namedtuple('AmbitusShort',
                          ['semitones', 'diatonic', 'pitchLowest', 'pitchHighest'])

@dataclass
class FileInfo:
    path: t.Optional[Text] = None
    number: t.Optional[int] = None
    format: t.Optional[Text] = None

# -----------------------------------------------------------------------------


class Metadata(base.Music21Object):
    r'''
    Metadata represent data for a work or fragment, including title, composer,
    dates, and other relevant information.

    Metadata is a :class:`~music21.base.Music21Object` subclass, meaning that it
    can be positioned on a Stream by offset and have a
    :class:`~music21.duration.Duration`.

    In many cases, each Stream will have a single Metadata object at the zero
    offset position.

    >>> md = metadata.Metadata(title='Concerto in F')
    >>> md.title
    'Concerto in F'

    Or by three-letter abbreviation:

    >>> md = metadata.Metadata(otl='Concerto in F')
    >>> md.otl
    'Concerto in F'
    >>> md.title
    'Concerto in F'

    Or by setWorkId

    >>> md.setWorkId('title', 'Rhapsody in Blue')
    >>> md.title
    'Rhapsody in Blue'

    >>> md.otl
    'Rhapsody in Blue'

    >>> md.composer = 'Gershwin, George'

    These are used by .search() methods to determine what attributes are
    made available by default.

    >>> md.searchAttributes
    ('abstract', 'accessRights', 'accompanyingMaterialWriter', 'accrualMethod',
    'accrualPeriodicity', 'accrualPolicy', 'actNumber', 'actor', 'adapter',
    'afterwordAuthor', 'alternativeTitle', 'animator', 'annotator', 'architect',
    'arranger', 'artist', 'associatedWork', 'attributedComposer', 'audience',
    'author', 'bibliographicCitation', 'calligrapher', 'cartographer',
    'choreographer', 'cinematographer', 'collaborator', 'collectionDesignation',
    'collotyper', 'commentator', 'commission', 'commissionedBy', 'compiler',
    'composer', 'composerAlias', 'composerCorporate', 'conceptor', 'conductor',
    'conformsTo', 'consultant', 'contractor', 'copyright', 'correspondent',
    'costumeDesigner', 'countryOfComposition', 'coverage', 'creator', 'curator',
    'dancer', 'date', 'dateAccepted', 'dateAvailable', 'dateCopyrighted',
    'dateCreated', 'dateIssued', 'dateModified', 'dateSubmitted', 'dateValid',
    'dedicatedTo', 'dedication', 'delineator', 'description', 'designer',
    'dialogAuthor', 'director', 'dissertant', 'distributor', 'draftsman',
    'editor', 'educationLevel', 'engineer', 'engraver', 'etcher', 'extent',
    'facsimilist', 'fileFormat', 'fileNumber', 'filePath', 'filmEditor',
    'forger', 'format', 'genericContributor', 'groupTitle', 'hasFormat',
    'hasPart', 'hasVersion', 'host', 'identifier', 'illuminator', 'illustrator',
    'instructionalMethod', 'instrumentalist', 'interviewee', 'interviewer',
    'introductionAuthor', 'inventor', 'isFormatOf', 'isPartOf', 'isReferencedBy',
    'isReplacedBy', 'isRequiredBy', 'isVersionOf', 'landscapeArchitect', 'language',
    'librettist', 'license', 'lightingDesigner', 'lithographer', 'localeOfComposition',
    'lyricist', 'manufacturer', 'mediator', 'medium', 'meetingOrganizer',
    'metalEngraver', 'moderator', 'movementName', 'movementNumber', 'musician',
    'narrator', 'number', 'opusNumber', 'orchestrator', 'originator', 'otherContributor',
    'otherDate', 'parentTitle', 'performer', 'photographer', 'platemaker',
    'popularTitle', 'printmaker', 'producer', 'productionPersonnel', 'programmer',
    'projectConsultant', 'provenance', 'publisher', 'puppeteer', 'quotationsAuthor',
    'recordingEngineer', 'references', 'relation', 'renderer', 'replaces',
    'reporter', 'requires', 'researchTeamHead', 'researchTeamMember', 'researcher',
    'responsibleParty', 'restager', 'reviewer', 'rightsHolder', 'scenarist',
    'sceneNumber', 'scientificAdvisor', 'screenplayAuthor', 'scribe', 'sculptor',
    'secretary', 'setDesigner', 'singer', 'source', 'spatialCoverage', 'speaker',
    'standardsBody', 'storyteller', 'subject', 'subtitle', 'surveyor',
    'suspectedComposer', 'tableOfContents', 'teacher', 'temporalCoverage',
    'textLanguage', 'textOriginalLanguage', 'title', 'transcriber', 'translator',
    'type', 'videographer', 'vocalist', 'volume', 'volumeNumber', 'woodCutter',
    'woodEngraver', 'writtenCommentator')

    >>> md.contributors
    [<music21.metadata.primitives.Contributor composer:Gershwin, George>]
    '''

    # CLASS VARIABLES #

    classSortOrder = -30

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

    # We differentiate between allUniqueNames, a list of all the values you can get,
    # and searchAttributes, a list of all the names you can search for.  The difference
    # is that searchAttributes has all the extra workIds in it that are different from
    # the uniqueName for that same property.  For example, 'dedicatedTo' is a uniqueName
    # for which the workId is 'dedication'.  Both will show up in searchAttributes (so
    # you can search for either one), but only 'dedicatedTo' will show up in allUniqueNames,
    # because you don't want to get both 'dedicatedTo' and 'dedication', since they are
    # the same value.  Note that searchAttributes' initialization uses set() to get rid
    # of any workIds that are the same name as the uniqueName.

    # add more as properties/import exists
    allUniqueNames = tuple(sorted([
        'fileFormat',
        'fileNumber',
        'filePath',
    ] + properties.ALL_UNIQUENAMES))

    searchAttributes: t.Tuple = tuple(sorted(set(
        list(allUniqueNames) + properties.ALL_M21WORKIDS)))

    workIdLookupDict = {}
    for key, value in workIdAbbreviationDict.items():
        workIdLookupDict[value.lower()] = key

    # INITIALIZER #

    def __init__(self, *args, **keywords):
        super().__init__()

        self._metadata: t.Dict = {}
        self.software: t.List[str] = [defaults.software]

        # TODO: check pickling, etc.
        self.fileInfo = FileInfo()

        # For backward compatibility, we allow the setting of workIds or
        # abbreviations via **keywords
        for abbreviation, workId in self.workIdAbbreviationDict.items():
            if workId in keywords:
                nsKey: str = properties.M21WORKID_TO_NSKEY[workId]
                self._metadata[nsKey] = Text(keywords[workId])
            elif abbreviation in keywords:
                nsKey: str = properties.M21ABBREV_TO_NSKEY[abbreviation]
                self._metadata[nsKey] = Text(keywords[abbreviation])

        # search for any keywords that match attributes
        # these are for direct Contributor access, must have defined
        # properties
        for attr in ['composer', 'date', 'title']:
            if attr in keywords:
                setattr(self, attr, keywords[attr])


# -----------------------------------------------------------------------------

    def add(self,
            key: str,
            value: t.Union[t.Any, t.Iterable[t.Any]]):
        '''
        Adds a single item or multiple items with this key, leaving any existing
        items with this key in place.

        The key can be the item's uniqueName or 'namespace:name'.  If it is
        not one of the standard metadata properties, KeyError will be raised.

        >>> md = metadata.Metadata()
        >>> md.add('suspectedComposer', 'Ludwig von Beethoven')
        >>> md['suspectedComposer']
        (<music21.metadata.primitives.Contributor suspectedComposer:Ludwig von Beethoven>,)

        >>> md.add('title', [metadata.Text('Caveat Emptor', language='la'),
        ...                  metadata.Text('Buyer Beware',  language='en')])
        >>> titles = md['title']
        >>> titles
        (<music21.metadata.primitives.Text Caveat Emptor>,
        <music21.metadata.primitives.Text Buyer Beware>)
        >>> titles[0].language
        'la'
        >>> titles[1].language
        'en'
        '''
        self._add(key, value, isCustom=False)

    def getCustom(self, key: str) -> t.Tuple[t.Any, ...]:
        return self._get(key, isCustom=True)

    def addCustom(self, key: str, value: t.Union[t.Any, t.List[t.Any]]):
        self._add(key, value, isCustom=True)

    def setCustom(self, key: str, value: t.Union[t.Any, t.List[t.Any]]):
        self._set(key, value, isCustom=True)

    def getAllNamedValues(self, skipContributors=False) -> t.List[t.Tuple[str, t.Any]]:
        '''
        Returns all values stored in this metadata as a list of (nsKey, value) tuples.
        nsKeys with multiple values will appear multiple times in the list (rather
        than appearing once, with a value that is a list of values).
        The tuple's first element is either of the form 'namespace:name', or a
        custom key (with no form at all).

        >>> md = metadata.Metadata()
        >>> md.add('composer', 'Jeff Bowen')
        >>> md.add('librettist', 'Hunter Bell')
        >>> md.add('title', '[title of show]')
        >>> md.addCustom('excerpt-start-measure', 1234)
        >>> all = md.getAllNamedValues()
        >>> all
        [('marcrel:CMP', <music21.metadata.primitives.Contributor composer:Jeff Bowen>),
        ('marcrel:LBT', <music21.metadata.primitives.Contributor librettist:Hunter Bell>),
        ('dcterms:title', <music21.metadata.primitives.Text [title of show]>),
        ('excerpt-start-measure', <music21.metadata.primitives.Text 1234>)]
        >>> all = md.getAllNamedValues(skipContributors=True)
        >>> all
        [('dcterms:title', <music21.metadata.primitives.Text [title of show]>),
        ('excerpt-start-measure', <music21.metadata.primitives.Text 1234>)]
        '''
        allOut: t.List[t.Tuple[str, t.Any]] = []

        for nsKey, value in self._metadata.items():
            if skipContributors and self._isContributorNSKey(nsKey):
                continue

            if isinstance(value, list):
                for v in value:
                    allOut.append((nsKey, v))
            else:
                allOut.append((nsKey, value))

        return allOut

    def getAllContributorNamedValues(self) -> t.List[t.Tuple[str, t.Any]]:
        '''
        Returns all contributors stored in this metadata as a list of (nsKey, value) tuples.
        The tuple's first element will be of the form 'namespace:name'.

        >>> md = metadata.Metadata()
        >>> md.addCustom('composer', 'Not a contributor')
        >>> md.add('title', '[title of show]')
        >>> md.addCustom('excerpt-start-measure', 1234)
        >>> md.add('composer', ['Ludwig von Beethoven', 'Wolfgang Amadeus Mozart'])
        >>> md.add('librettist', 'Marie Červinková-Riegrová')
        >>> all = md.getAllContributorNamedValues()
        >>> len(all)
        3
        >>> all[0]
        ('marcrel:CMP', <music21.metadata.primitives.Contributor composer:Ludwig von Beethoven>)
        >>> all[1]
        ('marcrel:CMP', <music21.metadata.primitives.Contributor composer:Wolfgang Amadeus Mozart>)
        >>> all[2][0]
        'marcrel:LBT'
        >>> all[2][1]
        <music21.metadata.primitives.Contributor librettist:Marie Červinková-Riegrová>
        '''

        allOut: t.List[t.Tuple[str, Contributor]] = []

        for nsKey, value in self._metadata.items():
            if not self._isContributorNSKey(nsKey):
                continue

            if isinstance(value, list):
                for v in value:
                    allOut.append((nsKey, v))
            else:
                allOut.append((nsKey, value))

        return allOut

# -----------------------------------------------------------------------------
#   A few static utility routines for clients calling public APIs
    @staticmethod
    def uniqueNameToNSKey(uniqueName: str) -> t.Optional[str]:
        '''
        Translates a unique name to the associated standard property's NSKey.
        Returns None if no such associated standard property can be found.

        >>> metadata.Metadata.uniqueNameToNSKey('librettist')
        'marcrel:LBT'
        >>> metadata.Metadata.uniqueNameToNSKey('not a standard property') is None
        True
        >>> metadata.Metadata.uniqueNameToNSKey(None) is None
        True
        >>> metadata.Metadata.uniqueNameToNSKey('alternativeTitle')
        'dcterms:alternative'
        '''
        if not uniqueName:
            return None
        return properties.UNIQUENAME_TO_NSKEY.get(uniqueName, None)

    @staticmethod
    def isContributorUniqueName(uniqueName: str) -> bool:
        '''
        Determines if a unique name is associated with a standard contributor
        property.  Returns False if no such associated standard property can
        be found.

        >>> metadata.Metadata.isContributorUniqueName('librettist')
        True
        >>> metadata.Metadata.isContributorUniqueName('architect')
        True
        >>> metadata.Metadata.isContributorUniqueName('alternativeTitle')
        False
        >>> metadata.Metadata.isContributorUniqueName('not a standard property')
        False
        >>> metadata.Metadata.isContributorUniqueName(None)
        False
        '''
        if not uniqueName:
            return False
        prop: PropertyDescription = (
            properties.UNIQUENAME_TO_PROPERTYDESCRIPTION.get(uniqueName, None))
        if prop is None:
            return False

        return prop.isContributor

    @staticmethod
    def _isStandardUniqueName(uniqueName: str) -> bool:
        '''
        Determines if a unique name is associated with a standard property.
        Returns False if no such associated standard property can be found.

        >>> metadata.Metadata._isStandardUniqueName('librettist')
        True
        >>> metadata.Metadata._isStandardUniqueName('architect')
        True
        >>> metadata.Metadata._isStandardUniqueName('alternativeTitle')
        True
        >>> metadata.Metadata._isStandardUniqueName('not a standard property')
        False
        >>> metadata.Metadata._isStandardUniqueName(None)
        False
        '''
        if not uniqueName:
            return False
        prop: PropertyDescription = (
            properties.UNIQUENAME_TO_PROPERTYDESCRIPTION.get(uniqueName, None))
        if prop is None:
            return False

        return True

    @staticmethod
    def _isStandardNSKey(nsKey: str) -> bool:
        '''
        Determines if a unique name is associated with a standard property.
        Returns False if no such associated standard property can be found.

        >>> metadata.Metadata._isStandardNSKey('marcrel:LBT')
        True
        >>> metadata.Metadata._isStandardNSKey('librettist')
        False
        >>> metadata.Metadata._isStandardNSKey('nonstandardnamespace:LBT')
        False
        >>> metadata.Metadata._isStandardNSKey('marcrel:nonstandardname')
        False
        >>> metadata.Metadata._isStandardNSKey(None)
        False
        '''
        if not nsKey:
            return False
        prop: PropertyDescription = (
            properties.NSKEY_TO_PROPERTYDESCRIPTION.get(nsKey, None))
        if prop is None:
            return False

        return True

    @staticmethod
    def isStandardKey(key: str) -> bool:
        '''
        Determines if key is either a 'namespace:name' or 'uniqueName' associated
        with a standard property.
        Returns False if no such associated standard property can be found.

        >>> metadata.Metadata.isStandardKey('marcrel:LBT')
        True
        >>> metadata.Metadata.isStandardKey('librettist')
        True
        >>> metadata.Metadata.isStandardKey('not a standard property')
        False
        >>> metadata.Metadata.isStandardKey('marcrel:nonstandardname')
        False
        >>> metadata.Metadata.isStandardKey(None)
        False
        '''
        if not key:
            return False

        if Metadata._isStandardNSKey(key):
            return True

        if Metadata._isStandardUniqueName(key):
            return True

        return False

    @staticmethod
    def nsKeyToUniqueName(nsKey: str) -> t.Optional[str]:
        '''
        Translates a standard property NSKey ('namespace:name') to that
        standard property's uniqueName.
        Returns None if no such standard property exists.

        >>> metadata.Metadata.nsKeyToUniqueName('marcrel:LBT')
        'librettist'
        >>> metadata.Metadata.nsKeyToUniqueName('not a standard nskey') is None
        True
        >>> metadata.Metadata.nsKeyToUniqueName(None) is None
        True
        >>> metadata.Metadata.nsKeyToUniqueName('dcterms:alternative')
        'alternativeTitle'
        '''
        if not nsKey:
            return None
        uniqueName: t.Optional[str] = properties.NSKEY_TO_UNIQUENAME.get(nsKey, None)
        return uniqueName


# -----------------------------------------------------------------------------
#   Pre-2022 public APIs

    @property
    def contributors(self) -> t.List[Contributor]:
        '''
        Returns a list of all the Contributors found in the metadata.
        Returns [] if no Contributors exist.

        >>> md = metadata.Metadata()
        >>> md['composer'] = ['Ludwig', 'Wolfgang']
        >>> md['librettist'] = 'Joe'
        >>> md.add('architect', 'John')      # 'architect' is new in 2022
        >>> md.add('title', 'Caveat Emptor') # not a contributor
        >>> contribs = md.contributors
        >>> contribs
        [<music21.metadata.primitives.Contributor composer:Ludwig>,
        <music21.metadata.primitives.Contributor composer:Wolfgang>,
        <music21.metadata.primitives.Contributor librettist:Joe>,
        <music21.metadata.primitives.Contributor architect:John>]
        '''

        # This was just a data attribute before.  Hopefully no-one is calling
        # md.contributors.append(c).  I did a global search on github for
        # 'music21 contributors', and all code that modified it that I found
        # were in music21 forks.  So I think we're OK making this a read-only
        # property that we generate on the fly.
        contribNamedValues = self.getAllContributorNamedValues()
        output = [namedValue[1] for namedValue in contribNamedValues]
        return output

    @property
    def copyright(self) -> t.Optional[str]:
        '''
        Returns the copyright as a str.
        Returns None if no copyright exists in the metadata.
        Returns 'MULTIPLE' if multiple copyrights exist in the metadata.
        Use md['copyright'] to get all the copyrights.

        >>> md = metadata.Metadata()
        >>> md.copyright is None
        True
        >>> md['dcterms:rights'] = 'Copyright © 1984 All Rights Reserved'
        >>> md.copyright
        'Copyright © 1984 All Rights Reserved'
        >>> md.add('dcterms:rights', 'Lyrics copyright © 1987 All Rights Reserved')
        >>> md.copyright
        'MULTIPLE'

        >>> md = metadata.Metadata()
        >>> md.copyright is None
        True
        >>> md['copyright'] = 'Copyright © 1984 All Rights Reserved'
        >>> md.copyright
        'Copyright © 1984 All Rights Reserved'
        >>> md['dcterms:rights']
        (<music21.metadata.primitives.Copyright Copyright © 1984 All Rights Reserved>,)
        >>> md.copyright = metadata.Text('Copyright ©    1984 from Text')
        >>> md['copyright']
        (<music21.metadata.primitives.Copyright Copyright © 1984 from Text>,)
        >>> md.copyright = metadata.Copyright('Copyright © 1984 from Copyright', role='something')
        >>> md['dcterms:rights']
        (<music21.metadata.primitives.Copyright Copyright © 1984 from Copyright>,)
        '''
        return self.__getattr__('copyright')

    # SPECIAL METHODS #
    def all(self, skipContributors=False):
        # noinspection SpellCheckingInspection
        '''
        Returns all values (as strings) stored in this metadata as a sorted list of tuples.

        >>> c = corpus.parse('corelli/opus3no1/1grave')
        >>> c.metadata.all()
        [('arranger', 'Michael Scott Cuthbert'),
         ('composer', 'Arcangelo Corelli'),
         ('copyright', '© 2014, Creative Commons License (CC-BY)'),
         ('fileFormat', 'musicxml'),
         ('filePath', '...corpus/corelli/opus3no1/1grave.xml'),
         ('movementName', 'Sonata da Chiesa, No. I (opus 3, no. 1)')]

        Skip contributors is there to help with musicxml parsing -- there's no reason for it
        except that we haven't exposed enough functionality yet:

        >>> c.metadata.date = metadata.DateRelative('1689', 'onOrBefore')
        >>> c.metadata.localeOfComposition = 'Rome'
        >>> c.metadata.all(skipContributors=True)
        [('copyright', '© 2014, Creative Commons License (CC-BY)'),
         ('dateCreated', '1689/--/-- or earlier'),
         ('fileFormat', 'musicxml'),
         ('filePath', '...corpus/corelli/opus3no1/1grave.xml'),
         ('localeOfComposition', 'Rome'),
         ('movementName', 'Sonata da Chiesa, No. I (opus 3, no. 1)')]
        '''
        # pylint: disable=undefined-variable
        allOut = {}

        for uniqueName in self.allUniqueNames:
            try:
                values: t.Tuple[str, ...] = self._getStringsByNSKey(
                    properties.UNIQUENAME_TO_NSKEY[uniqueName])
                if not values:
                    continue
                val = values[0]
            except AttributeError:
                continue
            except KeyError:
                # A uniqueName that doesn't have a PropertyDescription
                # That's the three fileInfo properties
                if uniqueName == 'fileFormat':
                    val = str(self.fileFormat)
                elif uniqueName == 'filePath':
                    val = str(self.filePath)
                elif uniqueName == 'fileNumber':
                    val = self.fileNumber
                else:
                    raise

            if skipContributors:
                if self.isContributorUniqueName(uniqueName):
                    continue
            if val == 'None' or not val:
                continue
            allOut[uniqueName] = val

        if not skipContributors:
            for c in self.contributors:
                if c.role in allOut:
                    continue
                if not c.name or c.name == 'None':
                    continue
                allOut[str(c.role)] = str(c.name)

        if 'title' in allOut and 'movementName' in allOut:
            if allOut['movementName'] == allOut['title']:
                del(allOut['title'])

        return list(sorted(allOut.items()))

    def _getStringByNSKey(self, nsKey: str) -> t.Optional[str]:
        values: t.Tuple[t.Any, ...] = self._getStringsByNSKey(nsKey)
        if not values:
            return None
        if len(values) == 1:
            return values[0]
        return 'MULTIPLE'

    def _getStringsByNSKey(self, nsKey: str) -> t.Tuple[str, ...]:
        values: t.Tuple[t.Any, ...]
        try:
            values = self._get(nsKey, isCustom=False)
        except KeyError:
            return tuple()

        if not values:
            return values

        output: t.Tuple[str, ...] = tuple(str(value) for value in values)
        return output

    def _getPluralAttribute(self, attributeName: str) -> t.Tuple[t.Union[str, int], ...]:
        # This does what __getattr__ would do if we supported plural attributeNames
        # (but it takes singular attributeNames, of course).

        # It raises AttributeError if attributeName is not a valid uniqueName,
        # workId, or workId abbreviation.  Used in search, for example, because
        # search wants to find everything.

        if attributeName in properties.UNIQUENAME_TO_NSKEY:
            return self._getStringsByNSKey(properties.UNIQUENAME_TO_NSKEY[attributeName])

        # Is attributeName a grandfathered workId?
        if attributeName in properties.M21WORKID_TO_NSKEY:
            return self._getStringsByNSKey(properties.M21WORKID_TO_NSKEY[attributeName])

        # Is attributeName a grandfathered workId abbreviation?
        if attributeName in properties.M21ABBREV_TO_NSKEY:
            return self._getStringsByNSKey(properties.M21ABBREV_TO_NSKEY[attributeName])

        # The following are in searchAttributes, and getattr will find them because
        # they are a property, but this routine needs to find them, too.
        if attributeName == 'fileFormat':
            if self.fileFormat is None:
                return tuple()
            return (self.fileFormat,)

        if attributeName == 'filePath':
            if self.filePath is None:
                return tuple()
            return (self.filePath,)

        if attributeName == 'fileNumber':
            if self.fileNumber is None:
                return tuple()
            return (self.fileNumber,)

        raise AttributeError(f'invalid attributeName: {attributeName}')

    def __getattr__(self, name):
        '''
        Utility attribute access for all uniqueNames, grandfathered workIds,
        and grandfathered workId abbreviations.  Many grandfathered workIds
        have explicit property definitions, so they won't end up here.

        These always return str or None.  Note well: if there is more than
        one item for a particular name, we return 'MULTIPLE', to signal the
        client to dig deeper (using an API such as md[name], which returns
        all the items for that name).

        If name is not a valid attribute (uniqueName, grandfathered workId,
        or grandfathered workId abbreviation), then AttributeError is raised.

        >>> md = metadata.Metadata()
        >>> md.description = metadata.Text('A uniqueName description', language='en')
        >>> md.dedication = 'A workId that is not a uniqueName'
        >>> md.otl = metadata.Text('A workId abbreviation')
        >>> md.description
        'A uniqueName description'
        >>> md.dedicatedTo  # the uniqueName for 'dedicated' workId
        'A workId that is not a uniqueName'
        >>> md.title  # the workId/uniqueName for 'otl' abbreviation
        'A workId abbreviation'
        >>> md.add('description', 'uniqueName description #2')
        >>> md.description
        'MULTIPLE'
        '''

        # __getattr__ is the call of last resort after looking for bare
        # attributes and property methods, so __getattr__ won't be called
        # for self.software (bare attribute), or for self.composer (property).
        # (property), even though we certainly could handle those here.
        # This is why we don't have to handle .composers/librettists/lyricists
        # or .fileFormat/filePath/fileNumber here, like we do in __setattr__
        # (which is the only call you get if you implement it, so it has
        # to handle everything).

        # Is name a uniqueName?
        if name in properties.UNIQUENAME_TO_NSKEY:
            return self._getStringByNSKey(properties.UNIQUENAME_TO_NSKEY[name])

        # Is name a grandfathered workId?
        if name in properties.M21WORKID_TO_NSKEY:
            return self._getStringByNSKey(properties.M21WORKID_TO_NSKEY[name])

        # Is name a grandfathered workId abbreviation?
        if name in properties.M21ABBREV_TO_NSKEY:
            return self._getStringByNSKey(properties.M21ABBREV_TO_NSKEY[name])

        raise AttributeError(f'object has no attribute: {name}')

    def __setattr__(self, name: str, value: t.Any):
        '''
        Utility attribute setter for all uniqueNames, grandfathered workIds,
        and grandfathered workId abbreviations.

        These can take any single value, and will convert to the appropriate
        internal valueType.  They will raise ValueError for iterables (other
        than str).
        '''

        # Implementation note: __setattr__ has a very different role from
        # __getattr__.  __getattr__ is the call of last resort after looking
        # for bare attributes and property methods, so __getattr__ won't be
        # called for self.software (bare attribute), or for self.composer
        # (property).  __setattr__, on the other hand, is the _only_ call
        # you will get.  So after checking for uniqueNames, workIds, and
        # workId abbreviations, if we haven't done the job yet, we need to
        # make a call to super().__setattr__ to handle all the bare attributes.
        # Unfortunately, that doesn't handle property.setters at all, so any
        # property.setters have to be removed, and handled explicitly here.

        # Is name a uniqueName?
        if name in properties.UNIQUENAME_TO_NSKEY:
            if (value is not None
                    and isinstance(value, t.Iterable)
                    and not isinstance(value, str)):
                raise ValueError(f'md.{name} can only be set to a single value; '
                                 f'set md[{name}] to multiple values instead.')
            self._set(properties.UNIQUENAME_TO_NSKEY[name], value, isCustom=False)
            return

        # Is name a grandfathered workId?
        if name in properties.M21WORKID_TO_NSKEY:
            if (value is not None
                    and isinstance(value, t.Iterable)
                    and not isinstance(value, str)):
                raise ValueError(f'md.{name} can only be set to a single value; '
                                 f'set md[{name}] to multiple values instead.')
            self._set(properties.M21WORKID_TO_NSKEY[name], value, isCustom=False)
            return

        # Is name a grandfathered workId abbreviation?
        if name in properties.M21ABBREV_TO_NSKEY:
            if (value is not None
                    and isinstance(value, t.Iterable)
                    and not isinstance(value, str)):
                raise ValueError(f'md.{name} can only be set to a single value; '
                                 f'set md[{name}] to multiple values instead.')
            self._set(properties.M21ABBREV_TO_NSKEY[name], value, isCustom=False)
            return

        # Is name one of the non-uniqueName property.setters (i.e the three
        # plural contributors, and the three new fileInfo setters)?
        if name in ('composers', 'librettists', 'lyricists'):
            uniqueName = name[:-1]  # remove the trailing 's'
            # check that value is t.Iterable (and not str)
            if not isinstance(value, t.Iterable) or isinstance(value, str):
                raise ValueError(f'md.{name} can only be set to multiple values.')
            self._set(uniqueName, value, isCustom=False)
            return

        if name == 'fileFormat':
            self.fileInfo.format = Text(value)
            return

        if name == 'filePath':
            self.fileInfo.path = Text(value)
            return

        if name == 'fileNumber':
            self.fileInfo.number = value
            return

        # OK, we've covered everything we know about; fall back to setting
        # bare attributes (including the ones in base classes).
        super().__setattr__(name, value)

    def __getitem__(self, key: str) -> t.Tuple[t.Any, ...]:
        '''
        Utility "dictionary key" access for all standard uniqueNames and
        standard keys of the form 'namespace:name'.

        These always return t.Tuple[t.Any, ...], which may be empty.

        If key is not a standard uniqueName or standard 'namespace:name',
        then KeyError is raised.

        >>> md = metadata.Metadata()
        >>> md['description'] = metadata.Text('A fun score!', language='en')
        >>> descs = md['description']
        >>> descs
        (<music21.metadata.primitives.Text A fun score!>,)
        >>> md.add('description', 'Also a great tune')
        >>> descs = md['description']
        >>> isinstance(descs, tuple)
        True
        >>> len(descs)
        2
        >>> descs
        (<music21.metadata.primitives.Text A fun score!>,
        <music21.metadata.primitives.Text Also a great tune>)
        >>> descs[0].language
        'en'
        >>> descs[1].language is None
        True
        '''
        if not isinstance(key, str):
            raise KeyError('metadata key must be str')

        return self._get(key, isCustom=False)

    def __setitem__(self, key: str, value: t.Union[t.Any, t.Iterable[t.Any]]):
        if not isinstance(key, str):
            raise KeyError('metadata key must be str')

        # Is key a uniqueName?
        if key in properties.UNIQUENAME_TO_NSKEY:
            self._set(properties.UNIQUENAME_TO_NSKEY[key], value, isCustom=False)
            return

        # Is key an nsKey ('namespace:name')?
        if key in properties.ALL_NSKEYS:
            self._set(key, value, isCustom=False)

        # Is key a grandfathered workId?
        if key in properties.M21WORKID_TO_NSKEY:
            self._set(properties.M21WORKID_TO_NSKEY[key], value, isCustom=False)
            return

        # Is key a grandfathered workId abbreviation?
        if key in properties.M21ABBREV_TO_NSKEY:
            self._set(properties.M21ABBREV_TO_NSKEY[key], value, isCustom=False)
            return

    # PUBLIC METHODS #

    @staticmethod
    def abbreviationToWorkId(abbreviation):
        '''Get work id abbreviations.

        >>> metadata.Metadata.abbreviationToWorkId('otl')
        'title'

        >>> for work_id in metadata.Metadata.workIdAbbreviationDict:
        ...    result = metadata.Metadata.abbreviationToWorkId(work_id)

        '''
        abbreviation = abbreviation.lower()
        if abbreviation not in Metadata.workIdAbbreviationDict:
            raise exceptions21.MetadataException(
                f'no such work id: {abbreviation}')
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

        >>> c_alt = metadata.Contributor()
        >>> c_alt.name = 'Cheney, Amy Marcy'
        >>> c_alt.role = 'composer'
        >>> md.addContributor(c_alt)
        >>> md.composers
        ['Beach, Amy', 'Cheney, Amy Marcy']

        >>> md.search('Beach')
        (True, 'composer')
        >>> md.search('Cheney')
        (True, 'composer')

        Note that in this case, a "composerAlias" would probably be a more
        appropriate role than a second composer.

        All contributor roles are searchable, even if they are not standard roles:

        >>> dancer = metadata.Contributor()
        >>> dancer.names = ['Merce Cunningham', 'Martha Graham']
        >>> dancer.role = 'interpretive dancer'
        >>> md.addContributor(dancer)
        >>> md.search('Cunningham')
        (True, 'interpretive dancer')
        '''
        if not isinstance(c, Contributor):
            raise exceptions21.MetadataException(
                f'supplied object is not a Contributor: {c}')
        self._addBackwardCompatibleContributor(c)

    def getContributorsByRole(self, value):
        r'''
        Return a :class:`~music21.metadata.Contributor` if defined for a
        provided role.

        >>> md = metadata.Metadata(title='Violin Concerto')

        >>> c = metadata.Contributor()
        >>> c.name = 'Price, Florence'
        >>> c.role = 'composer'
        >>> md.addContributor(c)
        >>> cList = md.getContributorsByRole('composer')
        >>> cList
        [<music21.metadata.primitives.Contributor composer:Price, Florence>]

        >>> cList[0].name
        'Price, Florence'

        Some musicxml files have contributors with no role defined.  To get
        these contributors, search for getContributorsByRole(None).  N.B. upon
        output to MusicXML, music21 gives these contributors the generic role
        of "creator"

        >>> c2 = metadata.Contributor()
        >>> c2.name = 'Baron van Swieten'
        >>> md.addContributor(c2)
        >>> noRoleList = md.getContributorsByRole(None)
        >>> len(noRoleList)
        1

        >>> noRoleList[0].role
        >>> noRoleList[0].name
        'Baron van Swieten'
        '''
        result = []  # there may be more than one per role
        for c in self.contributors:
            if c.role == value:
                result.append(c)
        if result:
            return result
        else:
            return None

    def search(self, query=None, field=None, **kwargs):
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

        These don't work (Richard didn't have the sense of rhythm to write this...)

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


        New in v.4 -- use a keyword argument to search
        that field directly:

        >>> md.search(composer='Joplin')
        (True, 'composer')
        '''
        # TODO: Change to a namedtuple and add as a third element
        #    during a successful search, the full value of the retrieved
        #    field (so that 'Joplin' would return 'Joplin, Scott')
        reQuery = None
        valueFieldPairs = []
        if query is None and field is None and not kwargs:
            return (False, None)
        elif query is None and field is None and kwargs:
            field, query = kwargs.popitem()

        if field is not None:
            field = field.lower()
            match = False
            try:
                values = self._getPluralAttribute(field)
                if values:
                    for value in values:
                        valueFieldPairs.append((value, field))
                    match = True
            except AttributeError:
                pass
            if not match:
                for searchAttribute in self.searchAttributes:
                    # environLocal.printDebug(['comparing fields:', f, field])
                    # look for partial match in all fields
                    if field.lower() in searchAttribute.lower():
                        values = self._getPluralAttribute(searchAttribute)
                        for value in values:
                            valueFieldPairs.append((value, searchAttribute))
                        match = True
                        break
        else:  # get all fields
            for innerField in self.allUniqueNames:
                if innerField == 'otherContributor':
                    # Special name that means "use the value.role instead, it's a custom role".
                    # We'll catch it below when we append contrib.role for all contributors
                    continue
                values = self._getPluralAttribute(innerField)
                for value in values:
                    valueFieldPairs.append((value, innerField))

        # now search all contributors.
        for _, contrib in self.getAllContributorNamedValues():
            if field is not None:
                if contrib.role is None and field.lower() != 'contributor':
                    continue
                if contrib.role is not None and field.lower() not in contrib.role:
                    continue
            for name in contrib.names:
                valueFieldPairs.append((name, contrib.role))

        # for now, make all queries strings
        # ultimately, can look for regular expressions by checking for
        # .search
        useRegex = False
        if hasattr(query, 'search'):
            useRegex = True
            reQuery = query  # already compiled
        # look for regex characters
        elif (isinstance(query, str)
              and any(character in query for character in '*.|+?{}')):
            useRegex = True
            reQuery = re.compile(query, flags=re.IGNORECASE)

        if useRegex:
            for value, innerField in valueFieldPairs:
                # "re.I" makes case-insensitive search
                if isinstance(value, str):
                    match = reQuery.search(value)
                    if match is not None:
                        return True, innerField
        elif callable(query):
            for value, innerField in valueFieldPairs:
                if query(value):
                    return True, innerField
        else:
            for value, innerField in valueFieldPairs:
                if isinstance(value, str):
                    query = str(query)
                    if query.lower() in value.lower():
                        return True, innerField
                if (isinstance(value, int)
                        and hasattr(query, 'sharps')
                        and query.sharps == value):
                    return True, innerField

                elif query == value:
                    return True, innerField
        return False, None

    def setWorkId(self, idStr, value):
        r'''
        Directly set a work id, given either as a full string name or as a
        three-character abbreviation. The following work id abbreviations and
        their full id string are given as follows. In many cases the Metadata
        object support properties for convenient access to these work ids.

        Abbreviations and strings::
            * otl / title
            * otp / popularTitle
            * ota / alternativeTitle
            * opr / parentTitle
            * oac / actNumber
            * osc / sceneNumber
            * omv / movementNumber
            * omd / movementName
            * ops / opusNumber
            * onm / number
            * ovm / volume
            * ode / dedication
            * oco / commission
            * gtl / groupTitle
            * gaw / associatedWork
            * gco / collectionDesignation
            * txo / textOriginalLanguage
            * txl / textLanguage
            * ocy / countryOfComposition
            * opc / localeOfComposition.

        >>> md = metadata.Metadata(title='Quartet')
        >>> md.title
        'Quartet'

        >>> md.setWorkId('otl', 'Trio')
        >>> md.title
        'Trio'

        >>> md.setWorkId('ocy', 'Latvia')
        >>> md.ocy
        'Latvia'
        >>> md.countryOfComposition
        'Latvia'
        >>> md['countryOfComposition']
        (<music21.metadata.primitives.Text Latvia>,)

        >>> md.setWorkId('sdf', None)
        Traceback (most recent call last):
        music21.exceptions21.MetadataException: no work id available with id: sdf
        '''
        idStr = idStr.lower()
        match = False
        for abbreviation, workId in self.workIdAbbreviationDict.items():
            # for id in WORK_IDS:
            # abbreviation = workIdToAbbreviation(id)
            if workId.lower() == idStr:
                self._setBackwardCompatibleItem(workId, Text(value))
                match = True
                break
            elif abbreviation == idStr:
                self._setBackwardCompatibleItem(workId, Text(value))
                match = True
                break
        if not match:
            raise exceptions21.MetadataException(
                f'no work id available with id: {idStr}')

    @staticmethod
    def workIdToAbbreviation(value):
        '''Get a work abbreviation from a string representation.

        >>> metadata.Metadata.workIdToAbbreviation('localeOfComposition')
        'opc'

        Static method.
        '''
        # NOTE: this is a performance critical function
        try:
            # try direct access, where keys are already lower case
            return Metadata.workIdLookupDict[value]
        except KeyError:
            pass

        vl = value.lower()

        # slow approach
        for workId in Metadata.workIdAbbreviationDict:
            if vl == Metadata.workIdAbbreviationDict[workId].lower():
                return workId
        raise exceptions21.MetadataException(
            f'no such work id: {value}')

    # PUBLIC PROPERTIES #

    @property
    def alternativeTitle(self):
        r'''
        Get or set the alternative title.

        >>> md = metadata.Metadata(popularTitle='Eroica')
        >>> md.alternativeTitle = 'Heroic Symphony'
        >>> md.alternativeTitle
        'Heroic Symphony'
        '''
        return self.__getattr__('alternativeTitle')

    @property
    def composer(self):
        r'''
        Get or set the composer of this work. Only the first composer can be
        got or set via properties.  Instead add Composer roles to the .contributors
        list.

        The composer attribute does not live in Metadata, but creates a
        :class:`~music21.metadata.Contributor` object in the .contributors
        object.

        >>> md = metadata.Metadata(
        ...     title='Symphony in e minor',
        ...     popularTitle='Gaelic',
        ...     composer='Beach, Mrs. H.H.A.',
        ...     )
        >>> md.composer
        'Beach, Mrs. H.H.A.'
        >>> md.add('composer', 'Beach, Amy Marcy Cheney')
        >>> md.composer
        'MULTIPLE'
        '''
        return self.__getattr__('composer')

    @property
    def composers(self) -> t.List[str]:
        r'''
        Get or set a list of strings of all composer roles.

        >>> md = metadata.Metadata(title='Yellow River Concerto')
        >>> md.composers = ['Xian Xinghai', 'Yin Chengzong']

        (Yin Chengzong might be better called "Arranger" but this is for
        illustrative purposes)

        >>> md.composers
        ['Xian Xinghai', 'Yin Chengzong']


        Might as well add a third composer to the concerto committee?

        >>> contrib3 = metadata.Contributor(role='composer', name='Chu Wanghua')
        >>> md.addContributor(contrib3)
        >>> md.composers
        ['Xian Xinghai', 'Yin Chengzong', 'Chu Wanghua']

        If there are no composers, returns an empty list:

        >>> md = metadata.Metadata(title='Sentient Algorithmic Composition')
        >>> md.composers
        []
        '''
        return self._getBackwardCompatibleContributorNames('composer')

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
        >>> md.date = '1805'
        >>> md.date
        '1805/--/--'

        >>> md.date = metadata.DateBetween(['1803/01/01', '1805/04/07'])
        >>> md.date
        '1803/01/01 to 1805/04/07'
        '''
        return self.__getattr__('date')

    @property
    def fileFormat(self) -> t.Optional[str]:
        '''
        Get or set the file format that was parsed.
        '''
        if self.fileInfo.format:
            return str(self.fileInfo.format)

    @property
    def filePath(self) -> t.Optional[str]:
        '''
        Get or set the file path that was parsed.
        '''
        if self.fileInfo.path:
            return str(self.fileInfo.path)

    @property
    def fileNumber(self) -> t.Optional[int]:
        '''
        Get or set the file path that was parsed.
        '''
        if self.fileInfo.number:
            return self.fileInfo.number

    @property
    def localeOfComposition(self):
        r'''
        Get or set the locale of composition, or origin, of the work.

        >>> md = metadata.Metadata(popularTitle='Eroica')
        >>> md.localeOfComposition = 'Paris, France'
        >>> md.localeOfComposition
        'Paris, France'
        '''
        return self.__getattr__('localeOfComposition')

    @property
    def librettist(self):
        r'''
        Gets or sets a single librettist for this work:

        >>> md = metadata.Metadata(title='Death of Klinghoffer, The')
        >>> md.librettist = 'Goodman, Alice'
        >>> md.librettist
        'Goodman, Alice'

        To preserve continuity with Humdrum, library catalogues, etc.,
        librettists should be distinguished from lyricists etc., but sometimes
        the line is not 100% clear.
        '''
        return self.__getattr__('librettist')

    @property
    def librettists(self) -> t.List[str]:
        r'''
        Gets or sets a list of librettists for this work:

        >>> md = metadata.Metadata(title='Madama Butterfly')
        >>> md.librettists = ['Illica, Luigi', 'Giacosa, Giuseppe']
        >>> md.librettists
        ['Illica, Luigi', 'Giacosa, Giuseppe']

        Should be distinguished from lyricists etc.
        '''
        return self._getBackwardCompatibleContributorNames('librettist')

    @property
    def lyricist(self):
        r'''
        Gets or sets a single lyricist for this work:

        >>> md = metadata.Metadata(title='Girlfriend')
        >>> md.lyricist = 'Keys, Alicia'

        To preserve continuity with Humdrum, library catalogues, etc.,
        lyricists should be distinguished from librettists etc., but sometimes
        the line is not 100% clear:

        >>> md = metadata.Metadata(title='West Side Story')
        >>> md.lyricist = 'Sondheim, Stephen'
        >>> md.lyricist
        'Sondheim, Stephen'
        '''
        return self.__getattr__('lyricist')

    @property
    def lyricists(self) -> t.List[str]:
        r'''
        Gets or sets a list of lyricists for this work:

        >>> md = metadata.Metadata(title='Rumors')
        >>> md.lyricists = ['Buckingham, Lindsey', 'McVie, Christine', 'Nicks, Stevie']
        >>> md.lyricists
        ['Buckingham, Lindsey', 'McVie, Christine', 'Nicks, Stevie']

        Should be distinguished from librettists etc.
        '''
        return self._getBackwardCompatibleContributorNames('lyricist')

    @property
    def movementName(self):
        r'''
        Get or set the movement title.

        >>> md = metadata.Metadata()
        >>> md.movementName = 'Vivace'
        >>> md.movementName
        'Vivace'

        Note that a number of pieces from various MusicXML datasets have
        the piece title as the movement title. For instance, the Bach
        Chorales, since they are technically movements of larger cantatas.
        '''
        return self.__getattr__('movementName')

    @property
    def movementNumber(self) -> t.Optional[str]:
        r'''
        Get or set the movement number.

        >>> md = metadata.Metadata(title='Ode to Joy')
        >>> md.movementNumber = 3

        Note that movement numbers are always returned as strings!  This may
        change in the future.

        >>> md.movementNumber
        '3'
        '''
        return self.__getattr__('movementNumber')

    @property
    def number(self):
        r'''
        Get or set the number of the work within a collection of pieces.
        (for instance, the number within a collection of ABC files)

        >>> md = metadata.Metadata()
        >>> md.number = 4

        Note that numbers are always returned as strings!  This may
        change in the future.

        >>> md.number
        '4'
        '''
        return self.__getattr__('number')

    @property
    def opusNumber(self):
        r'''
        Get or set the opus number.

        >>> md = metadata.Metadata()
        >>> md.opusNumber = 56

        Note that opusNumbers are always returned as strings!  This may
        change in the future.
        >>> md.opusNumber
        '56'
        '''
        return self.__getattr__('opusNumber')

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
        result: Text = None
        for key in searchId:
            result = self._getBackwardCompatibleItemNoConversion(key)
            if result is not None:  # get first matched
                # get a string from this Text object
                # get with normalized articles
                return result.getNormalizedArticle()

# -----------------------------------------------------------------------------
# Internal support routines (many of them static).

    @staticmethod
    def _isContributorNSKey(nsKey: str) -> bool:
        if not nsKey:
            return False
        prop: PropertyDescription = properties.NSKEY_TO_PROPERTYDESCRIPTION.get(nsKey, None)
        if prop is None:
            return False

        return prop.isContributor

    @staticmethod
    def _nsKeyToContributorRole(nsKey: str) -> t.Optional[str]:
        prop: PropertyDescription = properties.NSKEY_TO_PROPERTYDESCRIPTION.get(nsKey, None)
        if prop is None:
            return None
        if not prop.isContributor:
            return None

        # it's a small-c contributor
        if prop.oldMusic21WorkId:
            # it maps to a backward compatible big-C Contributor role, which can be
            # found in prop.oldMusic21WorkId.
            return prop.oldMusic21WorkId

        # it's a small-c contributor that doesn't map to a backward compatible
        # big-C Contributor role, but since we're not trying to be backward
        # compatible, we'll take these, too.
        if prop.uniqueName:
            return prop.uniqueName
        return prop.name

    def _get(self, key: str, isCustom: bool) -> t.Tuple[t.Any, ...]:
        '''
        Returns all the items stored in metadata with this key.
        The returned value is always a Tuple. If there are no items, an empty
        Tuple is returned. If there is only one item, a Tuple containing that
        one item is returned.

        The key can be the item's uniqueName or 'namespace:name'.  If it is
        not one of the standard metadata properties, KeyError will be raised.
        '''
        if not isCustom:
            if self._isStandardUniqueName(key):
                key = properties.UNIQUENAME_TO_NSKEY.get(key, None)
            if not self._isStandardNSKey(key):
                raise KeyError(
                    f'Key=\'{key}\' is not a standard metadata key.'
                    ' Call setCustom/getCustom for custom keys.')

        value: t.Optional[t.Any] = self._metadata.get(key, None)

        if not value:
            # return empty tuple
            return tuple()

        if not isinstance(value, list):
            # return tuple of one element
            return (value,)

        # return a tuple containing contents of list
        return tuple(value)

    def _add(self, key: str, value: t.Union[t.Any, t.Iterable[t.Any]], isCustom: bool):
        '''
        Adds a single item or multiple items with this key, leaving any existing
        items with this key in place.

        The key can be the item's uniqueName or 'namespace:name'.  If it is
        not one of the standard metadata properties, KeyError will be raised.
        '''
        if not isCustom:
            if self._isStandardUniqueName(key):
                key = properties.UNIQUENAME_TO_NSKEY.get(key, None)
            if not self._isStandardNSKey(key):
                raise KeyError(
                    f'Key=\'{key}\' is not a standard metadata key.'
                    ' Call addCustom/setCustom/getCustom for custom keys.')

        if not isinstance(value, t.Iterable):
            value = [value]

        if isinstance(value, str):
            # special case: str is iterable, but we don't want to iterate over it.
            value = [value]

        convertedValues: t.List = []
        for v in value:
            convertedValues.append(self._convertValue(key, v))

        prevValue: t.Optional[t.Any] = self._metadata.get(key, None)
        if prevValue is None:
            # set the convertedValues list in there
            self._metadata[key] = convertedValues
        elif isinstance(prevValue, list):
            # add the convertedValues list to the existing list
            self._metadata[key] = prevValue + convertedValues
        else:
            # set a list containing the single prevValue plus the convertedValues list
            self._metadata[key] = [prevValue] + convertedValues

    def _set(self, key: str, value: t.Union[t.Any, t.Iterable[t.Any]], isCustom: bool):
        '''
        Sets a single item or multiple items with this key, replacing any
        existing items with this key.

        The key can be the item's uniqueName or 'namespace:name'.  If it is
        not one of the standard metadata properties, KeyError will be raised.

        >>> md = metadata.Metadata()
        >>> md._set('marcrel:LBT', metadata.Text('Marie Červinková-Riegrová'), isCustom=False)
        >>> md['librettist']
        (<music21.metadata.primitives.Contributor librettist:Marie Červinková-Riegrová>,)
        >>> md._set('librettist', [metadata.Text('Melissa Li'),
        ...                            metadata.Text('Kit Yan Win')], isCustom=False)
        >>> librettists = md['marcrel:LBT']
        >>> isinstance(librettists, tuple)
        True
        >>> librettists
        (<music21.metadata.primitives.Contributor librettist:Melissa Li>,
        <music21.metadata.primitives.Contributor librettist:Kit Yan Win>)
        '''
        if not isCustom:
            if self._isStandardUniqueName(key):
                key = properties.UNIQUENAME_TO_NSKEY.get(key, None)
            if not self._isStandardNSKey(key):
                raise KeyError(
                    f'Key=\'{key}\' is not a standard metadata key.'
                    ' Call addCustom/setCustom/getCustom for custom keys.')

        self._metadata.pop(key, None)
        self._add(key, value, isCustom)

    @staticmethod
    def _convertValue(nsKey: str, value: t.Any) -> t.Any:
        '''
        Converts a value to the appropriate valueType (looked up in STDPROPERTIES by nsKey).

        Test conversion to Text

        >>> metadata.Metadata._convertValue('dcterms:title', 3.4)
        <music21.metadata.primitives.Text 3.4>
        >>> metadata.Metadata._convertValue('dcterms:title', '3.4')
        <music21.metadata.primitives.Text 3.4>
        >>> metadata.Metadata._convertValue('dcterms:title', metadata.Text('3.4'))
        <music21.metadata.primitives.Text 3.4>

        Test conversion to Copyright

        >>> metadata.Metadata._convertValue('dcterms:rights', 'copyright str')
        <music21.metadata.primitives.Copyright copyright str>
        >>> metadata.Metadata._convertValue('dcterms:rights', metadata.Text('copyright text'))
        <music21.metadata.primitives.Copyright copyright text>
        >>> metadata.Metadata._convertValue('dcterms:rights', metadata.Copyright('copyright'))
        <music21.metadata.primitives.Copyright copyright>

        Test conversion to Contributor

        >>> metadata.Metadata._convertValue('marcrel:CMP', 'composer str')
        <music21.metadata.primitives.Contributor composer:composer str>
        >>> metadata.Metadata._convertValue('marcrel:CMP', metadata.Text('composer text'))
        <music21.metadata.primitives.Contributor composer:composer text>
        >>> metadata.Metadata._convertValue('marcrel:CMP',
        ...     metadata.Contributor(role='random', name='Joe'))
        <music21.metadata.primitives.Contributor random:Joe>

        Test conversion to DateSingle

        >>> metadata.Metadata._convertValue('dcterms:created', '1938')
        <music21.metadata.primitives.DateSingle 1938/--/-->
        >>> metadata.Metadata._convertValue('dcterms:created', metadata.Text('1938'))
        <music21.metadata.primitives.DateSingle 1938/--/-->
        >>> metadata.Metadata._convertValue('dcterms:created',
        ...     metadata.DateBetween(['1938','1939']))
        <music21.metadata.primitives.DateBetween 1938/--/-- to 1939/--/-->
        '''
        valueType: t.Type = properties.NSKEY_TO_VALUETYPE.get(nsKey, None)
        originalValue: t.Any = value

        if valueType is None:
            # not a standard property, convert to Text by default
            valueType = Text

        if isinstance(value, valueType):
            # already of appropriate type, no conversion necessary
            return value

        # We must convert
        if valueType is Text:
            if isinstance(value, str):
                return Text(value)
            return Text(str(value))

        if valueType is Copyright:
            # Copyright is derived from Text, and can be initialized from Text or str
            if isinstance(value, str):
                return Copyright(value)
            if isinstance(value, Text):
                return Copyright(value)
            raise exceptions21.MetadataException(
                f'invalid type for Copyright: {type(value).__name__}')

        if valueType is DateSingle:
            if isinstance(value, Text):
                value = str(value)
            if isinstance(value, (str, datetime.datetime, Date)):
                # If you want other DateSingle-derived types (DateRelative,
                # DateBetween, or DateSelection), you have to create those
                # yourself before adding/setting them.

                # pylint: disable=bare-except
                try:
                    return DateSingle(value)
                except:
                    # Couldn't convert; just return unconverted value
                    return originalValue
                # pylint: enable=bare-except

            raise exceptions21.MetadataException(
                f'invalid type for DateSingle: {type(value).__name__}')

        if valueType is Contributor:
            if isinstance(value, str):
                value = Text(value)

            if isinstance(value, Text):
                return Contributor(role=Metadata._nsKeyToContributorRole(nsKey), name=value)
            raise exceptions21.MetadataException(
                f'invalid type for Contributor: {type(value).__name__}')

        raise exceptions21.MetadataException('internal error: invalid valueType')

# -----------------------------------------------------------------------------
#   Utilities for use by the backward compatible APIs

    @staticmethod
    def _isBackwardCompatibleContributorNSKey(nsKey: str) -> bool:
        '''
        Determines if nsKey is the 'namespace:name' of a backward-compatible contributor.

        Test backward-compatible contributor (lyricist) (should return True)
        Test non-backward-compatible contributor (architect) (should return False)
        Test standard non-contributor (should return False)
        Test non-standard nsKey (should return False)
        Test empty string (should return False)
        Test None (should return False)

        >>> metadata.Metadata._isBackwardCompatibleContributorNSKey('marcrel:LYR')
        True
        >>> metadata.Metadata._isBackwardCompatibleContributorNSKey('marcrel:ARC')
        False
        >>> metadata.Metadata._isBackwardCompatibleContributorNSKey('dcterms:title')
        False
        >>> metadata.Metadata._isBackwardCompatibleContributorNSKey('humdrum:XXX')
        False
        >>> metadata.Metadata._isBackwardCompatibleContributorNSKey('')
        False
        >>> metadata.Metadata._isBackwardCompatibleContributorNSKey(None)
        False
        '''
        prop: PropertyDescription = properties.NSKEY_TO_PROPERTYDESCRIPTION.get(nsKey, None)
        if prop is None:
            return False

        return prop.isContributor and (
            prop.oldMusic21WorkId is not None
            or prop.uniqueName == 'otherContributor')

    @staticmethod
    def _backwardCompatibleContributorRoleToNSKey(role: str) -> str:
        '''
        Translates a backward-compatible contributor role to a standard
        'namespace:name' nsKey.  Returns 'marcrel:CTB' (a.k.a. 'otherContributor')
        if the role is a non-standard role (which is allowed during backward
        compatibility).

        >>> metadata.Metadata._backwardCompatibleContributorRoleToNSKey('lyricist')
        'marcrel:LYR'
        >>> metadata.Metadata._backwardCompatibleContributorRoleToNSKey('composer')
        'marcrel:CMP'
        >>> metadata.Metadata._backwardCompatibleContributorRoleToNSKey('architect')
        'marcrel:CTB'
        >>> metadata.Metadata._backwardCompatibleContributorRoleToNSKey('alternativeTitle')
        'marcrel:CTB'
        >>> metadata.Metadata._backwardCompatibleContributorRoleToNSKey('humdrum:XXX')
        'marcrel:CTB'
        >>> metadata.Metadata._backwardCompatibleContributorRoleToNSKey('')
        'marcrel:CTB'
        >>> metadata.Metadata._backwardCompatibleContributorRoleToNSKey(None)
        'marcrel:CTB'
        '''
        nsKey: t.Optional[str] = properties.M21WORKID_TO_NSKEY.get(role, None)
        if nsKey is None:
            # it's a non-standard role, so add this contributor with uniqueName='otherContributor'
            return 'marcrel:CTB'  # aka. 'otherContributor'

        prop: t.Optional[PropertyDescription] = (
            properties.NSKEY_TO_PROPERTYDESCRIPTION.get(nsKey, None))
        if prop is None or not prop.isContributor:
            return 'marcrel:CTB'  # a.k.a. 'otherContributor'

        return nsKey

    def _addBackwardCompatibleContributor(self, c: Contributor):
        '''
        Adds a backward-compatible contributor role to the metadata.

        >>> md = metadata.Metadata()
        >>> ly0 = metadata.Contributor(role='lyricist', name='Joe0')
        >>> ly1 = metadata.Contributor(role='lyricist', name='Joe1')
        >>> bf0 = metadata.Contributor(role='best friend', name='John0')
        >>> bf1 = metadata.Contributor(role='best friend', name='John1')
        >>> md._addBackwardCompatibleContributor(ly0)
        >>> md._addBackwardCompatibleContributor(ly1)
        >>> md._addBackwardCompatibleContributor(bf0)
        >>> md._addBackwardCompatibleContributor(bf1)
        >>> all = md.getAllNamedValues()
        >>> all
        [('marcrel:LYR', <music21.metadata.primitives.Contributor lyricist:Joe0>),
        ('marcrel:LYR', <music21.metadata.primitives.Contributor lyricist:Joe1>),
        ('marcrel:CTB', <music21.metadata.primitives.Contributor best friend:John0>),
        ('marcrel:CTB', <music21.metadata.primitives.Contributor best friend:John1>)]
        '''
        nsKey: str = self._backwardCompatibleContributorRoleToNSKey(c.role)
        self._add(nsKey, c, isCustom=False)

    def _getAllBackwardCompatibleContributors(self) -> t.List[Contributor]:
        allOut: t.List[Contributor] = []

        for nsKey, value in self._metadata.items():
            if not self._isBackwardCompatibleContributorNSKey(nsKey):
                continue

            if isinstance(value, list):
                allOut += value
            else:
                allOut.append(value)

        return allOut

    def _getBackwardCompatibleItemNoConversion(self, workId: str) -> t.Optional[t.Any]:
        result: t.Tuple[t.Any, ...] = self._getBackwardCompatibleItemsNoConversion(workId)
        if not result:  # None or empty tuple
            return None
        if len(result) == 1:
            return result[0]
        return 'MULTIPLE'

    def _setBackwardCompatibleItem(self, workId: str, value: t.Any):
        nsKey: str = properties.M21WORKID_TO_NSKEY.get(workId, None)
        if nsKey is not None:
            self._set(nsKey, value, isCustom=False)

    def _getBackwardCompatibleItemsNoConversion(self, workId: str) -> t.Tuple[t.Any, ...]:
        nsKey: str = properties.M21WORKID_TO_NSKEY.get(workId, None)
        if nsKey is None:
            return tuple()

        resultTuple: t.Tuple[t.Any, ...] = self._get(nsKey, isCustom=False)
        return resultTuple

    def _getBackwardCompatibleContributorNames(self, workId: str) -> t.List[str]:
        output: t.List[str] = []
        values: t.Tuple[t.Any, ...] = self._getBackwardCompatibleItemsNoConversion(workId)

        # return only one name of each contributor (backward compatible behavior)
        for v in values:
            output.append(str(v))
        return output

    def _setBackwardCompatibleContributorNames(self, workId: str, names: t.List[str]):
        # Auto-conversion from str to standard Contributor happens behind the scenes
        self._set(workId, names, isCustom=False)

# -----------------------------------------------------------------------------

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
    ('abstract', 'accessRights', 'accompanyingMaterialWriter', 'accrualMethod',
    'accrualPeriodicity', 'accrualPolicy', 'actNumber', 'actor', 'adapter',
    'afterwordAuthor', 'alternativeTitle', 'ambitus', 'animator', 'annotator',
    'architect', 'arranger', 'artist', 'associatedWork', 'attributedComposer',
    'audience', 'author', 'bibliographicCitation', 'calligrapher', 'cartographer',
    'choreographer', 'cinematographer', 'collaborator', 'collectionDesignation',
    'collotyper', 'commentator', 'commission', 'commissionedBy', 'compiler',
    'composer', 'composerAlias', 'composerCorporate', 'conceptor', 'conductor',
    'conformsTo', 'consultant', 'contractor', 'copyright', 'correspondent',
    'costumeDesigner', 'countryOfComposition', 'coverage', 'creator', 'curator',
    'dancer', 'date', 'dateAccepted', 'dateAvailable', 'dateCopyrighted',
    'dateCreated', 'dateIssued', 'dateModified', 'dateSubmitted', 'dateValid',
    'dedicatedTo', 'dedication', 'delineator', 'description', 'designer',
    'dialogAuthor', 'director', 'dissertant', 'distributor', 'draftsman',
    'editor', 'educationLevel', 'engineer', 'engraver', 'etcher', 'extent',
    'facsimilist', 'fileFormat', 'fileNumber', 'filePath', 'filmEditor', 'forger',
    'format', 'genericContributor', 'groupTitle', 'hasFormat', 'hasPart',
    'hasVersion', 'host', 'identifier', 'illuminator', 'illustrator',
    'instructionalMethod', 'instrumentalist', 'interviewee', 'interviewer',
    'introductionAuthor', 'inventor', 'isFormatOf', 'isPartOf', 'isReferencedBy',
    'isReplacedBy', 'isRequiredBy', 'isVersionOf', 'keySignatureFirst',
    'keySignatures', 'landscapeArchitect', 'language', 'librettist', 'license',
    'lightingDesigner', 'lithographer', 'localeOfComposition', 'lyricist',
    'manufacturer', 'mediator', 'medium', 'meetingOrganizer', 'metalEngraver',
    'moderator', 'movementName', 'movementNumber', 'musician', 'narrator',
    'noteCount', 'number', 'numberOfParts', 'opusNumber', 'orchestrator',
    'originator', 'otherContributor', 'otherDate', 'parentTitle', 'performer',
    'photographer', 'pitchHighest', 'pitchLowest', 'platemaker', 'popularTitle',
    'printmaker', 'producer', 'productionPersonnel', 'programmer',
    'projectConsultant', 'provenance', 'publisher', 'puppeteer', 'quarterLength',
    'quotationsAuthor', 'recordingEngineer', 'references', 'relation', 'renderer',
    'replaces', 'reporter', 'requires', 'researchTeamHead', 'researchTeamMember',
    'researcher', 'responsibleParty', 'restager', 'reviewer', 'rightsHolder',
    'scenarist', 'sceneNumber', 'scientificAdvisor', 'screenplayAuthor', 'scribe',
    'sculptor', 'secretary', 'setDesigner', 'singer', 'source', 'sourcePath',
    'spatialCoverage', 'speaker', 'standardsBody', 'storyteller', 'subject',
    'subtitle', 'surveyor', 'suspectedComposer', 'tableOfContents', 'teacher',
    'tempoFirst', 'temporalCoverage', 'tempos', 'textLanguage',
    'textOriginalLanguage', 'timeSignatureFirst', 'timeSignatures', 'title',
    'transcriber', 'translator', 'type', 'videographer', 'vocalist', 'volume',
    'volumeNumber', 'woodCutter', 'woodEngraver', 'writtenCommentator')

    '''

    # CLASS VARIABLES #

    # When changing this, be sure to update freezeThaw.py
    _additionalRichSearchAttributes = (
        'ambitus',
        'keySignatureFirst',
        'keySignatures',
        'noteCount',
        'numberOfParts',
        'pitchHighest',
        'pitchLowest',
        'quarterLength',
        'sourcePath',
        'tempoFirst',
        'tempos',
        'timeSignatureFirst',
        'timeSignatures',
    )

    allUniqueNames = tuple(sorted(Metadata.allUniqueNames + _additionalRichSearchAttributes))
    searchAttributes = tuple(sorted(Metadata.searchAttributes + _additionalRichSearchAttributes))

    # INITIALIZER #

    def __init__(self, *args, **keywords):
        super().__init__(*args, **keywords)
        self.ambitus = None
        self.keySignatureFirst = None
        self.keySignatures = []
        self.noteCount = None
        self.numberOfParts = None
        self.pitchHighest = None
        self.pitchLowest = None
        self.quarterLength = None
        self.sourcePath = ''
        self.tempoFirst = None
        self.tempos = []
        self.timeSignatureFirst = None
        self.timeSignatures = []

    def _getPluralAttribute(self, attributeName) -> t.Tuple[t.Union[str, int], ...]:
        # we have to implement this to add the RichMetadata searchAttributes, since
        # Metadata.search calls it.
        if attributeName in self._additionalRichSearchAttributes:
            value = getattr(self, attributeName)
            if value is None:
                return tuple()
            return (value,)

        return super()._getPluralAttribute(attributeName)

    # PUBLIC METHODS #

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
            '_metadata',
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

    def getSourcePath(self, streamObj):
        '''
        Get a string of the path after the corpus for the piece...useful for
        searching on corpus items without proper composer data...

        >>> rmd = metadata.RichMetadata()
        >>> b = corpus.parse('bwv66.6')
        >>> rmd.getSourcePath(b)
        'bach/bwv66.6.mxl'
        '''
        if not streamObj.metadata or not streamObj.metadata.filePath:
            return ''

        streamFp = streamObj.metadata.filePath
        if not isinstance(streamFp, pathlib.Path):
            streamFp = pathlib.Path(streamFp)

        try:
            relativePath = streamFp.relative_to(common.getCorpusFilePath())
            return relativePath.as_posix()
        except ValueError:
            return streamFp.as_posix()

    def update(self, streamObj):
        r'''
        Given a Stream object, update attributes with stored objects.

        >>> rmd = metadata.RichMetadata()
        >>> rmd.keySignatureFirst is None
        True
        >>> rmd.sourcePath
        ''

        >>> b = corpus.parse('bwv66.6')
        >>> rmd.update(b)
        >>> rmd.keySignatureFirst
        3
        >>> rmd.sourcePath
        'bach/bwv66.6.mxl'
        >>> rmd.numberOfParts
        4
        '''
        from music21 import key
        from music21 import meter
        from music21 import tempo

        environLocal.printDebug(['RichMetadata: update(): start'])

        flat = streamObj.flatten().sorted()

        self.numberOfParts = len(streamObj.parts)
        self.keySignatureFirst = None
        self.keySignatures = []
        self.tempoFirst = None
        self.tempos = []
        self.timeSignatureFirst = None
        self.timeSignatures = []

        self.sourcePath = self.getSourcePath(streamObj)

        # We combine element searching into a single loop to prevent
        # multiple traversals of the flattened stream.
        for element in flat:
            if isinstance(element, meter.TimeSignature):
                ratioString = element.ratioString
                if ratioString not in self.timeSignatures:
                    self.timeSignatures.append(ratioString)
            elif isinstance(element, key.KeySignature):
                if element.sharps not in self.keySignatures:
                    self.keySignatures.append(element.sharps)
            elif isinstance(element, tempo.TempoIndication):
                tempoIndicationString = str(element)
                if tempoIndicationString not in self.tempos:
                    self.tempos.append(tempoIndicationString)

        if self.timeSignatures:
            self.timeSignatureFirst = self.timeSignatures[0]
        if self.keySignatures:
            self.keySignatureFirst = self.keySignatures[0]
        if self.tempos:
            self.tempoFirst = self.tempos[0]

        # for element in flat:
        #    pitches = ()
        #    if isinstance(element, note.Note):
        #        pitches = (element.pitch,)
        #    elif isinstance(element, chord.Chord):
        #        pitches = element.pitches
        #    for pitch in pitches:
        #        if self.pitchHighest is None:
        #            self.pitchHighest = pitch
        #        if self.pitchLowest is None:
        #            self.pitchLowest = pitch
        #        if pitch.ps < self.pitchLowest.ps:
        #            self.pitchLowest = pitch
        #        elif self.pitchHighest.ps < pitch.ps:
        #            self.pitchHighest = pitch
        # self.pitchLowest = str(self.pitchLowest)
        # self.pitchHighest = str(self.pitchHighest)

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
        if analysisObject.minPitchObj is not None and analysisObject.maxPitchObj is not None:
            # may be none if no pitches are stored
            # presently, these are numbers; convert to a collection of pitches later
            self.pitchLowest = analysisObject.minPitchObj.nameWithOctave
            self.pitchHighest = analysisObject.maxPitchObj.nameWithOctave
        ambitusInterval = analysisObject.getSolution(streamObj)
        self.ambitus = AmbitusShort(semitones=ambitusInterval.semitones,
                                    diatonic=ambitusInterval.diatonic.simpleName,
                                    pitchLowest=self.pitchLowest,
                                    pitchHighest=self.pitchHighest,
                                    )

# -----------------------------------------------------------------------------

class Test(unittest.TestCase):
    pass


# -----------------------------------------------------------------------------
_DOC_ORDER: t.List[type] = []


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)


# -----------------------------------------------------------------------------
