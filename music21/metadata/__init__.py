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
>>> s.metadata.title = 'title'
>>> s.metadata.composer = 'composer'
>>> #_DOCS_SHOW s.show()

.. image:: images/moduleMetadata-01.*
    :width: 600

    A guide to this initial new implementation:

    - The guts of class Metadata are completely rewritten to support the new
        extensions, but all of Metadata's old APIs are still in place and
        are all backward compatible. There are new APIs (getItem, addItem
        et al) to access the new metadata extensions.

    - The old metadata implementation had a list of supported workIds, and also a
        list of supported contributor roles.  You could have more than one of each
        role, but only one of each workId.
        In the new implementation, I don't really treat contributor roles differently
        from other metadata.  I have a list of supported property terms, which are
        pulled from Dublin Core (namespace = 'dcterms'), MARC Relator codes (a.k.a.
        contributor roles, namespace = 'marcrel'), and several music21-specific things
        that I have to continue supporting even though I can't find any official list
        of terms that support them (namespace = 'music21').  An example is 'popularTitle'.
        You can have more than one of any of these.  That implies that I need two APIs
        for adding a new piece of metadata.  One that does "this is the new (only) value
        for this metadata property term", and one that does "this is a new value to add in to any
        other values you might have for this metadata property term".  They are:
        addItem() and setItem().  addItem adds the new item to the (possibly empty)
        list of values, and setItem removes any current value(s) before adding the item.

    - Primitives: Old code had DateXxxx and Text.  DateXxxx still works for Dublin Core
        et al (it's a superset of what is needed), but Text needs to add the ability to
        know whether or not the text has been translated, as well as a specified encoding
        scheme (a.k.a. what standard should I use to parse this string) so I have added
        new fields to Text in a backward-compatible way.

    - Metadata does not (yet) explicitly support client-specified namespaces, but there
        are a few APIs (getPersonalItem, addPersonalItem, setPersonalItem) that have no
        namespace at all, so clients can set anything they want and get it passed through.
        A parser could use this to set (say) 'humdrum:XXX' metadata that doesn't map to
        any standard metadata property, and a writer that understood 'humdrum' metadata
        could then write it back to a file.  Personal metadata can also include things
        that are specific to a particular person who is in the process of editing files,
        e.g. setPersonalItem('I have reached staff number', 1000). This can also be passed
        through to various file formats as long as there is a place for such a thing (e.g.
        'miscellaneous' in MusicXML).

    - A new type that drives a lot of the implementation: PropertyDescription
        A PropertyDescription is a namedtuple with multiple fields that describe
            a metadata property:
            abbrevCode is a (usually abbreviated) code for the property
            name is the official name of the property (the tail of the property term URI)
            label is the human readable name of the property
            namespace is a shortened form of the URI for the set of terms
                e.g. 'dcterms' means the property term is from the Dublin Core terms.
                'dcterms' is the shortened form of <http://purl.org/dc/terms/>
                e.g. 'marcrel' means the property term is from the MARC Relator terms.
                'marcrel' is the shortened form of <http://www.loc.gov/loc.terms/relators/>
            isContributor is whether or not the property describes a contributor.
            m21WorkId is the backward compatible music21 name for this property (this
                is not necessary if we are using the 'music21' namespace for a
                particular backward compatible property, when the workId can be found
                in the name field). Note that we use m21WorkId for music21 contributor
                roles when necessary, as well.
            m21Abbrev is the backward compatible music21 abbreviation for this property
                (again, not necessary if we are using the 'music21' namespace, when
                the abbreviation can be found in the code field)
            uniqueName is the official music21 name for this property, that is unique
                within the list of properties. There is always a unique name, but the
                uniqueName field is only set if m21WorkId or name is not unique enough.
                To get the unique name from a particular PropertyDescription, we do:
                    (desc.uniqueName if desc.uniqueName
                        else desc.m21WorkId if desc.m21WorkId
                        else desc.name)
            valueType is the actual type of the value that will be stored in the metadata.
                This allows auto-conversion to take place inside setItem/addItem, and is
                the type clients will always receive from getItem.

        The list of supported properties is Metadata._STDPROPERTYDESCS, and various lookup dicts
        are created from that in the class for later use.

    - Data structure for all the metadata:
        Metadata contains a _metadata attribute which is a dict, where the keys are
        f'{namespace}:{name}', and the value is either Any, or a List[Any] (for properties
        that have more than one value).  The old attributes copyright and date have been
        moved into the _metadata dict ('dcterms:rights' and 'dcterms:created'). Those are
        good PropertyDescription examples to look at to see the relationship between
        name, m21WorkId, and uniqueName.  We have maintained the old software attribute as
        a list of strings that is accessed directly, as before.

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
    'PropertyDescription'
]

from music21 import environment
environLocal = environment.Environment(os.path.basename(__file__))

PropertyDescription = namedtuple('PropertyDescription',
    ('abbrevCode', 'name', 'label', 'namespace', 'isContributor',
    'm21Abbrev', 'm21WorkId', 'uniqueName', 'valueType'),
    # All fields default to None, except for valueType, which defaults to Text
    defaults=(None, None, None, None, None,
    None, None, None, Text))

@dataclass
class FileInfo:
    path: t.Optional[Text] = None
    number: t.Optional[int] = None
    format: t.Optional[Text] = None

AmbitusShort = namedtuple('AmbitusShort',
                          ['semitones', 'diatonic', 'pitchLowest', 'pitchHighest'])

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
    ('actNumber', 'alternativeTitle', 'associatedWork', 'collectionDesignation',
     'commission', 'composer', 'copyright', 'countryOfComposition', 'date', 'dedication',
     'groupTitle', 'localeOfComposition', 'movementName', 'movementNumber', 'number',
     'opusNumber', 'parentTitle', 'popularTitle', 'sceneNumber', 'textLanguage',
     'textOriginalLanguage', 'title', 'volume')

    Plus anything that is in contributors...


    All contributors are stored in a .contributors list:

    >>> md.contributors
    [<music21.metadata.primitives.Contributor composer:Gershwin, George>]
    '''

    # CLASS VARIABLES #

    classSortOrder = -30

    '''
    _STDPROPERTYDESCS: each Tuple in this list is
        (abbrevCode, name, label, namespace, isContributor,
         m21Abbrev, m21WorkId, uniqueName, valueType)
    where:
      abbrevCode: str is a (usually abbreviated) code for the property
      name: str is the namespace's name of the property (the tail of the property term URI)
      label: str is the human readable name of the property
      namespace: str is a shortened form of the URI for the set of terms
          e.g. 'dcterms' means the property term is from the Dublin Core terms.
          'dcterms' is the shortened form of <http://purl.org/dc/terms/>
          e.g. 'marcrel' means the property term is from the MARC Relator terms.
          'marcrel' is the shortened form of <http://www.loc.gov/loc.terms/relators/>
      isContributor: bool is whether or not the property describes a contributor.
      m21Abbrev: str is the backward compatible music21 abbreviation for this property
          (again, not necessary if we are using the 'music21' namespace, when
          the abbreviation can be found in the code field)
      m21WorkId: str is the backward compatible music21 name for this property (this
          is not necessary if we are using the 'music21' namespace for a
          particular backward compatible property, when the workId can be found
          in the name field). Note that we use m21WorkId for music21 contributor
          roles when necessary, as well.
      uniqueName: str is the official music21 name for this property, that is unique
          within the list of properties. There is always a unique name, but the
          uniqueName field is only set if m21WorkId or name is not unique enough.
          To get the unique name from a particular PropertyDescription, we do:
              (desc.uniqueName if desc.uniqueName
                  else desc.m21WorkId if desc.m21WorkId
                  else desc.name)
      valueType: Type is the actual type of the value that will be stored in the metadata.
          This allows auto-conversion to take place inside setItem/addItem, and is
          the type clients will always receive from getItem.

    _STDPROPERTYDESCS is defined at the bottom of class Metadata (the list is
    ~2000 lines long), but here are a few entries to give a taste:

    _STDPROPERTYDESCS: Tuple[PropertyDescription] = (
        # abstract: A summary of the resource.
        # nsKey: 'dcterms:abstract'
        # unique name is 'abstract', no backward compatible access
        # type of _metadata['dcterms:abstract'] is Text
        PropertyDescription(
                 abbrevCode='AB',
                 name='abstract',
                 label='Abstract',
                 namespace='dcterms',
                 isContributor=False),

        # alternative: An alternative name for the resource.
        # nsKey: 'dcterms:alternative'
        # unique name: 'alternativeTitle'
        # backward compatible access: md.alternativeTitle or md.ota
        # type of _metadata['dcterms:alternative'] is Text
        PropertyDescription(
                 abbrevCode='ALT',
                 name='alternative',
                 label='Alternative Title',
                 namespace='dcterms',
                 m21Abbrev='ota',
                 m21WorkId='alternativeTitle',
                 isContributor=False),

        # rights: Information about rights held in and over the resource.
        # nsKey: 'dcterms:rights'
        # unique name: 'copyright'
        # backward compatible access: md.copyright
        # type of _metadata['dcterms:rights'] is Text
        PropertyDescription(
                 abbrevCode='RT',
                 name='rights',
                 label='Rights',
                 namespace='dcterms',
                 m21WorkId='copyright', # no abbrev
                 isContributor=False),

        # created: Date of creation of the resource.
        # nsKey: 'dcterms:created'
        # unique name: 'dateCreated'
        # backward compatible access: md.date
        # type of _metadata['dcterms:created'] is derived from DateSingle
        PropertyDescription(
                 abbrevCode='CRD',
                 name='created',
                 label='Date Created',
                 namespace='dcterms',
                 m21WorkId='date',  # no abbrev
                 uniqueName='dateCreated',
                 valueType=DateSingle, # including DateRelative, DateBetween, DateSelection
                 isContributor=False),

        # composer: a person or organization who creates a musical work,
        #   usually a piece of music in manuscript or printed form.
        # nsKey: 'marcrel:CMP'
        # unique name: 'composer'
        # backward compatible access: md.composer
        # type of _metadata['marcrel:CMP'] is Contributor
        PropertyDescription(
                 abbrevCode='cmp',
                 name='CMP',
                 label='Composer',
                 namespace='marcrel',
                 m21WorkId='composer',
                 m21Abbrev='com',
                 valueType=Contributor,
                 isContributor=True),
    '''

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

    # add more as properties/import exists
    searchAttributes = tuple(sorted([
        'composer',
        'copyright',
        'date',
    ] + list(workIdAbbreviationDict.values())))

    workIdLookupDict = {}
    for key, value in workIdAbbreviationDict.items():
        workIdLookupDict[value.lower()] = key

    # INITIALIZER #

    def __init__(self, *args, **keywords):
        super().__init__()

        self._metadata: Dict = {}
        self.software: List[str] = [defaults.software]

        # For backward compatibility, we allow the setting of workIds or
        # abbreviations via **keywords
        for abbreviation, workId in self.workIdAbbreviationDict.items():
            # abbreviation = workIdToAbbreviation(id)
            if workId in keywords:
                nsKey: str = self._M21WORKID2NSKEY[workId]
                self._metadata[nsKey] = Text(keywords[workId])
            elif abbreviation in keywords:
                nsKey: str = self._M21ABBREV2NSKEY[abbreviation]
                self._metadata[nsKey] = Text(keywords[abbreviation])

        # search for any keywords that match attributes
        # these are for direct Contributor access, must have defined
        # properties
        for attr in ['composer', 'date', 'title']:
            if attr in keywords:
                setattr(self, attr, keywords[attr])


# -----------------------------------------------------------------------------
# PUBLIC APIs:
#   {get,add,set}{Item,Items}
#   {get,add,set}Personal{Item,Items}
#   getAllItems(skipContributors=False)
#   getAllContributorItems


    # never returns a list, always returns None, or the first item
    def getItem(self,
                key: str,
                namespace: Optional[str] = None) -> Optional[Any]:
        '''
        Returns the first item stored in metadata with this key and namespace.

        If namespace is provided, the key will be interpreted as name or
        abbrevCode (within that namespace). Either will work. If namespace is
        None, the key will be interpreted as uniqueName if possible. If the
        key is not a uniqueName, it will be used as is, so 'namespace:name'
        will work.  Personal item names should not be used here, since they
        may be interpreted as uniqueNames, with unpredictable results.

        Test getItem when the item isn't there.

        >>> md = metadata.Metadata()
        >>> md.getItem('title') # uniqueName
        >>> md.getItem('title', namespace='dcterms') # name, namespace
        >>> md.getItem('T', namespace='dcterms') # abbrevCode, namespace
        >>> md.getItem('dcterms:title') # 'namespace:name'

        Test getItem when the item is there:

        >>> md.setItem('title', metadata.Text('Caveat Emptor'))
        >>> md.getItem('title') # uniqueName
        <music21.metadata.primitives.Text Caveat Emptor>
        >>> md.getItem('title', namespace='dcterms') # name, namespace
        <music21.metadata.primitives.Text Caveat Emptor>
        >>> md.getItem('T', namespace='dcterms') # abbrevCode, namespace
        <music21.metadata.primitives.Text Caveat Emptor>
        >>> md.getItem('dcterms:title') # 'namespace:name'
        <music21.metadata.primitives.Text Caveat Emptor>
        '''
        return self._getItem(key, namespace)

    # always returns a List, which might be empty, have one item, or multiple items
    def getItems(self,
                 key: str,
                 namespace: Optional[str] = None) -> List[Any]:
        '''
        Returns all the items stored in metadata with this key and namespace.
        The returned value is always a list. If there are no items, [] is
        returned.  If there is only one item, [thatItem] is returned.

        If namespace is provided, the key will be interpreted as name or
        abbrevCode (within that namespace). Either will work. If namespace is
        None, the key will be interpreted as uniqueName if possible. If the
        key is not a uniqueName, it will be used as is, so 'namespace:name'
        will work.  Personal item names should not be used here, since they
        may be interpreted as uniqueNames, with unpredictable results.

        Test when there is no title.

        >>> md = metadata.Metadata()
        >>> md.getItems('title')
        []

        Test when there is one title.

        >>> md.setItem('title', metadata.Text('Heroic Symphony'))
        >>> md.getItems('title')
        [<music21.metadata.primitives.Text Heroic Symphony>]

        Test when there are two titles.

        >>> md.addItem('T', metadata.Text('The Heroic Symphony'), namespace='dcterms')
        >>> items = md.getItems('title', namespace='dcterms')
        >>> items[0]
        <music21.metadata.primitives.Text Heroic Symphony>
        >>> items[1]
        <music21.metadata.primitives.Text The Heroic Symphony>
        '''
        return self._getItems(key, namespace)

    # adds a single item
    def addItem(self,
                key: str,
                value: Any,
                namespace: Optional[str] = None):
        '''
        Adds a single item with this key and namespace.

        If namespace is provided, the key will be interpreted as name or
        abbrevCode (within that namespace). Either will work. If namespace is
        None, the key will be interpreted as uniqueName if possible. If the
        key is not a uniqueName, it will be used as is, so 'namespace:name'
        will work.  Personal item names should not be used here, since they
        may be interpreted as uniqueNames, with unpredictable results.

        Test adding as str instead of Text (it will be auto-converted to Text)

        >>> md = metadata.Metadata()
        >>> md.addItem('suspectedComposer', 'Ludwig von Beethoven')
        >>> md.getItem('suspectedComposer')
        <music21.metadata.primitives.Contributor suspectedComposer:Ludwig von Beethoven>
        '''
        self._addItem(key, value, namespace)

    # adds a list of items
    def addItems(self,
                key: str,
                valueList: List[Any],
                namespace: Optional[str] = None):
        '''
        Adds multiple items with this key and namespace.

        If namespace is provided, the key will be interpreted as name or
        abbrevCode (within that namespace). Either will work. If namespace is
        None, the key will be interpreted as uniqueName if possible. If the
        key is not a uniqueName, it will be used as is, so 'namespace:name'
        will work.  Personal item names should not be used here, since they
        may be interpreted as uniqueNames, with unpredictable results.

        >>> md = metadata.Metadata()
        >>> md.addItems('title', [metadata.Text('Caveat Emptor', language='la'),
        ...                       metadata.Text('Buyer Beware',  language='en')])
        >>> titles = md.getItems('title')
        >>> len(titles)
        2
        >>> titles[0]
        <music21.metadata.primitives.Text Caveat Emptor>
        >>> titles[0].language
        'la'
        >>> titles[1]
        <music21.metadata.primitives.Text Buyer Beware>
        >>> titles[1].language
        'en'
        >>> md.getItem('title')
        <music21.metadata.primitives.Text Caveat Emptor>
        '''
        self._addItems(key, valueList, namespace)

    # sets a single item (overwriting all existing items)
    def setItem(self,
                key: str,
                value: Any,
                namespace: Optional[str] = None):
        '''
        Replaces any items stored in metadata with this key and namespace, with value.
        If namespace is provided, the key will be interpreted as name or
        abbrevCode (within that namespace). Either will work. If namespace is
        None, the key will be interpreted as uniqueName or assumed to be of the
        form 'namespace:name'.

        >>> md = metadata.Metadata()
        >>> md.setItem('librettist', metadata.Text('Joe Libretto'))
        >>> md.getItem('librettist') # uniqueName
        <music21.metadata.primitives.Contributor librettist:Joe Libretto>
        >>> md.getItem('LBT', namespace='marcrel') # name, namespace
        <music21.metadata.primitives.Contributor librettist:Joe Libretto>
        >>> md.getItem('lbt', namespace='marcrel') # abbrevCode, namespace
        <music21.metadata.primitives.Contributor librettist:Joe Libretto>
        >>> md.getItem('marcrel:LBT') # 'namespace:name'
        <music21.metadata.primitives.Contributor librettist:Joe Libretto>
        >>> md.librettist # backward compatible access
        'Joe Libretto'
        >>> md.contributors # backward compatible access
        [<music21.metadata.primitives.Contributor librettist:Joe Libretto>]
        '''
        self._setItem(key, value, namespace)

    # sets a list of items (overwriting all existing items)
    def setItems(self,
                key: str,
                valueList: List[Any],
                namespace: Optional[str] = None):
        '''
        Replaces any items stored in metadata with this key and namespace, with
        multiple values.

        If namespace is provided, the key will be interpreted as name or
        abbrevCode (within that namespace). Either will work. If namespace is
        None, the key will be interpreted as uniqueName or assumed to be of the
        form 'namespace:name'.

        >>> md = metadata.Metadata()
        >>> md.setItems('librettist', [metadata.Text('Joe Libretto'),
        ...                            metadata.Text('John Smith')])

        >>> items = md.getItems('librettist') # uniqueName
        >>> len(items)
        2
        >>> items[0]
        <music21.metadata.primitives.Contributor librettist:Joe Libretto>
        >>> items[1]
        <music21.metadata.primitives.Contributor librettist:John Smith>

        >>> items = md.getItems('LBT', namespace='marcrel') # name, namespace
        >>> len(items)
        2
        >>> items[0]
        <music21.metadata.primitives.Contributor librettist:Joe Libretto>
        >>> items[1]
        <music21.metadata.primitives.Contributor librettist:John Smith>

        >>> items = md.getItems('lbt', namespace='marcrel') # abbrevCode, namespace
        >>> len(items)
        2
        >>> items[0]
        <music21.metadata.primitives.Contributor librettist:Joe Libretto>
        >>> items[1]
        <music21.metadata.primitives.Contributor librettist:John Smith>

        >>> items = md.getItems('marcrel:LBT') # 'namespace:name'
        >>> len(items)
        2
        >>> items[0]
        <music21.metadata.primitives.Contributor librettist:Joe Libretto>
        >>> items[1]
        <music21.metadata.primitives.Contributor librettist:John Smith>

        >>> md.librettists # backward compatible access
        ['Joe Libretto', 'John Smith']

        >>> md.librettist # backward compatible access
        'Joe Libretto'

        >>> items = md.contributors # backward compatible access
        >>> len(items)
        2
        >>> items[0]
        <music21.metadata.primitives.Contributor librettist:Joe Libretto>
        >>> items[1]
        <music21.metadata.primitives.Contributor librettist:John Smith>
        '''
        self._setItems(key, valueList, namespace)

    # Notes about personal metadata keys:
    # You can use nonstandard nsKeys like 'humdrum:XXX', or you can
    # just make up your own keys like 'excerpt-start-measure'.
    #
    # You can use a personal name that is the same as an existing
    # unique name of a standard supported property, but that is
    # not recommended:
    #
    # md.addItems('composer', ['Ludwig', 'Wolfgang'])
    # md.addPersonalItem('composer', 'Not a contributor')
    # md.getAllContributorItems()
    # [
    #   ('marcrel:CMP', <music21.metadata.primitives.Contributor composer:Ludwig>),
    #   ('marcrel:CMP', <music21.metadata.primitives.Contributor composer:Wolfgang>),
    # ]
    # md.getAllItems(skipContributors=True)
    # [
    #   ('composer', <music21.metadata.primitives.Text Not a contributor>),
    # ]
    #


    def getPersonalItem(self, key: str) -> Any:
        return self._getItem(key, namespace=None, personal=True)

    def getPersonalItems(self, key: str) -> List[Any]:
        return self._getItems(key, namespace=None, personal=True)

    def addPersonalItem(self, key: str, value: Any):
        self._addItem(key, value, namespace=None, personal=True)

    def addPersonalItems(self, key: str, valueList: List[Any]):
        self._addItems(key, valueList, namespace=None, personal=True)

    def setPersonalItem(self, key: str, value: Any):
        self._setItem(key, value, namespace=None, personal=True)

    def setPersonalItems(self, key: str, valueList: List[Any]):
        self._setItems(key, valueList, namespace=None, personal=True)

    # This is the extended version of all().  The tuple's key is an nsKey (but of course
    # there may be no namespace for personal metadata items).
    def getAllItems(self, skipContributors=False) -> List[Tuple[str, Any]]:
        '''
        Returns all values stored in this metadata as a list of (nsKey, value) tuples.
        nsKeys with multiple values will appear multiple times in the list (rather
        than appearing once, with a value that is a list of values).

        >>> md = metadata.Metadata()
        >>> md.addItems('composer', ['Ludwig', 'Wolfgang'])
        >>> md.addPersonalItem('composer', 'Not a contributor')
        >>> md.addItem('title', '[title of show]')
        >>> md.addPersonalItem('excerpt-start-measure', 1234)
        >>> all = md.getAllItems()
        >>> len(all)
        5
        >>> all[0]
        ('marcrel:CMP', <music21.metadata.primitives.Contributor composer:Ludwig>)
        >>> all[1]
        ('marcrel:CMP', <music21.metadata.primitives.Contributor composer:Wolfgang>)
        >>> all[2]
        ('composer', <music21.metadata.primitives.Text Not a contributor>)
        >>> all[3]
        ('dcterms:title', <music21.metadata.primitives.Text [title of show]>)
        >>> all[4]
        ('excerpt-start-measure', <music21.metadata.primitives.Text 1234>)
        >>> all = md.getAllItems(skipContributors=True)
        >>> len(all)
        3
        >>> all[0]
        ('composer', <music21.metadata.primitives.Text Not a contributor>)
        >>> all[1]
        ('dcterms:title', <music21.metadata.primitives.Text [title of show]>)
        >>> all[2]
        ('excerpt-start-measure', <music21.metadata.primitives.Text 1234>)
        '''
        allOut: List[Tuple[str, Any]] = []

        for nsKey, value in self._metadata.items():
            if skipContributors and self._isContributorNSKey(nsKey):
                continue

            if isinstance(value, list):
                for v in value:
                    allOut.append((nsKey, v))
            else:
                allOut.append((nsKey, value))

        # unlike backward compatible API Metadata.all, getAllItems does not sort.
        return allOut

    def getAllContributorItems(self) -> List[Tuple[str, Any]]:
        '''
        Returns all contributors stored in this metadata as a list of (nsKey, value) tuples.

        >>> md = metadata.Metadata()
        >>> md.addPersonalItem('composer', 'Not a contributor')
        >>> md.addItem('title', '[title of show]')
        >>> md.addPersonalItem('excerpt-start-measure', 1234)
        >>> md.addItems('composer', ['Ludwig', 'Wolfgang'])
        >>> md.addItem('librettist', 'Joe')
        >>> all = md.getAllContributorItems()
        >>> len(all)
        3
        >>> all[0]
        ('marcrel:CMP', <music21.metadata.primitives.Contributor composer:Ludwig>)
        >>> all[1]
        ('marcrel:CMP', <music21.metadata.primitives.Contributor composer:Wolfgang>)
        >>> all[2]
        ('marcrel:LBT', <music21.metadata.primitives.Contributor librettist:Joe>)
        '''

        allOut: List[Tuple[str, Contributor]] = []

        for nsKey, value in self._metadata.items():
            if not self._isContributorNSKey(nsKey):
                continue

            if isinstance(value, list):
                for v in value:
                    allOut.append((nsKey, v))
            else:
                allOut.append((nsKey, value))

        # unlike backward compatible API Metadata.all, getAllContributorItems does not sort.
        return allOut

# -----------------------------------------------------------------------------
#   A few static utility routines for clients calling public APIs
    @staticmethod
    def uniqueNameToNSKey(uniqueName: str) -> Optional[str]:
        '''
        Translates a unique name to the associated standard property's NSKey.
        Returns None if no such associated standard property can be found.

        >>> metadata.Metadata.uniqueNameToNSKey('librettist')
        'marcrel:LBT'
        >>> metadata.Metadata.uniqueNameToNSKey('not a standard property')
        >>> metadata.Metadata.uniqueNameToNSKey(None)
        >>> metadata.Metadata.uniqueNameToNSKey('alternativeTitle')
        'dcterms:alternative'
        '''
        if not uniqueName:
            return None
        return Metadata._UNIQUENAME2NSKEY.get(uniqueName, None)

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
        >>> metadata.Metadata.isContributorUniqueName('not a standard property')
        False
        >>> metadata.Metadata.isContributorUniqueName(None)
        False
        '''
        if not uniqueName:
            return False
        prop: PropertyDescription = Metadata._UNIQUENAME2STDPROPERTYDESC.get(uniqueName, None)
        if prop is None:
            return False

        return prop.isContributor

    @staticmethod
    def nsKeyToUniqueName(nsKey: str) -> Optional[str]:
        '''
        Translates a standard property NSKey to that standard property's
        uniqueName.
        Returns None if no such standard property exists.

        >>> metadata.Metadata.nsKeyToUniqueName('marcrel:LBT')
        'librettist'
        >>> metadata.Metadata.nsKeyToUniqueName('not a standard nskey')
        >>> metadata.Metadata.nsKeyToUniqueName(None)
        >>> metadata.Metadata.nsKeyToUniqueName('dcterms:alternative')
        'alternativeTitle'
        '''
        if not nsKey:
            return None
        uniqueName: Optional[str] = Metadata._NSKEY2UNIQUENAME.get(nsKey, None)
        return uniqueName


    @staticmethod
    def nsKeyToContributorUniqueName(nsKey: str) -> Optional[str]:
        '''
        Translates a standard contributor property NSKey to that standard
        contributor property's uniqueName.
        Returns None if no such standard contributor property exists.

        >>> metadata.Metadata.nsKeyToContributorUniqueName('marcrel:LBT')
        'librettist'
        >>> metadata.Metadata.nsKeyToContributorUniqueName('not a standard nskey')
        >>> metadata.Metadata.nsKeyToContributorUniqueName(None)
        >>> metadata.Metadata.nsKeyToContributorUniqueName('dcterms:alternative')
        '''
        if not nsKey:
            return None
        uniqueName: Optional[str] = Metadata._NSKEY2CONTRIBUTORUNIQUENAME.get(nsKey, None)
        return uniqueName

    # -----------------------------------------------------------------------------
#   Backward compatible public APIs
#   TODO: Consider deprecating some of these (the ones that are too limiting)

    @property
    def contributors(self) -> List[Contributor]:
        '''
        Returns a list of all the backward-compatible Contributors found in
        the metadata.
        Returns [] if no such backward-compatible Contributors exist.

        >>> md = metadata.Metadata()
        >>> md.setItems('composer', ['Ludwig', 'Wolfgang'])
        >>> md.setItem('librettist', 'Joe')
        >>> md.addItem('architect', 'John')      # not backward-compatible
        >>> md.addItem('title', 'Caveat Emptor') # not a contributor
        >>> contribs = md.contributors
        >>> len(contribs)
        3
        >>> contribs[0]
        <music21.metadata.primitives.Contributor composer:Ludwig>
        >>> contribs[1]
        <music21.metadata.primitives.Contributor composer:Wolfgang>
        >>> contribs[2]
        <music21.metadata.primitives.Contributor librettist:Joe>
        '''

        # This was just a data attribute before.  Hopefully no-one is calling
        # md.contributors.append(c).  I did a global search on github for
        # 'music21' 'contributors', and all code that modified it that I found
        # were in music21 forks.  So I think we're OK making this a read-only
        # property that we generate on the fly.
        output: List[Contributor] = self._getAllBackwardCompatibleContributors()
        return output

    @property
    def copyright(self) -> Optional[Copyright]:
        '''
        Returns the backward compatible Copyright (i.e. the first one in the metadata).
        Returns None if no Copyright exists in the metadata.

        >>> md = metadata.Metadata()
        >>> md.copyright
        >>> md.setItem('dcterms:rights', 'Copyright © 1984 All Rights Reserved')
        >>> md.addItem('dcterms:rights', 'Lyrics copyright © 1987 All Rights Reserved')
        >>> md.setItems('composer', ['Ludwig', 'Wolfgang'])
        >>> md.setItem('librettist', 'Joe')
        >>> md.addItem('architect', 'John')
        >>> md.addItem('title', 'Caveat Emptor')
        >>> md.copyright
        <music21.metadata.primitives.Copyright Copyright © 1984 All Rights Reserved>

        >>> md = metadata.Metadata()
        >>> md.copyright
        >>> md.setItem('dcterms:rights', 'Copyright © 1984 All Rights Reserved')
        >>> md.addItem('dcterms:rights', 'Lyrics copyright © 1987 All Rights Reserved')
        >>> md.copyright = 'Copyright © 1984 from str'
        >>> md.copyright
        <music21.metadata.primitives.Copyright Copyright © 1984 from str>
        >>> md.getItems('dcterms:rights')
        [<music21.metadata.primitives.Copyright Copyright © 1984 from str>]
        >>> md.copyright = metadata.Text('Copyright ©    1984 from Text')
        >>> md.getItems('dcterms:rights')
        [<music21.metadata.primitives.Copyright Copyright © 1984 from Text>]
        >>> md.copyright = metadata.Copyright('Copyright © 1984 from Copyright', role='something')
        >>> md.getItems('dcterms:rights')
        [<music21.metadata.primitives.Copyright Copyright © 1984 from Copyright>]
        '''
        output: Optional[Any] = self._getBackwardCompatibleItemNoConversion('copyright')
        if output is not None and not isinstance(output, Copyright):
            raise exceptions21.MetadataException('internal error: invalid copyright value type')
        return output

    @copyright.setter
    def copyright(self, newCopyright: Optional[Union[str, Text, Copyright]]):
        '''
        Sets the Copyright in a backward-compatible way (i.e. it removes all
        previous Copyright metadata items). newCopyright can be None or a
        Copyright object (or str/Text, which we convert internally to Copyright)
        '''
        self._setBackwardCompatibleItem('copyright', newCopyright)

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
         ('movementName', 'Sonata da Chiesa, No. I (opus 3, no. 1)')]

        Skip contributors is there to help with musicxml parsing -- there's no reason for it
        except that we haven't exposed enough functionality yet:

        >>> c.metadata.date = metadata.DateRelative('1689', 'onOrBefore')
        >>> c.metadata.localeOfComposition = 'Rome'
        >>> c.metadata.all(skipContributors=True)
        [('copyright', '© 2014, Creative Commons License (CC-BY)'),
         ('date', '1689/--/-- or earlier'),
         ('localeOfComposition', 'Rome'),
         ('movementName', 'Sonata da Chiesa, No. I (opus 3, no. 1)')]
        '''
        # pylint: disable=undefined-variable
        allOut = {}

        searchAttributes = self.searchAttributes

        for thisAttribute in sorted(set(searchAttributes)):
            try:
                val = getattr(self, thisAttribute)
            except AttributeError:
                continue

            if skipContributors:
                if isinstance(val, Contributor):
                    continue
                if thisAttribute == 'composer':
                    continue
            if val == 'None' or not val:
                continue
            allOut[str(thisAttribute)] = str(val)

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

    def __getattr__(self, name):
        r'''
        Utility attribute access for attributes that do not yet have property
        definitions.
        '''
        match = None
        for abbreviation, workId in self.workIdAbbreviationDict.items():
            # for id in WORK_IDS:
            # abbreviation = workIdToAbbreviation(id)
            if name == workId:
                match = workId
                break
            elif name == abbreviation:
                match = workId
                break
        if match is None:
            raise AttributeError(f'object has no attribute: {name}')
        # _getBackwardCompatibleItem returns None or str(value)
        # For backward compatibility reasons, we need to return 'None' instead of None
        result = self._getBackwardCompatibleItem(match)
        if result is not None:
            return result
        return 'None'

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
                value = getattr(self, field)
                valueFieldPairs.append((value, field))
                match = True
            except AttributeError:
                pass
            if not match:
                for searchAttribute in self.searchAttributes:
                    # environLocal.printDebug(['comparing fields:', f, field])
                    # look for partial match in all fields
                    if field.lower() in searchAttribute.lower():
                        value = getattr(self, searchAttribute)
                        valueFieldPairs.append((value, searchAttribute))
                        match = True
                        break
        else:  # get all fields
            for innerField in self.searchAttributes:
                value = getattr(self, innerField)
                valueFieldPairs.append((value, innerField))

        # now search all contributors.
        for contrib in self.contributors:
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
                # re.I makes case insensitive
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
        three character abbreviation. The following work id abbreviations and
        their full id string are given as follows. In many cases the Metadata
        object support properties for convenient access to these work ids.

        Id abbreviations and strings::
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
        >>> md.getItem('countryOfComposition')
        <music21.metadata.primitives.Text Latvia>

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
        return self._getBackwardCompatibleItem('alternativeTitle')

    @alternativeTitle.setter
    def alternativeTitle(self, value):
        self._setBackwardCompatibleItem('alternativeTitle', Text(value))

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
        >>> md.composer = 'Beach, Amy Marcy Cheney'
        >>> md.composer
        'Beach, Amy Marcy Cheney'
        '''
        return self._getBackwardCompatibleItem('composer')

    @composer.setter
    def composer(self, value):
        self._setBackwardCompatibleItem('composer', value)

    @property
    def composers(self) -> List[str]:
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

    @composers.setter
    def composers(self, value: List[str]) -> None:
        self._setBackwardCompatibleContributorNames('composer', value)


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
        # _getBackwardCompatibleItem returns None or str(value)
        # For backward compatibility reasons, we need to return 'None' instead of None
        output = self._getBackwardCompatibleItem('date')
        if output is not None:
            return output
        return 'None'

    @date.setter
    def date(self, value):
        self._setBackwardCompatibleItem('date', value)

    @property
    def localeOfComposition(self):
        r'''
        Get or set the locale of composition, or origin, of the work.
        '''
        return self._getBackwardCompatibleItem('localeOfComposition')

    @localeOfComposition.setter
    def localeOfComposition(self, value):
        self._setBackwardCompatibleItem('localeOfComposition', Text(value))

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
        return self._getBackwardCompatibleItem('librettist')

    @librettist.setter
    def librettist(self, value):
        self._setBackwardCompatibleItem('librettist', value)

    @property
    def librettists(self) -> List[str]:
        r'''
        Gets or sets a list of librettists for this work:

        >>> md = metadata.Metadata(title='Madama Butterfly')
        >>> md.librettists = ['Illica, Luigi', 'Giacosa, Giuseppe']
        >>> md.librettists
        ['Illica, Luigi', 'Giacosa, Giuseppe']

        Should be distinguished from lyricists etc.
        '''
        return self._getBackwardCompatibleContributorNames('librettist')

    @librettists.setter
    def librettists(self, value: List[str]) -> None:
        self._setBackwardCompatibleContributorNames('librettist', value)

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
        '''
        return self._getBackwardCompatibleItem('lyricist')

    @lyricist.setter
    def lyricist(self, value):
        self._setBackwardCompatibleItem('lyricist', value)

    @property
    def lyricists(self) -> List[str]:
        r'''
        Gets or sets a list of lyricists for this work:

        >>> md = metadata.Metadata(title='Rumors')
        >>> md.lyricists = ['Buckingham, Lindsey', 'McVie, Christine', 'Nicks, Stevie']
        >>> md.lyricists
        ['Buckingham, Lindsey', 'McVie, Christine', 'Nicks, Stevie']

        Should be distinguished from librettists etc.
        '''
        return self._getBackwardCompatibleContributorNames('lyricist')

    @lyricists.setter
    def lyricists(self, value: List[str]) -> None:
        self._setBackwardCompatibleContributorNames('lyricist', value)


    @property
    def movementName(self):
        r'''
        Get or set the movement title.

        Note that a number of pieces from various MusicXML datasets have
        the piece title as the movement title. For instance, the Bach
        Chorales, since they are technically movements of larger cantatas.
        '''
        return self._getBackwardCompatibleItem('movementName')

    @movementName.setter
    def movementName(self, value):
        self._setBackwardCompatibleItem('movementName', Text(value))

    @property
    def movementNumber(self) -> Optional[str]:
        r'''
        Get or set the movement number.

        >>> md = metadata.Metadata(title='Ode to Joy')
        >>> md.movementNumber = 3

        Note that movement numbers are always returned as strings!  This may
        change in the future.

        >>> md.movementNumber
        '3'
        '''
        return self._getBackwardCompatibleItem('movementNumber')

    @movementNumber.setter
    def movementNumber(self, value):
        self._setBackwardCompatibleItem('movementNumber', Text(value))

    @property
    def number(self):
        r'''
        Get or set the number of the work within a collection of pieces.
        (for instance, the number within a collection of ABC files)

        Note that numbers are always returned as strings!  This may
        change in the future.
        '''
        return self._getBackwardCompatibleItem('number')

    @number.setter
    def number(self, value):
        self._setBackwardCompatibleItem('number', Text(value))

    @property
    def opusNumber(self):
        r'''
        Get or set the opus number.

        Note that opusNumbers are always returned as strings!  This may
        change in the future.
        '''
        return self._getBackwardCompatibleItem('opusNumber')

    @opusNumber.setter
    def opusNumber(self, value):
        self._setBackwardCompatibleItem('opusNumber', Text(value))

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

    @title.setter
    def title(self, value):
        self._setBackwardCompatibleItem('title', Text(value))

# -----------------------------------------------------------------------------

    # Support routines (many of them static).  For use internally, and a few of them
    # externally.

    @staticmethod
    def _nsKey(key: str, namespace: Optional[str] = None, personal: bool = False) -> str:
        # Caller is required to check backward compatibility (either before or after); this
        # routine is general.
        # If namespace is provided, the key will be interpreted as name or
        # abbrevCode (within that namespace). Either will work. If namespace is
        # None, the key will be interpreted as uniqueName or assumed to be of the
        # form 'namespace:name'.
        if not key:
            return ''

        if personal:
            return key

        if namespace:
            # check if key is an abbreviation in this namespace
            nsKeyForAbbrev: str = Metadata._NAMESPACEABBREV2NSKEY.get((namespace, key), None)
            if nsKeyForAbbrev:
                return nsKeyForAbbrev
            # it wasn't an abbreviation, so assume it's a name
            return f'{namespace}:{key}'

        # No namespace: key might be uniqueName, from which we can look up the nsKey
        nsKeyForUniqueName: str = Metadata._UNIQUENAME2NSKEY.get(key, None)
        if nsKeyForUniqueName:
            return nsKeyForUniqueName

        # Key might already be of the form 'namespace:name', just return it
        return key

    @staticmethod
    def _isContributorNSKey(nsKey: str) -> bool:
        if not nsKey:
            return False
        prop: PropertyDescription = Metadata._NSKEY2STDPROPERTYDESC.get(nsKey, None)
        if prop is None:
            return False

        return prop.isContributor

    @staticmethod
    def _nsKeyToContributorRole(nsKey: str) -> Optional[str]:
        prop: PropertyDescription = Metadata._NSKEY2STDPROPERTYDESC.get(nsKey, None)
        if prop is None:
            return None
        if not prop.isContributor:
            return None

        # it's a small-c contributor
        if prop.namespace == 'music21':
            # it's in the music21 namespace, so it's a big-C Contributor,
            # and Contributor.role can be found in prop.name
            return prop.name

        # it's a small-c contributor that's not in the music21 namespace
        if prop.m21WorkId:
            # it maps to a backward compatible big-C Contributor role, which can be
            # found in prop.m21WorkId.
            return prop.m21WorkId

        # it's a small-c contributor that doesn't map to a backward compatible
        # big-C Contributor role, but since we're not trying to be backward
        # compatible, we'll take these, too.
        return prop.uniqueName

    def _getItem(self,
                 key: str,
                 namespace: Optional[str] = None,
                 personal: bool = False) -> Optional[Any]:
        '''
        If namespace is provided, the key will be interpreted as name or
        abbrevCode (within that namespace). Either will work. If namespace is
        None, the key will be interpreted as uniqueName or assumed to be of the
        form 'namespace:name'.
        '''
        nsKey: str = self._nsKey(key, namespace, personal)
        output: Any = self._metadata.get(nsKey, None)
        if not output:
            return None
        if isinstance(output, list):
            return output[0]
        return output

    def _getItems(self,
                 key: str,
                 namespace: Optional[str] = None,
                 personal: bool = False) -> List[Any]:
        nsKey: str = self._nsKey(key, namespace, personal)
        output: Any = self._metadata.get(nsKey, None)
        if not output:
            return []
        if not isinstance(output, list):
            return [output]
        return output

    @staticmethod
    def _convertValue(nsKey: str, value: Any) -> Any:
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
        valueType: Type = Metadata._NSKEY2VALUETYPE.get(nsKey, None)
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
                return DateSingle(value)
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

    def _addItem(self,
                 key: str,
                 value: Any,
                 namespace: Optional[str] = None,
                 personal: bool = False):
        '''
        If namespace is provided, the key will be interpreted as name or
        abbrevCode (within that namespace). Either will work. If namespace is
        None, the key will be interpreted as uniqueName or assumed to be of the
        form 'namespace:name'.
        '''
        if isinstance(value, list):
            raise ValueError

        nsKey: str = self._nsKey(key, namespace, personal)
        value = self._convertValue(nsKey, value)

        prevValue: Optional[Any] = self._metadata.get(nsKey, None)
        if prevValue is None:
            # set a single value
            self._metadata[nsKey] = value
        elif isinstance(prevValue, list):
            # add value to the list
            prevValue.append(value)
        else:
            # overwrite prevValue with a list containing prevValue and value
            self._metadata[nsKey] = [prevValue, value]

    def _addItems(self,
                  key: str,
                  valueList: List[Any],
                  namespace: Optional[str] = None,
                  personal: bool = False):
        '''
        Adds a list of items to metadata with key and namespace.

        If namespace is provided, the key will be interpreted as name or
        abbrevCode (within that namespace). Either will work. If namespace is
        None, the key will be interpreted as uniqueName or assumed to be of the
        form 'namespace:name'.

        >>> md = metadata.Metadata()
        >>> md._addItems('title', ['value0']) # add list as first value
        >>> md._addItems('title', ['value1', 'value2']) # add list to single element
        >>> md._addItems('title', ['value3', 'value4']) # add list to list
        >>> titles = md.getItems('title')
        >>> len(titles)
        5
        >>> titles[0]
        <music21.metadata.primitives.Text value0>
        >>> titles[1]
        <music21.metadata.primitives.Text value1>
        >>> titles[2]
        <music21.metadata.primitives.Text value2>
        >>> titles[3]
        <music21.metadata.primitives.Text value3>
        >>> titles[4]
        <music21.metadata.primitives.Text value4>
        '''
        if not isinstance(valueList, list):
            raise ValueError
        if not valueList:
            raise ValueError

        nsKey: str = self._nsKey(key, namespace, personal)

        newValueList: List[Any] = []
        for value in valueList:
            newValue = self._convertValue(nsKey, value)
            newValueList.append(newValue)

        prevValue: Optional[Any] = self._metadata.get(nsKey, None)
        if prevValue is None:
            # set the newValueList
            if len(newValueList) == 1:
                self._metadata[nsKey] = newValueList[0]
            else:
                self._metadata[nsKey] = newValueList
        elif isinstance(prevValue, list):
            # add value to the list
            prevValue += newValueList
        else:
            # overwrite prevValue with a list containing prevValue followed by newValueList
            self._metadata[nsKey] = [prevValue] + newValueList

    def _setItem(self,
                 key: str,
                 value: Any,
                 namespace: Optional[str] = None,
                 personal: bool = False):
        '''
        If namespace is provided, the key will be interpreted as name or
        abbrevCode (within that namespace). Either will work. If namespace is
        None, the key will be interpreted as uniqueName or assumed to be of the
        form 'namespace:name'.
        '''
        nsKey: str = self._nsKey(key, namespace, personal)
        self._metadata.pop(nsKey, None)
        self._addItem(nsKey, value)

    def _setItems(self,
                  key: str,
                  valueList: List[Any],
                  namespace: Optional[str] = None,
                  personal: bool = False):
        '''
        If namespace is provided, the key will be interpreted as name or
        abbrevCode (within that namespace). Either will work. If namespace is
        None, the key will be interpreted as uniqueName or assumed to be of the
        form 'namespace:name'.
        '''
        nsKey: str = self._nsKey(key, namespace, personal)
        self._metadata.pop(nsKey, None)
        self._addItems(nsKey, valueList)

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
        prop: PropertyDescription = Metadata._NSKEY2STDPROPERTYDESC.get(nsKey, None)
        if prop is None:
            return False

        return prop.isContributor and (
            prop.namespace == 'music21'
            or prop.m21WorkId is not None
            or prop.uniqueName == 'otherContributor')

#     @staticmethod
#     def _isBackwardCompatibleNSKey(nsKey: str) -> bool:
#         prop: PropertyDescription = Metadata._NSKEY2STDPROPERTYDESC.get(nsKey, None)
#         if prop is None:
#             return False
#
#         return prop.namespace == 'music21' or prop.m21WorkId is not None

#     @staticmethod
#     def _nsKeyToBackwardCompatibleContributorRole(nsKey: str) -> Optional[str]:
#         prop: PropertyDescription = Metadata._NSKEY2STDPROPERTYDESC.get(nsKey, None)
#         if prop is None:
#             return None
#         if not prop.isContributor:
#             return None
#
#         # it's a small-c contributor
#         if prop.namespace == 'music21':
#             # it's in the music21 namespace, so it's a big-C Contributor,
#             # and Contributor.role can be found in prop.name
#             return prop.name
#
#         # it's a small-c contributor that's not in the music21 namespace
#         if prop.m21WorkId:
#             # it maps to a backward compatible big-C Contributor role, which can be
#             # found in prop.m21WorkId.
#             return prop.m21WorkId
#
#         return None

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
        nsKey: Optional[str] = Metadata._M21WORKID2NSKEY.get(role, None)
        if nsKey is None:
            # it's a non-standard role, so add this contributor with uniqueName='otherContributor'
            # return Metadata.uniqueNameToNSKey('otherContributor')
            return 'marcrel:CTB'

        prop: Optional[PropertyDescription] = Metadata._NSKEY2STDPROPERTYDESC.get(nsKey, None)
        if prop is None or not prop.isContributor:
            # return Metadata.uniqueNameToNSKey('otherContributor')
            return 'marcrel:CTB'

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
        >>> all = md.getAllItems()
        >>> len(all)
        4
        >>> all[0]
        ('marcrel:LYR', <music21.metadata.primitives.Contributor lyricist:Joe0>)
        >>> all[1]
        ('marcrel:LYR', <music21.metadata.primitives.Contributor lyricist:Joe1>)
        >>> all[2]
        ('marcrel:CTB', <music21.metadata.primitives.Contributor best friend:John0>)
        >>> all[3]
        ('marcrel:CTB', <music21.metadata.primitives.Contributor best friend:John1>)
        '''
        nsKey: str = self._backwardCompatibleContributorRoleToNSKey(c.role)
        self._addItem(nsKey, c)

    def _getAllBackwardCompatibleContributors(self) -> List[Contributor]:
        allOut: List[Contributor] = []

        for nsKey, value in self._metadata.items():
            if not self._isBackwardCompatibleContributorNSKey(nsKey):
                continue

            if isinstance(value, list):
                allOut += value
            else:
                allOut.append(value)

        return allOut

    def _getBackwardCompatibleItemNoConversion(self, workId: str) -> Optional[Any]:
        result: List[Any] = self._getBackwardCompatibleItemsNoConversion(workId)
        if not result:  # None or empty list
            return None
        return result[0]

    def _getBackwardCompatibleItem(self, workId: str) -> Optional[str]:
        item = self._getBackwardCompatibleItemNoConversion(workId)
        if item is None:
            return None
        if isinstance(item, Contributor):
            return item.names[0]
        return str(item)

#     def _addBackwardCompatibleItem(self, workId: str, value: Any):
#         nsKey: str = Metadata._M21WORKID2NSKEY.get(workId, None)
#         if nsKey is not None:
#             self._addItem(nsKey, value)
#
    def _setBackwardCompatibleItem(self, workId: str, value: Any):
        nsKey: str = Metadata._M21WORKID2NSKEY.get(workId, None)
        if nsKey is not None:
            self._setItem(nsKey, value)

    def _getBackwardCompatibleItemsNoConversion(self, workId: str) -> List[Any]:
        nsKey: str = Metadata._M21WORKID2NSKEY.get(workId, None)
        if nsKey is None:
            return None

        resultList: List[Any] = self._getItems(nsKey)
        if not resultList:
            return []

        return resultList

    def _getBackwardCompatibleContributorNames(self, workId: str) -> List[str]:
        output: List[str] = []
        values: List[Any] = self._getBackwardCompatibleItemsNoConversion(workId)

        # return only one name of each contributor (backward compatible behavior)
        for v in values:
            output.append(v.names[0])
        return output

    def _setBackwardCompatibleContributorNames(self, workId: str, names: List[str]):
        # Auto-conversion from str to standard Contributor happens behind the scenes
        self._setItems(workId, names)


# -----------------------------------------------------------------------------
#   Descriptions of the standard supported properties

    _STDPROPERTYDESCS: Tuple[PropertyDescription, ...] = (
        # The following 'dcterms' properties are the standard Dublin Core property terms
        # found at http://purl.org/dc/terms/

        # abstract: A summary of the resource.
        PropertyDescription(
            abbrevCode='AB',
            name='abstract',
            label='Abstract',
            namespace='dcterms',
            isContributor=False),

        # accessRights: Information about who access the resource or an indication of
        #   its security status.
        PropertyDescription(
            abbrevCode='AR',
            name='accessRights',
            label='Access Rights',
            namespace='dcterms',
            isContributor=False),

        # accrualMethod: The method by which items are added to a collection.
        PropertyDescription(
            abbrevCode='AM',
            name='accrualMethod',
            label='Accrual Method',
            namespace='dcterms',
            isContributor=False),

        # accrualPeriodicity: The frequency with which items are added to a collection.
        PropertyDescription(
            abbrevCode='AP',
            name='accrualPeriodicity',
            label='Accrual Periodicity',
            namespace='dcterms',
            isContributor=False),

        # accrualPolicy: The policy governing the addition of items to a collection.
        PropertyDescription(
            abbrevCode='APL',
            name='accrualPolicy',
            label='Accrual Policy',
            namespace='dcterms',
            isContributor=False),

        # alternative: An alternative name for the resource.
        PropertyDescription(
            abbrevCode='ALT',
            name='alternative',
            label='Alternative Title',
            namespace='dcterms',
            m21Abbrev='ota',
            m21WorkId='alternativeTitle',
            isContributor=False),

        # audience: A class of agents for whom the resource is intended or useful.
        PropertyDescription(
            abbrevCode='AUD',
            name='audience',
            label='Audience',
            namespace='dcterms',
            isContributor=False),

        # available: Date that the resource became or will become available.
        PropertyDescription(
            abbrevCode='AVL',
            name='available',
            label='Date Available',
            namespace='dcterms',
            uniqueName='dateAvailable',
            valueType=DateSingle,   # including DateRelative, DateBetween, DateSelection
            isContributor=False),

        # bibliographicCitation: A bibliographic reference for the resource.
        PropertyDescription(
            abbrevCode='BIB',
            name='bibliographicCitation',
            label='Bibliographic Citation',
            namespace='dcterms',
            isContributor=False),

        # conformsTo: An established standard to which the described resource conforms.
        PropertyDescription(
            abbrevCode='COT',
            name='conformsTo',
            label='Conforms To',
            namespace='dcterms',
            isContributor=False),

        # contributor: An entity responsible for making contributions to the resource.
        # NOTE: You should use one of the 'marcrel' properties below instead, since
        # this property is very vague. The 'marcrel' properties are considered to be
        # refinements of dcterms:contributor (this property), so if someone asks for
        # everything as Dublin Core metadata, those will all be translated into
        # dcterms:contributor properties.
        PropertyDescription(
            abbrevCode='CN',
            name='contributor',
            label='Contributor',
            namespace='dcterms',
            uniqueName='genericContributor',
            valueType=Contributor,
            isContributor=True),

        # coverage: The spatial or temporal topic of the resource, spatial applicability
        #   of the resource, or jurisdiction under which the resource is relevant.
        PropertyDescription(
            abbrevCode='CVR',
            name='coverage',
            label='Coverage',
            namespace='dcterms',
            isContributor=False),

        # created: Date of creation of the resource.
        PropertyDescription(
            abbrevCode='CRD',
            name='created',
            label='Date Created',
            namespace='dcterms',
            m21WorkId='date',  # no abbrev
            uniqueName='dateCreated',
            valueType=DateSingle,   # including DateRelative, DateBetween, DateSelection
            isContributor=False),

        # creator: An entity responsible for making the resource.
        PropertyDescription(
            abbrevCode='CR',
            name='creator',
            label='Creator',
            namespace='dcterms',
            valueType=Contributor,
            isContributor=True),

        # date: A point or period of time associated with an event in the lifecycle
        #   of the resource.
        PropertyDescription(
            abbrevCode='DT',
            name='date',
            label='Date',
            namespace='dcterms',
            valueType=DateSingle,   # including DateRelative, DateBetween, DateSelection
            isContributor=False),

        # dateAccepted: Date of acceptance of the resource.
        PropertyDescription(
            abbrevCode='DTA',
            name='dateAccepted',
            label='Date Accepted',
            namespace='dcterms',
            valueType=DateSingle,   # including DateRelative, DateBetween, DateSelection
            isContributor=False),

        # dateCopyrighted: Date of copyright of the resource.
        PropertyDescription(
            abbrevCode='DTC',
            name='dateCopyrighted',
            label='Date Copyrighted',
            namespace='dcterms',
            valueType=DateSingle,   # including DateRelative, DateBetween, DateSelection
            isContributor=False),

        # dateSubmitted: Date of submission of the resource.
        PropertyDescription(
            abbrevCode='DTS',
            name='dateSubmitted',
            label='Date Submitted',
            namespace='dcterms',
            valueType=DateSingle,   # including DateRelative, DateBetween, DateSelection
            isContributor=False),

        # description: An account of the resource.
        PropertyDescription(
            abbrevCode='DSC',
            name='description',
            label='Description',
            namespace='dcterms',
            isContributor=False),

        # educationLevel: A class of agents, defined in terms of progression
        #   through an educational or training context, for which the described
        #   resource is intended.
        PropertyDescription(
            abbrevCode='EL',
            name='educationLevel',
            label='Audience Education Level',
            namespace='dcterms',
            isContributor=False),

        # extent: The size or duration of the resource.
        PropertyDescription(
            abbrevCode='EXT',
            name='extent',
            label='Extent',
            namespace='dcterms',
            isContributor=False),

        # format: The file format, physical medium, or dimensions of the resource.
        PropertyDescription(
            abbrevCode='FMT',
            name='format',
            label='Format',
            namespace='dcterms',
            isContributor=False),

        # hasFormat: A related resource that is substantially the same as the
        #   pre-existing described resource, but in another format.
        PropertyDescription(
            abbrevCode='HFMT',
            name='hasFormat',
            label='Has Format',
            namespace='dcterms',
            isContributor=False),

        # hasPart: A related resource that is included either physically or
        #   logically in the described resource.
        PropertyDescription(
            abbrevCode='HPT',
            name='hasPart',
            label='Has Part',
            namespace='dcterms',
            isContributor=False),

        # hasVersion: A related resource that is a version, edition, or adaptation
        #   of the described resource.
        PropertyDescription(
            abbrevCode='HVS',
            name='hasVersion',
            label='Has Version',
            namespace='dcterms',
            isContributor=False),

        # identifier: An unambiguous reference to the resource within a given context.
        PropertyDescription(
            abbrevCode='ID',
            name='identifier',
            label='Identifier',
            namespace='dcterms',
            isContributor=False),

        # instructionalMethod: A process, used to engender knowledge, attitudes and
        #   skills, that the described resource is designed to support.
        PropertyDescription(
            abbrevCode='IM',
            name='instructionalMethod',
            label='Instructional Method',
            namespace='dcterms',
            isContributor=False),

        # isFormatOf: A pre-existing related resource that is substantially the same
        #   as the described resource, but in another format.
        PropertyDescription(
            abbrevCode='IFMT',
            name='isFormatOf',
            label='Is Format Of',
            namespace='dcterms',
            isContributor=False),

        # isPartOf: A related resource in which the described resource is physically
        #   or logically included.
        PropertyDescription(
            abbrevCode='IPT',
            name='isPartOf',
            label='Is Part Of',
            namespace='dcterms',
            isContributor=False),

        # isReferencedBy: A related resource that references, cites, or otherwise
        #   points to the described resource.
        PropertyDescription(
            abbrevCode='IREF',
            name='isReferencedBy',
            label='Is Referenced By',
            namespace='dcterms',
            isContributor=False),

        # isReplacedBy: A related resource that supplants, displaces, or supersedes
        #   the described resource.
        PropertyDescription(
            abbrevCode='IREP',
            name='isReplacedBy',
            label='Is Replaced By',
            namespace='dcterms',
            isContributor=False),

        # isRequiredBy: A related resource that requires the described resource
        #   to support its function, delivery, or coherence.
        PropertyDescription(
            abbrevCode='IREQ',
            name='isRequiredBy',
            label='Is Required By',
            namespace='dcterms',
            isContributor=False),

        # issued: Date of formal issuance of the resource.
        PropertyDescription(
            abbrevCode='IS',
            name='issued',
            label='Date Issued',
            namespace='dcterms',
            uniqueName='dateIssued',
            valueType=DateSingle,   # including DateRelative, DateBetween, DateSelection
            isContributor=False),

        # isVersionOf: A related resource of which the described resource is a
        #   version, edition, or adaptation.
        PropertyDescription(
            abbrevCode='IVSN',
            name='isVersionOf',
            label='Is Version Of',
            namespace='dcterms',
            isContributor=False),

        # language: A language of the resource.
        PropertyDescription(
            abbrevCode='LG',
            name='language',
            label='Language',
            namespace='dcterms',
            isContributor=False),

        # license: A legal document giving official permission to do something
        #   with the resource.
        PropertyDescription(
            abbrevCode='LI',
            name='license',
            label='License',
            namespace='dcterms',
            isContributor=False),

        # mediator: An entity that mediates access to the resource.
        PropertyDescription(
            abbrevCode='ME',
            name='mediator',
            label='Mediator',
            namespace='dcterms',
            isContributor=False),

        # medium: The material or physical carrier of the resource.
        PropertyDescription(
            abbrevCode='MED',
            name='medium',
            label='Medium',
            namespace='dcterms',
            isContributor=False),

        # modified: Date on which the resource was changed.
        PropertyDescription(
            abbrevCode='MOD',
            name='modified',
            label='Date Modified',
            namespace='dcterms',
            uniqueName='dateModified',
            valueType=DateSingle,   # including DateRelative, DateBetween, DateSelection
            isContributor=False),

        # provenance: A statement of any changes in ownership and custody of
        #   the resource since its creation that are significant for its
        #   authenticity, integrity, and interpretation.
        PropertyDescription(
            abbrevCode='PRV',
            name='provenance',
            label='Provenance',
            namespace='dcterms',
            isContributor=False),

        # publisher: An entity responsible for making the resource available.
        PropertyDescription(
            abbrevCode='PBL',
            name='publisher',
            label='Publisher',
            namespace='dcterms',
            valueType=Contributor,
            isContributor=True),

        # references: A related resource that is referenced, cited, or
        #   otherwise pointed to by the described resource.
        PropertyDescription(
            abbrevCode='REF',
            name='references',
            label='References',
            namespace='dcterms',
            isContributor=False),

        # relation: A related resource.
        PropertyDescription(
            abbrevCode='REL',
            name='relation',
            label='Relation',
            namespace='dcterms',
            isContributor=False),

        # replaces: A related resource that is supplanted, displaced, or
        #   superseded by the described resource.
        PropertyDescription(
            abbrevCode='REP',
            name='replaces',
            label='Replaces',
            namespace='dcterms',
            isContributor=False),

        # requires: A related resource that is required by the described
        #   resource to support its function, delivery, or coherence.
        PropertyDescription(
            abbrevCode='REQ',
            name='requires',
            label='Requires',
            namespace='dcterms',
            isContributor=False),

        # rights: Information about rights held in and over the resource.
        PropertyDescription(
            abbrevCode='RT',
            name='rights',
            label='Rights',
            namespace='dcterms',
            m21WorkId='copyright',
            valueType=Copyright,
            isContributor=False),

        # rightsHolder: A person or organization owning or managing rights
        #   over the resource.
        PropertyDescription(
            abbrevCode='RH',
            name='rightsHolder',
            label='Rights Holder',
            namespace='dcterms',
            valueType=Contributor,
            isContributor=True),

        # source: A related resource from which the described resource
        #   is derived.
        PropertyDescription(
            abbrevCode='SRC',
            name='source',
            label='Source',
            namespace='dcterms',
            isContributor=False),

        # spatial: Spatial characteristics of the resource.
        PropertyDescription(
            abbrevCode='SP',
            name='spatial',
            label='Spatial Coverage',
            namespace='dcterms',
            uniqueName='spatialCoverage',
            isContributor=False),

        # subject: A topic of the resource.
        PropertyDescription(
            abbrevCode='SUB',
            name='subject',
            label='Subject',
            namespace='dcterms',
            isContributor=False),

        # tableOfContents: A list of subunits of the resource.
        PropertyDescription(
            abbrevCode='TOC',
            name='tableOfContents',
            label='Table Of Contents',
            namespace='dcterms',
            isContributor=False),

        # temporal: Temporal characteristics of the resource.
        PropertyDescription(
            abbrevCode='TE',
            name='temporal',
            label='Temporal Coverage',
            namespace='dcterms',
            uniqueName='temporalCoverage',
            isContributor=False),

        # title: A name given to the resource.
        PropertyDescription(
            abbrevCode='T',
            name='title',
            label='Title',
            namespace='dcterms',
            m21Abbrev='otl',
            m21WorkId='title',
            isContributor=False),

        # type : The nature or genre of the resource.
        PropertyDescription(
            abbrevCode='TYP',
            name='type',
            label='Type',
            namespace='dcterms',
            isContributor=False),

        # valid: Date (often a range) of validity of a resource.
        PropertyDescription(
            abbrevCode='VA',
            name='valid',
            label='Date Valid',
            namespace='dcterms',
            uniqueName='dateValid',
            valueType=DateSingle,   # including DateRelative, DateBetween, DateSelection
            isContributor=False),

        # The following 'marcrel' property terms are the MARC Relator terms
        # that are refinements of dcterms:contributor, and can be used anywhere
        # dcterms:contributor can be used if you want to be more specific (and
        # you will want to). The MARC Relator terms are defined at:
        # http://www.loc.gov/loc.terms/relators/
        # and this particular sublist can be found at:
        # https://memory.loc.gov/diglib/loc.terms/relators/dc-contributor.html

        # ACT/Actor: a person or organization who principally exhibits acting
        #   skills in a musical or dramatic presentation or entertainment.
        PropertyDescription(
            abbrevCode='act',
            name='ACT',
            label='Actor',
            namespace='marcrel',
            uniqueName='actor',
            valueType=Contributor,
            isContributor=True),

        # ADP/Adapter: a person or organization who 1) reworks a musical composition,
        #   usually for a different medium, or 2) rewrites novels or stories
        #   for motion pictures or other audiovisual medium.
        PropertyDescription(
            abbrevCode='adp',
            name='ADP',
            label='Adapter',
            namespace='marcrel',
            uniqueName='adapter',
            valueType=Contributor,
            isContributor=True),

        # ANM/Animator: a person or organization who draws the two-dimensional
        #   figures, manipulates the three dimensional objects and/or also
        #   programs the computer to move objects and images for the purpose
        #   of animated film processing.
        PropertyDescription(
            abbrevCode='anm',
            name='ANM',
            label='Animator',
            namespace='marcrel',
            uniqueName='animator',
            valueType=Contributor,
            isContributor=True),

        # ANN/Annotator: a person who writes manuscript annotations on a printed item.
        PropertyDescription(
            abbrevCode='ann',
            name='ANN',
            label='Annotator',
            namespace='marcrel',
            uniqueName='annotator',
            valueType=Contributor,
            isContributor=True),

        # ARC/Architect: a person or organization who designs structures or oversees
        #   their construction.
        PropertyDescription(
            abbrevCode='arc',
            name='ARC',
            label='Architect',
            namespace='marcrel',
            uniqueName='architect',
            valueType=Contributor,
            isContributor=True),

        # ARR/Arranger: a person or organization who transcribes a musical
        #   composition, usually for a different medium from that of the original;
        #   in an arrangement the musical substance remains essentially unchanged.
        PropertyDescription(
            abbrevCode='arr',
            name='ARR',
            label='Arranger',
            namespace='marcrel',
            m21WorkId='arranger',
            valueType=Contributor,
            isContributor=True),

        # ART/Artist: a person (e.g., a painter) or organization who conceives, and
        #   perhaps also implements, an original graphic design or work of art, if
        #   specific codes (e.g., [egr], [etr]) are not desired. For book illustrators,
        #   prefer Illustrator [ill].
        PropertyDescription(
            abbrevCode='art',
            name='ART',
            label='Artist',
            namespace='marcrel',
            uniqueName='artist',
            valueType=Contributor,
            isContributor=True),

        # AUT/Author: a person or organization chiefly responsible for the
        #   intellectual or artistic content of a work, usually printed text.
        PropertyDescription(
            abbrevCode='aut',
            name='AUT',
            label='Author',
            namespace='marcrel',
            uniqueName='author',
            valueType=Contributor,
            isContributor=True),

        # AQT/Author in quotations or text extracts: a person or organization
        #   whose work is largely quoted or extracted in works to which he or
        #   she did not contribute directly.
        PropertyDescription(
            abbrevCode='aqt',
            name='AQT',
            label='Author in quotations or text extracts',
            namespace='marcrel',
            uniqueName='quotationsAuthor',
            valueType=Contributor,
            isContributor=True),

        # AFT/Author of afterword, colophon, etc.: a person or organization
        #   responsible for an afterword, postface, colophon, etc. but who
        #   is not the chief author of a work.
        PropertyDescription(
            abbrevCode='aft',
            name='AFT',
            label='Author of afterword, colophon, etc.',
            namespace='marcrel',
            uniqueName='afterwordAuthor',
            valueType=Contributor,
            isContributor=True),

        # AUD/Author of dialog: a person or organization responsible for
        #   the dialog or spoken commentary for a screenplay or sound
        #   recording.
        PropertyDescription(
            abbrevCode='aud',
            name='AUD',
            label='Author of dialog',
            namespace='marcrel',
            uniqueName='dialogAuthor',
            valueType=Contributor,
            isContributor=True),

        # AUI/Author of introduction, etc.:  a person or organization
        #   responsible for an introduction, preface, foreword, or other
        #   critical introductory matter, but who is not the chief author.
        PropertyDescription(
            abbrevCode='aui',
            name='AUI',
            label='Author of introduction, etc.',
            namespace='marcrel',
            uniqueName='introductionAuthor',
            valueType=Contributor,
            isContributor=True),

        # AUS/Author of screenplay, etc.:  a person or organization responsible
        #   for a motion picture screenplay, dialog, spoken commentary, etc.
        PropertyDescription(
            abbrevCode='aus',
            name='AUS',
            label='Author of screenplay, etc.',
            namespace='marcrel',
            uniqueName='screenplayAuthor',
            valueType=Contributor,
            isContributor=True),

        # CLL/Calligrapher: a person or organization who writes in an artistic
        #   hand, usually as a copyist and or engrosser.
        PropertyDescription(
            abbrevCode='cll',
            name='CLL',
            label='Calligrapher',
            namespace='marcrel',
            uniqueName='calligrapher',
            valueType=Contributor,
            isContributor=True),

        # CTG/Cartographer: a person or organization responsible for the
        #   creation of maps and other cartographic materials.
        PropertyDescription(
            abbrevCode='ctg',
            name='CTG',
            label='Cartographer',
            namespace='marcrel',
            uniqueName='cartographer',
            valueType=Contributor,
            isContributor=True),

        # CHR/Choreographer: a person or organization who composes or arranges
        #   dances or other movements (e.g., "master of swords") for a musical
        #   or dramatic presentation or entertainment.
        PropertyDescription(
            abbrevCode='chr',
            name='CHR',
            label='Choreographer',
            namespace='marcrel',
            uniqueName='choreographer',
            valueType=Contributor,
            isContributor=True),

        # CNG/Cinematographer: a person or organization who is in charge of
        #   the images captured for a motion picture film. The cinematographer
        #   works under the supervision of a director, and may also be referred
        #   to as director of photography. Do not confuse with videographer.
        PropertyDescription(
            abbrevCode='cng',
            name='CNG',
            label='Cinematographer',
            namespace='marcrel',
            uniqueName='cinematographer',
            valueType=Contributor,
            isContributor=True),

        # CLB/Collaborator: a person or organization that takes a limited part
        #   in the elaboration of a work of another person or organization that
        #   brings complements (e.g., appendices, notes) to the work.
        PropertyDescription(
            abbrevCode='clb',
            name='CLB',
            label='Collaborator',
            namespace='marcrel',
            uniqueName='collaborator',
            valueType=Contributor,
            isContributor=True),

        # CLT/Collotyper: a person or organization responsible for the production
        #   of photographic prints from film or other colloid that has ink-receptive
        #   and ink-repellent surfaces.
        PropertyDescription(
            abbrevCode='clt',
            name='CLT',
            label='Collotyper',
            namespace='marcrel',
            uniqueName='collotyper',
            valueType=Contributor,
            isContributor=True),

        # CMM/Commentator: a person or organization who provides interpretation,
        #   analysis, or a discussion of the subject matter on a recording,
        #   motion picture, or other audiovisual medium.
        PropertyDescription(
            abbrevCode='cmm',
            name='CMM',
            label='Commentator',
            namespace='marcrel',
            uniqueName='commentator',
            valueType=Contributor,
            isContributor=True),

        # CWT/Commentator for written text: a person or organization responsible
        #   for the commentary or explanatory notes about a text. For the writer
        #   of manuscript annotations in a printed book, use Annotator [ann].
        PropertyDescription(
            abbrevCode='cwt',
            name='CWT',
            label='Commentator for written text',
            namespace='marcrel',
            uniqueName='writtenCommentator',
            valueType=Contributor,
            isContributor=True),

        # COM/Compiler: a person or organization who produces a work or
        #   publication by selecting and putting together material from the
        #   works of various persons or bodies.
        PropertyDescription(
            abbrevCode='com',
            name='COM',
            label='Compiler',
            namespace='marcrel',
            uniqueName='compiler',
            valueType=Contributor,
            isContributor=True),

        # CMP/Composer: a person or organization who creates a musical work,
        #   usually a piece of music in manuscript or printed form.
        PropertyDescription(
            abbrevCode='cmp',
            name='CMP',
            label='Composer',
            namespace='marcrel',
            m21WorkId='composer',
            valueType=Contributor,
            isContributor=True),

        # CCP/Conceptor: a person or organization responsible for the original
        #   idea on which a work is based, this includes the scientific author
        #   of an audio-visual item and the conceptor of an advertisement.
        PropertyDescription(
            abbrevCode='ccp',
            name='CCP',
            label='Conceptor',
            namespace='marcrel',
            uniqueName='conceptor',
            valueType=Contributor,
            isContributor=True),

        # CND/Conductor: a person who directs a performing group (orchestra,
        #   chorus, opera, etc.) in a musical or dramatic presentation or
        #   entertainment.
        PropertyDescription(
            abbrevCode='cnd',
            name='CND',
            label='Conductor',
            namespace='marcrel',
            uniqueName='conductor',
            valueType=Contributor,
            isContributor=True),

        # CSL/Consultant: a person or organization relevant to a resource, who
        #   is called upon for professional advice or services in a specialized
        #   field of knowledge or training.
        PropertyDescription(
            abbrevCode='csl',
            name='CSL',
            label='Consultant',
            namespace='marcrel',
            uniqueName='consultant',
            valueType=Contributor,
            isContributor=True),

        # CSP/Consultant to a project: a person or organization relevant to a
        #   resource, who is engaged specifically to provide an intellectual
        #   overview of a strategic or operational task and by analysis,
        #   specification, or instruction, to create or propose a cost-effective
        #   course of action or solution.
        PropertyDescription(
            abbrevCode='csp',
            name='CSP',
            label='Consultant to a project',
            namespace='marcrel',
            uniqueName='projectConsultant',
            valueType=Contributor,
            isContributor=True),

        # CTR/Contractor: a person or organization relevant to a resource, who
        #   enters into a contract with another person or organization to
        #   perform a specific task.
        PropertyDescription(
            abbrevCode='ctr',
            name='CTR',
            label='Contractor',
            namespace='marcrel',
            uniqueName='contractor',
            valueType=Contributor,
            isContributor=True),

        # CTB/Contributor: a person or organization one whose work has been
        #   contributed to a larger work, such as an anthology, serial
        #   publication, or other compilation of individual works. Do not
        #   use if the sole function in relation to a work is as author,
        #   editor, compiler or translator.
        # Note: this is in fact a refinement of dcterms:contributor, since
        # it is more specific than that one.
        PropertyDescription(
            abbrevCode='ctb',
            name='CTB',
            label='Contributor',
            namespace='marcrel',
            uniqueName='otherContributor',  # more specific than 'genericContributor'
            valueType=Contributor,
            isContributor=True),

        # CRP/Correspondent: a person or organization who was either
        #   the writer or recipient of a letter or other communication.
        PropertyDescription(
            abbrevCode='crp',
            name='CRP',
            label='Correspondent',
            namespace='marcrel',
            uniqueName='correspondent',
            valueType=Contributor,
            isContributor=True),

        # CST/Costume designer: a person or organization who designs
        #   or makes costumes, fixes hair, etc., for a musical or
        #   dramatic presentation or entertainment.
        PropertyDescription(
            abbrevCode='cst',
            name='CST',
            label='Costume designer',
            namespace='marcrel',
            uniqueName='costumeDesigner',
            valueType=Contributor,
            isContributor=True),

        # We already have 'dcterms:creator', so we won't use the marcrel equivalent
        # CRE/Creator: a person or organization responsible for the
        #   intellectual or artistic content of a work.
        #         PropertyDescription(
        #             abbrevCode='cre',
        #             name='CRE',
        #             label='Creator',
        #             namespace='marcrel',
        #             uniqueName='creator',
        #             valueType=Contributor,
        #             isContributor=True),

        # CUR/Curator of an exhibition: a person or organization
        #   responsible for conceiving and organizing an exhibition.
        PropertyDescription(
            abbrevCode='cur',
            name='CUR',
            label='Curator of an exhibition',
            namespace='marcrel',
            uniqueName='curator',
            valueType=Contributor,
            isContributor=True),

        # DNC/Dancer: a person or organization who principally
        #   exhibits dancing skills in a musical or dramatic
        #   presentation or entertainment.
        PropertyDescription(
            abbrevCode='dnc',
            name='DNC',
            label='Dancer',
            namespace='marcrel',
            uniqueName='dancer',
            valueType=Contributor,
            isContributor=True),

        # DLN/Delineator: a person or organization executing technical
        #   drawings from others' designs.
        PropertyDescription(
            abbrevCode='dln',
            name='DLN',
            label='Delineator',
            namespace='marcrel',
            uniqueName='delineator',
            valueType=Contributor,
            isContributor=True),

        # DSR/Designer: a person or organization responsible for the design
        #   if more specific codes (e.g., [bkd], [tyd]) are not desired.
        PropertyDescription(
            abbrevCode='dsr',
            name='DSR',
            label='Designer',
            namespace='marcrel',
            uniqueName='designer',
            valueType=Contributor,
            isContributor=True),

        # DRT/Director: a person or organization who is responsible for the
        #   general management of a work or who supervises the production of
        #   a performance for stage, screen, or sound recording.
        PropertyDescription(
            abbrevCode='drt',
            name='DRT',
            label='Director',
            namespace='marcrel',
            uniqueName='director',
            valueType=Contributor,
            isContributor=True),

        # DIS/Dissertant: a person who presents a thesis for a university or
        #   higher-level educational degree.
        PropertyDescription(
            abbrevCode='dis',
            name='DIS',
            label='Dissertant',
            namespace='marcrel',
            uniqueName='dissertant',
            valueType=Contributor,
            isContributor=True),

        # DRM/Draftsman: a person or organization who prepares artistic or
        #   technical drawings.
        PropertyDescription(
            abbrevCode='drm',
            name='DRM',
            label='Draftsman',
            namespace='marcrel',
            uniqueName='draftsman',
            valueType=Contributor,
            isContributor=True),

        # EDT/Editor: a person or organization who prepares for publication
        #   a work not primarily his/her own, such as by elucidating text,
        #   adding introductory or other critical matter, or technically
        #   directing an editorial staff.
        PropertyDescription(
            abbrevCode='edt',
            name='EDT',
            label='Editor',
            namespace='marcrel',
            uniqueName='editor',
            valueType=Contributor,
            isContributor=True),

        # ENG/Engineer: a person or organization that is responsible for
        #   technical planning and design, particularly with construction.
        PropertyDescription(
            abbrevCode='eng',
            name='ENG',
            label='Engineer',
            namespace='marcrel',
            uniqueName='engineer',
            valueType=Contributor,
            isContributor=True),

        # EGR/Engraver: a person or organization who cuts letters, figures,
        #   etc. on a surface, such as a wooden or metal plate, for printing.
        PropertyDescription(
            abbrevCode='egr',
            name='EGR',
            label='Engraver',
            namespace='marcrel',
            uniqueName='engraver',
            valueType=Contributor,
            isContributor=True),

        # ETR/Etcher: a person or organization who produces text or images
        #   for printing by subjecting metal, glass, or some other surface
        #   to acid or the corrosive action of some other substance.
        PropertyDescription(
            abbrevCode='etr',
            name='ETR',
            label='Etcher',
            namespace='marcrel',
            uniqueName='etcher',
            valueType=Contributor,
            isContributor=True),

        # FAC/Facsimilist: a person or organization that executed the facsimile.
        PropertyDescription(
            abbrevCode='fac',
            name='FAC',
            label='Facsimilist',
            namespace='marcrel',
            uniqueName='facsimilist',
            valueType=Contributor,
            isContributor=True),

        # FLM/Film editor: a person or organization who is an editor of a
        #   motion picture film. This term is used regardless of the medium
        #   upon which the motion picture is produced or manufactured (e.g.,
        #   acetate film, video tape).
        PropertyDescription(
            abbrevCode='flm',
            name='FLM',
            label='Film editor',
            namespace='marcrel',
            uniqueName='filmEditor',
            valueType=Contributor,
            isContributor=True),

        # FRG/Forger: a person or organization who makes or imitates something
        #   of value or importance, especially with the intent to defraud.
        PropertyDescription(
            abbrevCode='frg',
            name='FRG',
            label='Forger',
            namespace='marcrel',
            uniqueName='forger',
            valueType=Contributor,
            isContributor=True),

        # HST/Host: a person who is invited or regularly leads a program
        #   (often broadcast) that includes other guests, performers, etc.
        #   (e.g., talk show host).
        PropertyDescription(
            abbrevCode='hst',
            name='HST',
            label='Host',
            namespace='marcrel',
            uniqueName='host',
            valueType=Contributor,
            isContributor=True),

        # ILU/Illuminator: a person or organization responsible for the
        #   decoration of a work (especially manuscript material) with
        #   precious metals or color, usually with elaborate designs and
        #   motifs.
        PropertyDescription(
            abbrevCode='ilu',
            name='ILU',
            label='Illuminator',
            namespace='marcrel',
            uniqueName='illuminator',
            valueType=Contributor,
            isContributor=True),

        # ILL/Illustrator: a person or organization who conceives, and
        #   perhaps also implements, a design or illustration, usually
        #   to accompany a written text.
        PropertyDescription(
            abbrevCode='ill',
            name='ILL',
            label='Illustrator',
            namespace='marcrel',
            uniqueName='illustrator',
            valueType=Contributor,
            isContributor=True),

        # ITR/Instrumentalist: a person or organization who principally
        #   plays an instrument in a musical or dramatic presentation
        #   or entertainment.
        PropertyDescription(
            abbrevCode='itr',
            name='ITR',
            label='Instrumentalist',
            namespace='marcrel',
            uniqueName='instrumentalist',
            valueType=Contributor,
            isContributor=True),

        # IVE/Interviewee: a person or organization who is interviewed
        #   at a consultation or meeting, usually by a reporter, pollster,
        #   or some other information gathering agent.
        PropertyDescription(
            abbrevCode='ive',
            name='IVE',
            label='Interviewee',
            namespace='marcrel',
            uniqueName='interviewee',
            valueType=Contributor,
            isContributor=True),

        # IVR/Interviewer: a person or organization who acts as a reporter,
        #   pollster, or other information gathering agent in a consultation
        #   or meeting involving one or more individuals.
        PropertyDescription(
            abbrevCode='ivr',
            name='IVR',
            label='Interviewer',
            namespace='marcrel',
            uniqueName='interviewer',
            valueType=Contributor,
            isContributor=True),

        # INV/Inventor: a person or organization who first produces a
        #   particular useful item, or develops a new process for
        #   obtaining a known item or result.
        PropertyDescription(
            abbrevCode='inv',
            name='INV',
            label='Inventor',
            namespace='marcrel',
            uniqueName='inventor',
            valueType=Contributor,
            isContributor=True),

        # LSA/Landscape architect: a person or organization whose work
        #   involves coordinating the arrangement of existing and
        #   proposed land features and structures.
        PropertyDescription(
            abbrevCode='lsa',
            name='LSA',
            label='Landscape architect',
            namespace='marcrel',
            uniqueName='landscapeArchitect',
            valueType=Contributor,
            isContributor=True),

        # LBT/Librettist: a person or organization who is a writer of
        #   the text of an opera, oratorio, etc.
        PropertyDescription(
            abbrevCode='lbt',
            name='LBT',
            label='Librettist',
            namespace='marcrel',
            m21WorkId='librettist',
            valueType=Contributor,
            isContributor=True),

        # LGD/Lighting designer: a person or organization who designs the
        #   lighting scheme for a theatrical presentation, entertainment,
        #   motion picture, etc.
        PropertyDescription(
            abbrevCode='lgd',
            name='LGD',
            label='Lighting designer',
            namespace='marcrel',
            uniqueName='lightingDesigner',
            valueType=Contributor,
            isContributor=True),

        # LTG/Lithographer: a person or organization who prepares the stone
        #   or plate for lithographic printing, including a graphic artist
        #   creating a design directly on the surface from which printing
        #   will be done.
        PropertyDescription(
            abbrevCode='ltg',
            name='LTG',
            label='Lithographer',
            namespace='marcrel',
            uniqueName='lithographer',
            valueType=Contributor,
            isContributor=True),

        # LYR/Lyricist: a person or organization who is the a writer of the
        #   text of a song.
        PropertyDescription(
            abbrevCode='lyr',
            name='LYR',
            label='Lyricist',
            namespace='marcrel',
            m21WorkId='lyricist',
            valueType=Contributor,
            isContributor=True),

        # MFR/Manufacturer: a person or organization that makes an
        #   artifactual work (an object made or modified by one or
        #   more persons). Examples of artifactual works include vases,
        #   cannons or pieces of furniture.
        PropertyDescription(
            abbrevCode='mfr',
            name='MFR',
            label='Manufacturer',
            namespace='marcrel',
            uniqueName='manufacturer',
            valueType=Contributor,
            isContributor=True),

        # MTE/Metal-engraver: a person or organization responsible for
        #   decorations, illustrations, letters, etc. cut on a metal
        #   surface for printing or decoration.
        PropertyDescription(
            abbrevCode='mte',
            name='MTE',
            label='Metal-engraver',
            namespace='marcrel',
            uniqueName='metalEngraver',
            valueType=Contributor,
            isContributor=True),

        # MOD/Moderator: a person who leads a program (often broadcast)
        #   where topics are discussed, usually with participation of
        #   experts in fields related to the discussion.
        PropertyDescription(
            abbrevCode='mod',
            name='MOD',
            label='Moderator',
            namespace='marcrel',
            uniqueName='moderator',
            valueType=Contributor,
            isContributor=True),

        # MUS/Musician: a person or organization who performs music or
        #   contributes to the musical content of a work when it is not
        #   possible or desirable to identify the function more precisely.
        PropertyDescription(
            abbrevCode='mus',
            name='MUS',
            label='Musician',
            namespace='marcrel',
            uniqueName='musician',
            valueType=Contributor,
            isContributor=True),

        # NRT/Narrator: a person who is a speaker relating the particulars
        #   of an act, occurrence, or course of events.
        PropertyDescription(
            abbrevCode='nrt',
            name='NRT',
            label='Narrator',
            namespace='marcrel',
            uniqueName='narrator',
            valueType=Contributor,
            isContributor=True),

        # ORM/Organizer of meeting: a person or organization responsible
        #   for organizing a meeting for which an item is the report or
        #   proceedings.
        PropertyDescription(
            abbrevCode='orm',
            name='ORM',
            label='Organizer of meeting',
            namespace='marcrel',
            uniqueName='meetingOrganizer',
            valueType=Contributor,
            isContributor=True),

        # ORG/Originator: a person or organization performing the work,
        #   i.e., the name of a person or organization associated with
        #   the intellectual content of the work. This category does not
        #   include the publisher or personal affiliation, or sponsor
        #   except where it is also the corporate author.
        PropertyDescription(
            abbrevCode='org',
            name='ORG',
            label='Originator',
            namespace='marcrel',
            uniqueName='originator',
            valueType=Contributor,
            isContributor=True),

        # PRF/Performer: a person or organization who exhibits musical
        #   or acting skills in a musical or dramatic presentation or
        #   entertainment, if specific codes for those functions ([act],
        #   [dnc], [itr], [voc], etc.) are not used. If specific codes
        #   are used, [prf] is used for a person whose principal skill
        #   is not known or specified.
        PropertyDescription(
            abbrevCode='prf',
            name='PRF',
            label='Performer',
            namespace='marcrel',
            uniqueName='performer',
            valueType=Contributor,
            isContributor=True),

        # PHT/Photographer: a person or organization responsible for
        #   taking photographs, whether they are used in their original
        #   form or as reproductions.
        PropertyDescription(
            abbrevCode='pht',
            name='PHT',
            label='Photographer',
            namespace='marcrel',
            uniqueName='photographer',
            valueType=Contributor,
            isContributor=True),

        # PLT/Platemaker: a person or organization responsible for the
        #   production of plates, usually for the production of printed
        #   images and/or text.
        PropertyDescription(
            abbrevCode='plt',
            name='PLT',
            label='Platemaker',
            namespace='marcrel',
            uniqueName='platemaker',
            valueType=Contributor,
            isContributor=True),

        # PRM/Printmaker: a person or organization who makes a relief,
        #   intaglio, or planographic printing surface.
        PropertyDescription(
            abbrevCode='prm',
            name='PRM',
            label='Printmaker',
            namespace='marcrel',
            uniqueName='printmaker',
            valueType=Contributor,
            isContributor=True),

        # PRO/Producer: a person or organization responsible for the
        #   making of a motion picture, including business aspects,
        #   management of the productions, and the commercial success
        #   of the work.
        PropertyDescription(
            abbrevCode='pro',
            name='PRO',
            label='Producer',
            namespace='marcrel',
            uniqueName='producer',
            valueType=Contributor,
            isContributor=True),

        # PRD/Production personnel: a person or organization associated
        #   with the production (props, lighting, special effects, etc.)
        #   of a musical or dramatic presentation or entertainment.
        PropertyDescription(
            abbrevCode='prd',
            name='PRD',
            label='Production personnel',
            namespace='marcrel',
            uniqueName='productionPersonnel',
            valueType=Contributor,
            isContributor=True),

        # PRG/Programmer: a person or organization responsible for the
        #   creation and/or maintenance of computer program design
        #   documents, source code, and machine-executable digital files
        #   and supporting documentation.
        PropertyDescription(
            abbrevCode='prg',
            name='PRG',
            label='Programmer',
            namespace='marcrel',
            uniqueName='programmer',
            valueType=Contributor,
            isContributor=True),

        # PPT/Puppeteer: a person or organization who manipulates, controls,
        #   or directs puppets or marionettes in a musical or dramatic
        #   presentation or entertainment.
        PropertyDescription(
            abbrevCode='ppt',
            name='PPT',
            label='Puppeteer',
            namespace='marcrel',
            uniqueName='puppeteer',
            valueType=Contributor,
            isContributor=True),

        # RCE/Recording engineer: a person or organization who supervises
        #   the technical aspects of a sound or video recording session.
        PropertyDescription(
            abbrevCode='rce',
            name='RCE',
            label='Recording engineer',
            namespace='marcrel',
            uniqueName='recordingEngineer',
            valueType=Contributor,
            isContributor=True),

        # REN/Renderer: a person or organization who prepares drawings
        #   of architectural designs (i.e., renderings) in accurate,
        #   representational perspective to show what the project will
        #   look like when completed.
        PropertyDescription(
            abbrevCode='ren',
            name='REN',
            label='Renderer',
            namespace='marcrel',
            uniqueName='renderer',
            valueType=Contributor,
            isContributor=True),

        # RPT/Reporter: a person or organization who writes or presents
        #   reports of news or current events on air or in print.
        PropertyDescription(
            abbrevCode='rpt',
            name='RPT',
            label='Reporter',
            namespace='marcrel',
            uniqueName='reporter',
            valueType=Contributor,
            isContributor=True),

        # RTH/Research team head: a person who directed or managed a
        #   research project.
        PropertyDescription(
            abbrevCode='rth',
            name='RTH',
            label='Research team head',
            namespace='marcrel',
            uniqueName='researchTeamHead',
            valueType=Contributor,
            isContributor=True),

        # RTM/Research team member:  a person who participated in a
        #   research project but whose role did not involve direction
        #   or management of it.
        PropertyDescription(
            abbrevCode='rtm',
            name='RTM',
            label='Research team member',
            namespace='marcrel',
            uniqueName='researchTeamMember',
            valueType=Contributor,
            isContributor=True),

        # RES/Researcher: a person or organization responsible for
        #   performing research.
        PropertyDescription(
            abbrevCode='res',
            name='RES',
            label='Researcher',
            namespace='marcrel',
            uniqueName='researcher',
            valueType=Contributor,
            isContributor=True),

        # RPY/Responsible party: a person or organization legally
        #   responsible for the content of the published material.
        PropertyDescription(
            abbrevCode='rpy',
            name='RPY',
            label='Responsible party',
            namespace='marcrel',
            uniqueName='responsibleParty',
            valueType=Contributor,
            isContributor=True),

        # RSG/Restager: a person or organization, other than the
        #   original choreographer or director, responsible for
        #   restaging a choreographic or dramatic work and who
        #   contributes minimal new content.
        PropertyDescription(
            abbrevCode='rsg',
            name='RSG',
            label='Restager',
            namespace='marcrel',
            uniqueName='restager',
            valueType=Contributor,
            isContributor=True),

        # REV/Reviewer:  a person or organization responsible for
        #   the review of a book, motion picture, performance, etc.
        PropertyDescription(
            abbrevCode='rev',
            name='REV',
            label='Reviewer',
            namespace='marcrel',
            uniqueName='reviewer',
            valueType=Contributor,
            isContributor=True),

        # SCE/Scenarist: a person or organization who is the author
        #   of a motion picture screenplay.
        PropertyDescription(
            abbrevCode='sce',
            name='SCE',
            label='Scenarist',
            namespace='marcrel',
            uniqueName='scenarist',
            valueType=Contributor,
            isContributor=True),

        # SAD/Scientific advisor: a person or organization who brings
        #   scientific, pedagogical, or historical competence to the
        #   conception and realization on a work, particularly in the
        #   case of audio-visual items.
        PropertyDescription(
            abbrevCode='sad',
            name='SAD',
            label='Scientific advisor',
            namespace='marcrel',
            uniqueName='scientificAdvisor',
            valueType=Contributor,
            isContributor=True),

        # SCR/Scribe: a person who is an amanuensis and for a writer of
        #   manuscripts proper. For a person who makes pen-facsimiles,
        #   use Facsimilist [fac].
        PropertyDescription(
            abbrevCode='scr',
            name='SCR',
            label='Scribe',
            namespace='marcrel',
            uniqueName='scribe',
            valueType=Contributor,
            isContributor=True),

        # SCL/Sculptor: a person or organization who models or carves
        #   figures that are three-dimensional representations.
        PropertyDescription(
            abbrevCode='scl',
            name='SCL',
            label='Sculptor',
            namespace='marcrel',
            uniqueName='sculptor',
            valueType=Contributor,
            isContributor=True),

        # SEC/Secretary: a person or organization who is a recorder,
        #   redactor, or other person responsible for expressing the
        #   views of a organization.
        PropertyDescription(
            abbrevCode='sec',
            name='SEC',
            label='Secretary',
            namespace='marcrel',
            uniqueName='secretary',
            valueType=Contributor,
            isContributor=True),

        # STD/Set designer:  a person or organization who translates the
        #   rough sketches of the art director into actual architectural
        #   structures for a theatrical presentation, entertainment, motion
        #   picture, etc. Set designers draw the detailed guides and
        #   specifications for building the set.
        PropertyDescription(
            abbrevCode='std',
            name='STD',
            label='Set designer',
            namespace='marcrel',
            uniqueName='setDesigner',
            valueType=Contributor,
            isContributor=True),

        # SNG/Singer: a person or organization who uses his/her/their voice
        #   with or without instrumental accompaniment to produce music.
        #   A performance may or may not include actual words.
        PropertyDescription(
            abbrevCode='sng',
            name='SNG',
            label='Singer',
            namespace='marcrel',
            uniqueName='singer',
            valueType=Contributor,
            isContributor=True),

        # SPK/Speaker: a person who participates in a program (often broadcast)
        #   and makes a formalized contribution or presentation generally
        #   prepared in advance.
        PropertyDescription(
            abbrevCode='spk',
            name='SPK',
            label='Speaker',
            namespace='marcrel',
            uniqueName='speaker',
            valueType=Contributor,
            isContributor=True),

        # STN/Standards body: an organization responsible for the development
        #   or enforcement of a standard.
        PropertyDescription(
            abbrevCode='stn',
            name='STN',
            label='Standards body',
            namespace='marcrel',
            uniqueName='standardsBody',
            valueType=Contributor,
            isContributor=True),

        # STL/Storyteller: a person relaying a story with creative and/or
        #   theatrical interpretation.
        PropertyDescription(
            abbrevCode='stl',
            name='STL',
            label='Storyteller',
            namespace='marcrel',
            uniqueName='storyteller',
            valueType=Contributor,
            isContributor=True),

        # SRV/Surveyor: a person or organization who does measurements of
        #   tracts of land, etc. to determine location, forms, and boundaries.
        PropertyDescription(
            abbrevCode='srv',
            name='SRV',
            label='Surveyor',
            namespace='marcrel',
            uniqueName='surveyor',
            valueType=Contributor,
            isContributor=True),

        # TCH/Teacher: a person who, in the context of a resource, gives
        #   instruction in an intellectual subject or demonstrates while
        #   teaching physical skills.
        PropertyDescription(
            abbrevCode='tch',
            name='TCH',
            label='Teacher',
            namespace='marcrel',
            uniqueName='teacher',
            valueType=Contributor,
            isContributor=True),

        # TRC/Transcriber: a person who prepares a handwritten or typewritten copy
        #   from original material, including from dictated or orally recorded
        #   material. For makers of pen-facsimiles, use Facsimilist [fac].
        PropertyDescription(
            abbrevCode='trc',
            name='TRC',
            label='Transcriber',
            namespace='marcrel',
            uniqueName='transcriber',
            valueType=Contributor,
            isContributor=True),

        # TRL/Translator: a person or organization who renders a text from one
        #   language into another, or from an older form of a language into the
        #   modern form.
        PropertyDescription(
            abbrevCode='trl',
            name='TRL',
            label='Translator',
            namespace='marcrel',
            m21WorkId='translator',
            valueType=Contributor,
            isContributor=True),

        # VDG/Videographer: a person or organization in charge of a video production,
        #   e.g. the video recording of a stage production as opposed to a commercial
        #   motion picture. The videographer may be the camera operator or may
        #   supervise one or more camera operators. Do not confuse with cinematographer.
        PropertyDescription(
            abbrevCode='vdg',
            name='VDG',
            label='Videographer',
            namespace='marcrel',
            uniqueName='videographer',
            valueType=Contributor,
            isContributor=True),

        # VOC/Vocalist: a person or organization who principally exhibits singing
        #   skills in a musical or dramatic presentation or entertainment.
        PropertyDescription(
            abbrevCode='voc',
            name='VOC',
            label='Vocalist',
            namespace='marcrel',
            uniqueName='vocalist',
            valueType=Contributor,
            isContributor=True),

        # WDE/Wood-engraver: a person or organization who makes prints by cutting
        #   the image in relief on the end-grain of a wood block.
        PropertyDescription(
            abbrevCode='wde',
            name='WDE',
            label='Wood-engraver',
            namespace='marcrel',
            uniqueName='woodEngraver',
            valueType=Contributor,
            isContributor=True),

        # WDC/Woodcutter: a person or organization who makes prints by cutting the
        #   image in relief on the plank side of a wood block.
        PropertyDescription(
            abbrevCode='wdc',
            name='WDC',
            label='Woodcutter',
            namespace='marcrel',
            uniqueName='woodCutter',
            valueType=Contributor,
            isContributor=True),

        # WAM/Writer of accompanying material: a person or organization who writes
        #   significant material which accompanies a sound recording or other
        #   audiovisual material.
        PropertyDescription(
            abbrevCode='wam',
            name='WAM',
            label='Writer of accompanying material',
            namespace='marcrel',
            uniqueName='accompanyingMaterialWriter',
            valueType=Contributor,
            isContributor=True),

        # The following marcrel property term refines dcterms:publisher

        # DST/Distributor: a person or organization that has exclusive or shared
        #   marketing rights for an item.
        PropertyDescription(
            abbrevCode='dst',
            name='DST',
            label='Distributor',
            namespace='marcrel',
            uniqueName='distributor',
            valueType=Contributor,
            isContributor=True),

        # The following music21 property terms have historically been supported
        # by music21, so we must add them as standard property terms here:

        # textOriginalLanguage: original language of vocal/choral text
        PropertyDescription(
            abbrevCode='txo',
            name='textOriginalLanguage',
            label='Original Text Language',
            namespace='music21',
            isContributor=False),

        # textLanguage: language of the encoded vocal/choral text
        PropertyDescription(
            abbrevCode='txl',
            name='textLanguage',
            label='Text Language',
            namespace='music21',
            isContributor=False),

        # popularTitle: popular title
        PropertyDescription(
            abbrevCode='otp',
            name='popularTitle',
            label='Popular Title',
            namespace='music21',
            isContributor=False),

        # parentTitle: parent title
        PropertyDescription(
            abbrevCode='opr',
            name='parentTitle',
            label='Parent Title',
            namespace='music21',
            isContributor=False),

        # actNumber: act number (e.g. '2' or 'Act 2')
        PropertyDescription(
            abbrevCode='oac',
            name='actNumber',
            label='Act Number',
            namespace='music21',
            isContributor=False),

        # sceneNumber: scene number (e.g. '3' or 'Scene 3')
        PropertyDescription(
            abbrevCode='osc',
            name='sceneNumber',
            label='Scene Number',
            namespace='music21',
            isContributor=False),

        # movementNumber: movement number (e.g. '4', or 'mov. 4', or...)
        PropertyDescription(
            abbrevCode='omv',
            name='movementNumber',
            label='Movement Number',
            namespace='music21',
            isContributor=False),

        # movementName: movement name (often a tempo description)
        PropertyDescription(
            abbrevCode='omd',
            name='movementName',
            label='Movement Name',
            namespace='music21',
            isContributor=False),

        # opusNumber: opus number (e.g. '23', or 'Opus 23')
        PropertyDescription(
            abbrevCode='ops',
            name='opusNumber',
            label='Opus Number',
            namespace='music21',
            isContributor=False),

        # number: number (e.g. '5', or 'No. 5')
        PropertyDescription(
            abbrevCode='onm',
            name='number',
            label='Number',
            namespace='music21',
            uniqueName='workNumber',
            isContributor=False),

        # volume: volume number (e.g. '6' or 'Vol. 6')
        PropertyDescription(
            abbrevCode='ovm',
            name='volume',
            label='Volume Number',
            uniqueName='volumeNumber',
            namespace='music21',
            isContributor=False),

        # dedication: dedicated to
        PropertyDescription(
            abbrevCode='ode',
            name='dedication',
            label='Dedicated To',
            uniqueName='dedicatedTo',
            namespace='music21',
            isContributor=False),

        # commission: commissioned by
        PropertyDescription(
            abbrevCode='oco',
            name='commission',
            label='Commissioned By',
            uniqueName='commissionedBy',
            namespace='music21',
            isContributor=False),

        # countryOfComposition: country of composition
        PropertyDescription(
            abbrevCode='ocy',
            name='countryOfComposition',
            label='Country of Composition',
            namespace='music21',
            isContributor=False),

        # localeOfComposition: city, town, or village of composition
        PropertyDescription(
            abbrevCode='opc',
            name='localeOfComposition',
            label='Locale of Composition',
            namespace='music21',
            isContributor=False),

        # groupTitle: group title (e.g. 'The Seasons')
        PropertyDescription(
            abbrevCode='gtl',
            name='groupTitle',
            label='Group Title',
            namespace='music21',
            isContributor=False),

        # associatedWork: associated work, such as a play or film
        PropertyDescription(
            abbrevCode='gaw',
            name='associatedWork',
            label='Associated Work',
            namespace='music21',
            isContributor=False),

        # collectionDesignation: This is a free-form text record that can be used to
        #   identify a collection of pieces, such as works appearing in a compendium
        #   or anthology. E.g. Norton Scores, Smithsonian Collection, Burkhart Anthology.
        PropertyDescription(
            abbrevCode='gco',
            name='collectionDesignation',
            label='Collection Designation',
            namespace='music21',
            isContributor=False),

        # attributedComposer: attributed composer
        PropertyDescription(
            abbrevCode='coa',
            name='attributedComposer',
            label='Attributed Composer',
            namespace='music21',
            valueType=Contributor,
            isContributor=True),

        # suspectedComposer: suspected composer
        PropertyDescription(
            abbrevCode='cos',
            name='suspectedComposer',
            label='Suspected Composer',
            namespace='music21',
            valueType=Contributor,
            isContributor=True),

        # composerAlias: composer's abbreviated, alias, or stage name
        PropertyDescription(
            abbrevCode='col',
            name='composerAlias',
            label='Composer Alias',
            namespace='music21',
            valueType=Contributor,
            isContributor=True),

        # composerCorporate: composer's corporate name
        PropertyDescription(
            abbrevCode='coc',
            name='composerCorporate',
            label='Composer Corporate Name',
            namespace='music21',
            valueType=Contributor,
            isContributor=True),

        # orchestrator: orchestrator
        PropertyDescription(
            abbrevCode='lor',
            name='orchestrator',
            label='Orchestrator',
            namespace='music21',
            valueType=Contributor,
            isContributor=True),
    )

    _NSKEY2STDPROPERTYDESC: dict = {f'{x.namespace}:{x.name}': x for x in _STDPROPERTYDESCS}
    _NSKEY2VALUETYPE: dict = {f'{x.namespace}:{x.name}': x.valueType for x in _STDPROPERTYDESCS}
    _NSKEY2CONTRIBUTORUNIQUENAME: dict = {
        f'{x.namespace}:{x.name}':
            x.uniqueName if x.uniqueName
            else x.m21WorkId if x.m21WorkId
            else x.name
            for x in _STDPROPERTYDESCS if x.isContributor}

    _NSKEY2UNIQUENAME: dict = {
        f'{x.namespace}:{x.name}':
            x.uniqueName if x.uniqueName
            else x.m21WorkId if x.m21WorkId
            else x.name
            for x in _STDPROPERTYDESCS}
    _UNIQUENAME2NSKEY: dict = {
        x.uniqueName if x.uniqueName
        else x.m21WorkId if x.m21WorkId
        else x.name:
            f'{x.namespace}:{x.name}'
            for x in _STDPROPERTYDESCS}

    _UNIQUENAME2STDPROPERTYDESC: dict = {
        x.uniqueName if x.uniqueName
        else x.m21WorkId if x.m21WorkId
        else x.name:
            x for x in _STDPROPERTYDESCS}

    _M21ABBREV2NSKEY: dict = {
        x.m21Abbrev if x.m21Abbrev
        else x.abbrevCode if x.namespace == 'music21'
        else None:
            f'{x.namespace}:{x.name}'
            for x in _STDPROPERTYDESCS
            if x.m21Abbrev or x.namespace == 'music21'}

    _M21WORKID2NSKEY: dict = {
        x.m21WorkId if x.m21WorkId
        else x.name if x.namespace == 'music21'
        else None:
            f'{x.namespace}:{x.name}'
            for x in _STDPROPERTYDESCS
            if x.m21WorkId or x.namespace == 'music21'}

    _NAMESPACEABBREV2NSKEY: dict = {
        (x.namespace, x.abbrevCode):
            f'{x.namespace}:{x.name}'
            for x in _STDPROPERTYDESCS}

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
    ('actNumber', 'alternativeTitle', 'ambitus', 'associatedWork', 'collectionDesignation',
     'commission', 'composer', 'copyright', 'countryOfComposition', 'date', 'dedication',
     'fileFormat', 'fileNumber', 'filePath',
     'groupTitle', 'keySignatureFirst', 'keySignatures', 'localeOfComposition', 'movementName',
     'movementNumber', 'noteCount', 'number', 'numberOfParts',
     'opusNumber', 'parentTitle', 'pitchHighest',
     'pitchLowest', 'popularTitle', 'quarterLength', 'sceneNumber', 'sourcePath', 'tempoFirst',
     'tempos', 'textLanguage', 'textOriginalLanguage', 'timeSignatureFirst',
     'timeSignatures', 'title', 'volume')
    '''

    # CLASS VARIABLES #

    # When changing this, be sure to update freezeThaw.py
    searchAttributes = tuple(sorted(Metadata.searchAttributes + (
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
    )))

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
