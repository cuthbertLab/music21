# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         metadata.py
# Purpose:      music21 classes for representing score and work metadata
#
# Authors:      Christopher Ariza
#               Greg Chapman
#               Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2010-22 Michael Scott Asato Cuthbert and the music21
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

A guide to the v8+ Dublin Core implementation:

The class Metadata has been completely rewritten in music21 v8 to support
significant new functionality.

The previous Metadata implementation had a list of supported workIds, and also
a list of standard contributor roles.  More than one of each contributor role
could exist, but only one of each workId.  And while there was some support for
custom contributor roles, there was no support for other custom metadata, only
the specified list of workIds.

In the v8 implementation, contributor roles are treated the same as other
non-contributor metadata.  Music21 includes a list of supported property terms,
which are pulled from Dublin Core (namespace = 'dcterms'), MARC Relator codes
(namespace = 'marcrel'), and Humdrum (namespace = 'humdrum').  Each property
term is assigned a unique name (e.g. 'composer', 'alternativeTitle', etc).

Each metadata property can be specified by 'uniqueName' or by 'namespace:name'.
For example: `md['composer']` and `md['marcrel:CMP']` are equivalent, as are
`md['alternativeTitle']` and `md['dcterms:alternative']`. There can be more than
one of any such item (not just contributors).  And you can also have metadata
items with custom names.

For simple metadata items, like a single title, there is an easy way to get/set
them: use an attribute-style get operation (e.g. `t = md.title`).  This will always
return a single string.  If there is more than one item of that name, a summary
string will be returned.  To see the full list of metadata items in their native
value type, use a dictionary-style get operation (e.g. `titles = md['title']`).
If an item or list of items is set (whether attribute-style or dictionary-style),
any existing items of that name are deleted. To add an item or list of items
without deleting existing items, use the `md.add()` API.  See the examples below:

Set a title (overwrites any existing titles):

>>> md = metadata.Metadata()
>>> md.title = 'A Title'
>>> md.title
'A Title'
>>> md['title']
(<music21.metadata.primitives.Text A Title>,)

Set two titles (overwrites any existing titles):

>>> md['title'] = ['The Title', 'A Second Title']
>>> md['title']
(<music21.metadata.primitives.Text The Title>,
<music21.metadata.primitives.Text A Second Title>)
>>> md.title
'The Title, A Second Title'

Add a third title (leaves any existing titles in place):

>>> md.add('title', 'Third Title, A')
>>> md['title']
(<music21.metadata.primitives.Text The Title>,
<music21.metadata.primitives.Text A Second Title>,
<music21.metadata.primitives.Text Third Title, A>)
>>> md.title
'The Title, A Second Title, A Third Title'

You can also set/add/get free-form custom metadata items:

>>> md.setCustom('modification description', 'added missing sharp in measure 27')
>>> md.getCustom('modification description')
(<music21.metadata.primitives.Text added missing sharp in measure 27>,)

Adding another custom element for the same description creates a second
entry.

>>> md.addCustom('modification description', 'deleted redundant natural in measure 28')
>>> md.getCustom('modification description')
(<music21.metadata.primitives.Text added missing sharp in measure 27>,
 <music21.metadata.primitives.Text deleted redundant natural in measure 28>)

Metadata does not explicitly support client-specified namespaces, but by using
getCustom/addCustom/setCustom, clients can set anything they want. For instance, to
embed the old SoundTracker .MOD format's sample name, a .MOD file parser could use
`md.addCustom('soundtracker:SampleName', 'Bassoon')`, and a .MOD file writer that
understood 'soundtracker:' metadata could then write it back accurately to one of
those files. Custom metadata (whether namespaced this way, or free form) can also
be written to various other file formats without interpretation, as long as there
is a place for it (e.g. in the '<miscellaneous>' tag in MusicXML).

In music21 v8, primitives.Text has been updated to add `isTranslated` to keep track of
whether the text has been translated,
as well as an encoding scheme, that specifies which standard should be used to parse
the string.  See metadata/primitives.py for more information.
'''

from collections import namedtuple
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
from music21.common import deprecated


from music21.metadata import properties
from music21.metadata.properties import PropertyDescription
from music21.metadata import bundles
from music21.metadata import caching
from music21.metadata import primitives
from music21.metadata.primitives import (Date, DateSingle, DateRelative, DateBetween,
                                         DateSelection, Text, Contributor, Creator,
                                         Imprint, Copyright, ValueType)

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

    To get a simple string, use attribute-style access by unique name.
    Some workIds from music21 v7 have been renamed (e.g. 'date' has been renamed
    to 'dateCreated').  The old music21 v7 name in these cases is still supported
    when you use attribute-style access.

    >>> md = metadata.Metadata(title='Concerto in F')
    >>> md.title
    'Concerto in F'

    Attribute access also works with three-letter workId abbreviations (these are
    grandfathered in from music21 v7; abbreviations have not been added for
    new-in-v8 metadata items):

    >>> md = metadata.Metadata(otl='Concerto in F')
    >>> md.otl
    'Concerto in F'
    >>> md.title
    'Concerto in F'

    It is also possible to set a list/tuple of values or get a tuple full of
    (richer-typed) values using dictionary-style access.

    >>> md = metadata.Metadata()
    >>> md['composer'] = ['Billy Strayhorn', 'Duke Ellington']
    >>> md['composer']
    (<music21.metadata.primitives.Contributor composer:Billy Strayhorn>,
     <music21.metadata.primitives.Contributor composer:Duke Ellington>)
    >>> md.composer
    'Billy Strayhorn and Duke Ellington'
    >>> md.contributors
    (<music21.metadata.primitives.Contributor composer:Billy Strayhorn>,
     <music21.metadata.primitives.Contributor composer:Duke Ellington>)

    allUniqueNames is a list of all the unique names (without any of the
    grandfathered v7 workId synonyms).

    >>> md.allUniqueNames
    ('abstract', 'accessRights', 'accompanyingMaterialWriter', 'actNumber', 'adapter',
     ...
     'commissionedBy', 'compiler', 'composer', 'composerAlias', 'composerCorporate',
     ...
     'lithographer', 'localeOfComposition', 'lyricist',
     ...
     'title', 'transcriber', 'translator', 'type', 'volumeNumber', ...)


    searchAttributes are used by .search() methods to determine what attributes can
    be searched for.  There are some synonyms (like 'dateCreated' and 'date')
    that will find the same items.  This is because some uniqueNames have been
    updated in music21 v8 ('dateCreated'), and the old v7 name ('date') has
    been grandfathered in as a synonym.

    Here is the list of grandfathered v7 synonyms, which may disappear in a
    future version:

    >>> sorted(set(md.searchAttributes) - set(md.allUniqueNames))
    ['commission', 'date', 'dedication', 'volume']

    And here are their new v8 unique/Dublin-Core standard names:

    >>> sorted(metadata.properties.MUSIC21_WORK_ID_TO_UNIQUE_NAME.values())
    ['commissionedBy', 'dateCreated', 'dedicatedTo', 'volumeNumber']
    '''

    # CLASS VARIABLES #

    classSortOrder = -30

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
    ] + properties.ALL_UNIQUE_NAMES))

    searchAttributes: t.Tuple = tuple(sorted(set(
        list(allUniqueNames) + properties.ALL_MUSIC21_WORK_IDS)))

    # INITIALIZER #

    def __init__(self, *args, **keywords):
        super().__init__()

        self._contents: t.Dict[str, t.List[ValueType]] = {}

        # TODO: check pickling, etc.
        self.fileInfo = FileInfo()

        # We allow the setting of metadata values (attribute-style) via **keywords.
        # Any keywords that are uniqueNames, grandfathered workIds, or grandfathered
        # workId abbreviations can be set this way.
        for attr in keywords:
            if attr in properties.ALL_LEGAL_ATTRIBUTES:
                setattr(self, attr, keywords[attr])

        self['software'] = [defaults.software]

# -----------------------------------------------------------------------------
# Public APIs

    def add(self,
            name: str,
            value: t.Union[t.Any, t.Iterable[t.Any]]):
        '''
        Adds a single item or multiple items with this name, leaving any existing
        items with this name in place.

        The name can be the item's uniqueName or 'namespace:name'.  If it is
        not the uniqueName or namespaceName of one of the standard metadata
        properties, KeyError will be raised.

        >>> md = metadata.Metadata()
        >>> md.add('average duration', '180 minutes')
        Traceback (most recent call last):
        KeyError: "Name='average duration' is not a standard metadata name...

        Example of adding a composer and two titles:

        >>> md.add('composer', 'Houcine Slaoui')
        >>> md['composer']
        (<music21.metadata.primitives.Contributor composer:Houcine Slaoui>,)

        >>> md.add('title', metadata.Text('الماريكان', language='ar'))
        >>> md.add('title', metadata.Text('The Americans',  language='en'))
        >>> titles = md['title']
        >>> titles
        (<music21.metadata.primitives.Text الماريكان>,
         <music21.metadata.primitives.Text The Americans>)
        >>> titles[0].language
        'ar'
        >>> titles[1].language
        'en'

        If you do in fact want to overwrite any existing items with this name,
        you can use dictionary-style or attribute-style setting instead.
        See :meth:`~music21.metadata.Metadata.__setitem__` and
        :meth:`~music21.metadata.Metadata.__setattr__` for details.
        '''
        self._add(name, value, isCustom=False)

    def getCustom(self, name: str) -> t.Tuple[ValueType, ...]:
        '''
        Gets any custom-named metadata items. The name can be free-form,
        or it can be a custom 'namespace:name'.

        getCustom always returns t.Tuple[Text, ...], which may be empty.

        >>> md = metadata.Metadata()
        >>> md.setCustom('measure with 2nd ending', 'measure 128')
        >>> md.getCustom('measure with 2nd ending')
        (<music21.metadata.primitives.Text measure 128>,)

        A second item can also be added.

        >>> md.addCustom('measure with 2nd ending', 'measure 192')
        >>> measures = md.getCustom('measure with 2nd ending')

        >>> isinstance(measures, tuple)
        True
        >>> len(measures)
        2
        >>> measures
        (<music21.metadata.primitives.Text measure 128>,
         <music21.metadata.primitives.Text measure 192>)
        '''
        return self._get(name, isCustom=True)

    def addCustom(self, name: str, value: t.Union[t.Any, t.Iterable[t.Any]]):
        '''
        Adds any custom-named metadata items. The name can be free-form,
        or it can be a custom 'namespace:name'.

        addCustom takes a single object of any type, or a list/tuple of
        objects of any type.  The object(s) will be converted to Text.

        >>> md = metadata.Metadata()
        >>> md.addCustom('measure with 2nd ending', 'measure 128')
        >>> md.getCustom('measure with 2nd ending')
        (<music21.metadata.primitives.Text measure 128>,)

        An item list can also be added.

        >>> md.addCustom('measure with 2nd ending', ['measure 192', 'measure 256'])
        >>> measures = md.getCustom('measure with 2nd ending')

        >>> isinstance(measures, tuple)
        True
        >>> len(measures)
        3
        >>> measures
        (<music21.metadata.primitives.Text measure 128>,
         <music21.metadata.primitives.Text measure 192>,
         <music21.metadata.primitives.Text measure 256>)
        '''
        self._add(name, value, isCustom=True)

    def setCustom(self, name: str, value: t.Union[t.Any, t.Iterable[t.Any]]):
        '''
        Sets any custom-named metadata items (deleting any existing such items).
        The name can be free-form, or it can be a custom 'namespace:name'.

        setCustom takes a single object of any type, or a list/tuple of
        objects of any type.  The object(s) will be converted to Text.

        >>> md = metadata.Metadata()
        >>> md.setCustom('measure with 2nd ending', 'measure 128')
        >>> md.getCustom('measure with 2nd ending')
        (<music21.metadata.primitives.Text measure 128>,)

        An item list can also be set.

        >>> md.setCustom('measure with 2nd ending', ['measure 192', 'measure 256'])
        >>> measures = md.getCustom('measure with 2nd ending')

        >>> isinstance(measures, tuple)
        True
        >>> len(measures)
        2
        >>> measures
        (<music21.metadata.primitives.Text measure 192>,
         <music21.metadata.primitives.Text measure 256>)
        '''
        self._set(name, value, isCustom=True)

    def getAllNamedValues(self, skipContributors=False) -> t.Tuple[t.Tuple[str, ValueType], ...]:
        '''
        Returns all values stored in this metadata as a tuple of (name, value) tuples.
        Names with multiple values will appear multiple times in the list (rather
        than appearing once, with a value that is a list of values).
        The tuple's first element (the name) is either of the form 'namespace:name', or a
        custom name (with no form at all).

        >>> md = metadata.Metadata()
        >>> md.add('composer', 'Jeff Bowen')
        >>> md.add('librettist', 'Hunter Bell')
        >>> md.add('title', 'Other World')
        >>> md.addCustom('excerpt-start-measure', 1234)
        >>> allMd = md.getAllNamedValues()
        >>> allMd
        (('musicxml:software', <music21.metadata.primitives.Text music21 v...>),
         ('marcrel:CMP', <music21.metadata.primitives.Contributor composer:Jeff Bowen>),
         ('marcrel:LBT', <music21.metadata.primitives.Contributor librettist:Hunter Bell>),
         ('dcterms:title', <music21.metadata.primitives.Text Other World>),
         ('excerpt-start-measure', <music21.metadata.primitives.Text 1234>))
        >>> allNonContributors = md.getAllNamedValues(skipContributors=True)
        >>> allNonContributors
        (('musicxml:software', <music21.metadata.primitives.Text music21 v...>),
         ('dcterms:title', <music21.metadata.primitives.Text Other World>),
         ('excerpt-start-measure', <music21.metadata.primitives.Text 1234>))
        '''
        allOut: t.List[t.Tuple[str, ValueType]] = []

        valueList: t.List[ValueType]
        for name, valueList in self._contents.items():
            if skipContributors and self._isContributorNamespaceName(name):
                continue

            value: ValueType
            for value in valueList:
                allOut.append((name, value))

        return tuple(allOut)

    def getAllContributorNamedValues(self) -> t.Tuple[t.Tuple[str, Contributor], ...]:
        '''
        Returns all contributors stored in this metadata as a tuple of (name, value) tuples.
        The individual tuple's first element (the name) will be of the form 'namespace:name'.
        Contributors with a custom role should have a uniqueName of 'otherContributor' (i.e.
        a namespaceName of 'marcrel:CTB'), and have their `value.role` field set to the custom
        role.

        >>> md = metadata.Metadata()
        >>> md['title'] = ['Dimitrij', 'False Dmitry']
        >>> md.composer = 'Antonín Dvořák'
        >>> md.opusNumber = 64
        >>> md.add('librettist', 'Marie Červinková-Riegrová')
        >>> md['otherContributor'] = (
        ...     metadata.Contributor(
        ...         role='based on plot by',
        ...         name ='Ferdinand Mikovec'
        ...     ),
        ...     metadata.Contributor(
        ...         role='original partial plot by',
        ...         name='Friedrich Schiller'
        ...     )
        ... )
        >>> md.addCustom('average duration', '180 minutes')

        The non-contributor items (title, opusNumber, average duration) will not appear
        in the returned list of all contributors.

        >>> allContributors = md.getAllContributorNamedValues()
        >>> allContributors
        (('marcrel:CMP', <music21.metadata.primitives.Contributor composer:Antonín Dvořák>),
         ('marcrel:LBT',
          <music21.metadata.primitives.Contributor librettist:Marie Červinková-Riegrová>),
         ('marcrel:CTB',
          <music21.metadata.primitives.Contributor based on plot by:Ferdinand Mikovec>),
         ('marcrel:CTB',
          <music21.metadata.primitives.Contributor original partial plot by:Friedrich Schiller>))
        '''

        allOut: t.List[t.Tuple[str, Contributor]] = []

        for name, value in self._contents.items():
            if not self._isContributorNamespaceName(name):
                continue

            for v in value:
                assert isinstance(v, Contributor)
                allOut.append((name, v))

        return tuple(allOut)

# -----------------------------------------------------------------------------
#   A few static utility routines for clients calling public APIs

    @staticmethod
    def uniqueNameToNamespaceName(uniqueName: str) -> t.Optional[str]:
        '''
        Translates a unique name to the associated standard property's
        namespace name (i.e. the property's name in the form 'namespace:name').

        An example from the MARC Relators namespace: the namespace name of
        'librettist' is 'marcrel:LBT'.

        >>> metadata.Metadata.uniqueNameToNamespaceName('librettist')
        'marcrel:LBT'

        Returns None if no such associated standard property can be found.

        >>> metadata.Metadata.uniqueNameToNamespaceName('average duration') is None
        True

        An example from the Dublin Core namespace: the namespace name of
        'alternativeTitle' is 'dcterms:alternative'.

        >>> metadata.Metadata.uniqueNameToNamespaceName('alternativeTitle')
        'dcterms:alternative'
        '''

        return properties.UNIQUE_NAME_TO_NAMESPACE_NAME.get(uniqueName, None)

    @staticmethod
    def namespaceNameToUniqueName(namespaceName: str) -> t.Optional[str]:
        '''
        Translates a standard property namespace name ('namespace:name') to that
        standard property's uniqueName.

        An example from the MARC Relators namespace: the unique name of
        'marcrel:LBT' is 'librettist'.

        >>> metadata.Metadata.namespaceNameToUniqueName('marcrel:LBT')
        'librettist'

        Returns None if no such standard property exists.

        >>> metadata.Metadata.namespaceNameToUniqueName('soundtracker:SampleName') is None
        True

        An example from the Dublin Core namespace: the unique name of
        'dcterms:alternative' is 'alternativeTitle'.

        >>> metadata.Metadata.namespaceNameToUniqueName('dcterms:alternative')
        'alternativeTitle'
        '''
        return properties.NAMESPACE_NAME_TO_UNIQUE_NAME.get(namespaceName, None)

    @staticmethod
    def isContributorUniqueName(uniqueName: t.Optional[str]) -> bool:
        '''
        Determines if a unique name is associated with a standard contributor
        property.  Returns False if no such associated standard contributor
        property can be found.

        We allow uniqueName == None, since None is a valid custom contributor role.

        Example: 'librettist' and 'otherContributor' are unique names of standard
        contributors.

        >>> metadata.Metadata.isContributorUniqueName('librettist')
        True
        >>> metadata.Metadata.isContributorUniqueName('otherContributor')
        True

        Example: 'alternativeTitle' is the unique name of a standard property,
        but it is not a contributor.

        >>> metadata.Metadata.isContributorUniqueName('alternativeTitle')
        False

        Example: 'average duration' is not the unique name of a standard property.

        >>> metadata.Metadata.isContributorUniqueName('average duration')
        False
        '''
        if not uniqueName:
            return False
        prop: t.Optional[PropertyDescription] = (
            properties.UNIQUE_NAME_TO_PROPERTY_DESCRIPTION.get(uniqueName, None)
        )
        if prop is None:
            return False

        return prop.isContributor

    @staticmethod
    def isStandardName(name: str) -> bool:
        '''
        Determines if name is either a 'namespace:name' or a 'uniqueName'
        associated with a standard property.

        Returns False if no such associated standard property can be found.

        >>> metadata.Metadata.isStandardName('librettist')
        True

        'marcrel:LBT' is the namespace name of 'librettist'

        >>> metadata.Metadata.isStandardName('marcrel:LBT')
        True

        Some examples of non-standard (custom) names.

        >>> metadata.Metadata.isStandardName('average duration')
        False
        >>> metadata.Metadata.isStandardName('soundtracker:SampleName')
        False
        '''
        if Metadata._isStandardNamespaceName(name):
            return True

        if Metadata._isStandardUniqueName(name):
            return True

        return False



# -----------------------------------------------------------------------------
#   Public APIs

    @property
    def software(self) -> t.Tuple[str, ...]:
        '''
        Returns a tuple of software names/versions.

        Returns an empty tuple if no software names/versions exist,
        but this is rare, since music21 adds its own version when
        initializing a Metadata object.

        >>> md = metadata.Metadata()
        >>> md.software
        ('music21 v...',)
        >>> md.add('software', 'Finale for Macintosh')
        >>> md.software
        ('music21 v...',
         'Finale for Macintosh')
        >>> md['software']
        (<music21.metadata.primitives.Text music21 v...>,
         <music21.metadata.primitives.Text Finale for Macintosh>)
        '''
        # software is a bit of an exception: it looks singular, but it's actually
        # plural (with no singular attribute at all).
        return self._getPluralAttribute('software')

    @property
    def contributors(self) -> t.Tuple[Contributor, ...]:
        '''
        Returns a tuple of all the Contributors found in the metadata.
        Returns an empty tuple if no Contributors exist.

        >>> md = metadata.Metadata()
        >>> md['composer'] = ['Richard Strauss']
        >>> md.librettist = 'Oscar Wilde'

        When we add a title (whether through `.attribute` setting, `[item]` setting,
        or the :meth:`~music21.metadata.Metadata.add` method), it will not show up
        in the list of contributors.

        >>> md.add('title', 'Salome')
        >>> contribs = md.contributors
        >>> contribs
        (<music21.metadata.primitives.Contributor composer:Richard Strauss>,
         <music21.metadata.primitives.Contributor librettist:Oscar Wilde>)
        '''
        output: t.List[Contributor] = []
        for _, contrib in self.getAllContributorNamedValues():
            output.append(contrib)
        return tuple(output)

    @property
    def copyright(self):
        '''
        Returns the copyright as a str.
        Returns None if no copyright exists in the metadata.
        Returns all the copyright values in one string (with ', ' between them)
        if multiple copyrights exist in the metadata. Use md['copyright'] to
        get all the copyrights as Copyright objects.

        >>> md = metadata.Metadata()
        >>> md.copyright is None
        True
        >>> md.copyright = 'Copyright © 1896, Éditions Durand (expired)'
        >>> md.copyright
        'Copyright © 1896, Éditions Durand (expired)'

        Using dictionary-style access, you can use either the uniqueName ('copyright')
        or the namespaceName ('dcterms:rights').  Here you can see how multiple
        copyrights are handled.

        >>> md.copyright = 'Copyright © 1984 All Rights Reserved'
        >>> md.copyright
        'Copyright © 1984 All Rights Reserved'

        To add another copyright to the list, call md.add().

        >>> md.add('copyright', 'Lyrics copyright © 1987 All Rights Reserved')

        md.copyright will now return both copyrights in one string

        >>> md.copyright
        'Copyright © 1984 All Rights Reserved, Lyrics copyright © 1987 All Rights Reserved'

        md['copyright'] will return a tuple containing both Copyright objects.

        >>> md['copyright']
        (<music21.metadata.primitives.Copyright Copyright © 1984 All Rights Reserved>,
         <music21.metadata.primitives.Copyright Lyrics copyright © 1987 All Rights Reserved>)

        You can set str, Text, or Copyright values, and they will be converted to
        Copyright automatically if necessary.  Note that 'dcterms:rights'
        is Dublin Core terminology for 'copyright', and can be used interchangeably
        with 'copyright' as a metadata dictionary-style key.

        >>> md.copyright = metadata.Text('Copyright © 1984')
        >>> md['copyright']
        (<music21.metadata.primitives.Copyright Copyright © 1984>,)
        >>> md.copyright = metadata.Copyright('Copyright © 1985', role='something')
        >>> md['dcterms:rights']
        (<music21.metadata.primitives.Copyright Copyright © 1985>,)
        '''
        return self._getSingularAttribute('copyright')

    # SPECIAL METHODS #
    def all(self, skipContributors=False):
        # noinspection SpellCheckingInspection,PyShadowingNames
        '''
        Returns all values stored in this metadata as a sorted Tuple of Tuple[str, str].
        Each individual Tuple is (uniqueName, stringValue).

        >>> c = corpus.parse('corelli/opus3no1/1grave')
        >>> c.metadata.all()
        (('arranger', 'Michael Scott Cuthbert'),
         ('composer', 'Arcangelo Corelli'),
         ('copyright', '© 2014, Creative Commons License (CC-BY)'),
         ('fileFormat', 'musicxml'),
         ('filePath', '...corpus/corelli/opus3no1/1grave.xml'),
         ('movementName', 'Sonata da Chiesa, No. I (opus 3, no. 1)'),
         ('software', 'music21 v...'))

        >>> c.metadata.date = metadata.DateRelative('1689', 'onOrBefore')
        >>> c.metadata.localeOfComposition = 'Rome'
        >>> c.metadata.all(skipContributors=True)
        (('copyright', '© 2014, Creative Commons License (CC-BY)'),
         ('dateCreated', '1689/--/-- or earlier'),
         ('fileFormat', 'musicxml'),
         ('filePath', '...corpus/corelli/opus3no1/1grave.xml'),
         ('localeOfComposition', 'Rome'),
         ('movementName', 'Sonata da Chiesa, No. I (opus 3, no. 1)'),
         ('software', 'music21 v...'))
        '''
        # pylint: disable=undefined-variable
        allOut = {}

        for uniqueName in self.allUniqueNames:
            try:
                values: t.Tuple[str, ...] = self._getStringValuesByNamespaceName(
                    properties.UNIQUE_NAME_TO_NAMESPACE_NAME[uniqueName]
                )
                if not values:
                    continue
                val = values[0]
            except AttributeError:
                continue
            except KeyError:
                # A uniqueName that doesn't have a PropertyDescription
                # That's the three fileInfo properties, just get them
                # attribute-style (i.e. as string)
                if uniqueName == 'fileFormat':
                    val = str(self.fileFormat)
                elif uniqueName == 'filePath':
                    val = str(self.filePath)
                elif uniqueName == 'fileNumber':
                    val = str(self.fileNumber)
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

        return tuple(sorted(allOut.items()))

    def __getattr__(self, name):
        '''
        Utility attribute access for all uniqueNames, grandfathered workIds,
        and grandfathered workId abbreviations.  Many grandfathered workIds
        have explicit property definitions, so they won't end up here.

        These always return str or None.  If there is more than one item
        for a particular name, we will try to summarize or list them all
        in one returned string.

        If name is not a valid attribute (uniqueName, grandfathered workId,
        or grandfathered workId abbreviation), then AttributeError is raised.

        >>> md = metadata.Metadata()

        An example of setting an attribute by uniqueName ('description').

        >>> md.description = metadata.Text('A description set via uniqueName', language='en')

        An example of setting an attribute by grandfathered workId ('dedication')

        >>> md.dedication = 'A dedication set via grandfathered workId'

        An example of setting an attribute by grandfathered workId abbreviation ('otl')

        >>> md.otl = metadata.Text('A title set via grandfathered workId abbreviation')

        See how we can get all three attributes by uniqueName, even though two of them
        were set by other names.

        An example of getting (by uniqueName) an attribute that was set by uniqueName.

        >>> md.description
        'A description set via uniqueName'

        An example of getting (by uniqueName) an attribute that was set by workId.
        The uniqueName for the grandfathered workId 'dedication' is 'dedicatedTo'.

        >>> md.dedicatedTo
        'A dedication set via grandfathered workId'

        An example of getting (by uniqueName) an attribute that was set by abbreviation.
        The uniqueName for the grandfathered workId abbreviation 'otl' is 'title'.

        >>> md.title
        'A title set via grandfathered workId abbreviation'

        An example of getting an attribute for which there are multiple values.

        >>> md.add('description', 'A description added via md.add()')
        >>> md.description
        'A description set via uniqueName, A description added via md.add()'
        '''

        # __getattr__ is the call of last resort after looking for bare attributes
        # and property methods, so __getattr__ won't be called (e.g.) for self.composer
        # (a property method), even though we certainly could handle that here. This is
        # why we don't have to handle .composers/librettists/lyricists or .fileFormat/
        # .filePath/.fileNumber here, like we do in __setattr__ (which is the only call
        # you get if you implement it, so it has to handle everything).
        return self._getSingularAttribute(name)

    def __setattr__(self, name: str, value: t.Any):
        '''
        Attribute setter for all uniqueNames, grandfathered workIds,
        and grandfathered workId abbreviations, as well as the plural
        properties ('composers', 'librettists', 'lyricists') and the
        three new fileInfo properties.

        These can take a single value of any type (or, if appropriate, an
        iterable of any type of value), and will convert to the appropriate
        internal valueType.
        '''

        # Implementation note: __setattr__ has a very different role from
        # __getattr__.  __getattr__ is the call of last resort after looking
        # for bare attributes and property methods, so __getattr__ won't be
        # called for (e.g.) self.composer (a property).  __setattr__, on the
        # other hand, is the _only_ call you will get.  So after checking for
        # uniqueNames, workIds, and workId abbreviations, if we haven't done
        # the job yet, we need to make a call to super().__setattr__ to handle
        # all the bare attributes, including in base classes (e.g. Music21Object).
        # Unfortunately, super().__setattr__ will not call our property.setters,
        # so all property.setters have been removed, and handled explicitly here.

        if name in properties.ALL_SINGLE_ATTRIBUTE_NAMES:
            if (value is not None
                    and isinstance(value, t.Iterable)
                    and not isinstance(value, str)):
                raise ValueError(f'md.{name} can only be set to a single value; '
                                 f'set md[{name}] to multiple values instead.')

        if name in properties.ALL_PLURAL_ATTRIBUTE_NAMES:
            if not isinstance(value, t.Iterable) or isinstance(value, str):
                raise ValueError(
                    f'md.{name} can only be set to an iterable (e.g. a list, tuple, etc).'
                )

        # Is name a uniqueName?
        if name in properties.UNIQUE_NAME_TO_NAMESPACE_NAME:
            self._set(
                properties.UNIQUE_NAME_TO_NAMESPACE_NAME[name],
                value,
                isCustom=False
            )
            return

        # Is name a grandfathered workId?
        if name in properties.MUSIC21_WORK_ID_TO_NAMESPACE_NAME:
            self._set(
                properties.MUSIC21_WORK_ID_TO_NAMESPACE_NAME[name],
                value,
                isCustom=False
            )
            return

        # Is name a grandfathered workId abbreviation?
        if name in properties.MUSIC21_ABBREVIATION_TO_NAMESPACE_NAME:
            self._set(
                properties.MUSIC21_ABBREVIATION_TO_NAMESPACE_NAME[name],
                value,
                isCustom=False
            )
            return

        # Is name one of the three grandfathered plural contributor
        # attribute setters?
        if name in ('composers', 'librettists', 'lyricists'):
            uniqueName = name[:-1]  # remove the trailing 's'
            self._set(uniqueName, value, isCustom=False)
            return

        # Is name one of the new fileInfo attribute setters?
        if name == 'fileFormat':
            if value is None:
                self.fileInfo.format = None
            else:
                self.fileInfo.format = Text(value)
            return

        if name == 'filePath':
            if value is None:
                self.fileInfo.path = None
            else:
                self.fileInfo.path = Text(value)
            return

        if name == 'fileNumber':
            if value is None:
                self.fileInfo.number = None
            else:
                self.fileInfo.number = int(value)
            return

        # OK, we've covered everything we know about; fall back to setting
        # bare attributes (including the ones in base classes).
        super().__setattr__(name, value)

    def __getitem__(self, key: str) -> t.Tuple[ValueType, ...]:
        '''
        "Dictionary key" access for all standard uniqueNames and
        standard keys of the form 'namespace:name'.

        These always return t.Tuple[ValueType, ...], which may be empty.

        If key is not a standard uniqueName or standard 'namespace:name',
        then KeyError is raised.

        >>> md = metadata.Metadata()
        >>> md['average duration']
        Traceback (most recent call last):
        KeyError: "Name='average duration' is not a standard metadata name...

        Example: setting, then getting (dictionary style) a single value. Note that
        it must be set as a single element list/tuple, and is always returned as a
        single element tuple.

        >>> md['description'] = [
        ...     metadata.Text('For the coronation of Catherine the Great.', language='en')
        ... ]
        >>> descs = md['description']
        >>> descs
        (<music21.metadata.primitives.Text For the coronation of Catherine the Great.>,)

        A second description can also be added.

        >>> md.add('description', 'In five sections, unique for its time.')
        >>> descs = md['description']
        >>> isinstance(descs, tuple)
        True
        >>> len(descs)
        2
        >>> descs
        (<music21.metadata.primitives.Text For the coronation of Catherine the Great.>,
         <music21.metadata.primitives.Text In five sections, unique for its time.>)
        >>> descs[0].language
        'en'
        >>> descs[1].language is None
        True
        '''
        if not isinstance(key, str):
            raise KeyError('metadata key must be str')

        return self._get(key, isCustom=False)

    def __setitem__(self, key: str, value: t.Union[t.Any, t.Iterable[t.Any]]):
        '''
        "Dictionary key" access for all standard uniqueNames and
        standard keys of the form 'namespace:name'.

        If key is not a standard uniqueName or standard 'namespace:name',
        then KeyError is raised.

        >>> md = metadata.Metadata()
        >>> md['average duration'] = ['180 minutes']
        Traceback (most recent call last):
        KeyError: "Name='average duration' is not a standard metadata name...

        KeyError is also raised for non-str keys.

        >>> md[3] = ['180 minutes']
        Traceback (most recent call last):
        KeyError: 'metadata key must be str'

        '''
        if not isinstance(key, str):
            raise KeyError('metadata key must be str')

        self._set(key, value, isCustom=False)

    def addContributor(self, c):
        # noinspection PyShadowingNames
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
        ('Beach, Amy', 'Cheney, Amy Marcy')

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
        namespaceName: str = self._contributorRoleToNamespaceName(c.role)
        self._add(namespaceName, c, isCustom=False)

    def getContributorsByRole(self, role: t.Optional[str]) -> t.Tuple[Contributor, ...]:
        r'''
        Return a :class:`~music21.metadata.Contributor` if defined for a
        provided role.

        We allow role == None, since None is a valid custom contributor role.

        >>> md = metadata.Metadata(title='Violin Concerto')

        >>> c = metadata.Contributor()
        >>> c.name = 'Price, Florence'
        >>> c.role = 'composer'
        >>> md.addContributor(c)
        >>> cTuple = md.getContributorsByRole('composer')
        >>> cTuple
        (<music21.metadata.primitives.Contributor composer:Price, Florence>,)

        >>> cTuple[0].name
        'Price, Florence'

        Some musicxml files have contributors with no role defined.  To get
        these contributors, search for getContributorsByRole(None).  N.B. upon
        output to MusicXML, music21 gives these contributors the generic role
        of "creator"

        >>> c2 = metadata.Contributor()
        >>> c2.name = 'Baron van Swieten'
        >>> md.add('otherContributor', c2)
        >>> noRoleTuple = md.getContributorsByRole(None)
        >>> len(noRoleTuple)
        1
        >>> noRoleTuple[0].role is None
        True
        >>> noRoleTuple[0].name
        'Baron van Swieten'
        '''
        result: t.List[Contributor] = []  # there may be more than one per role
        for _, contrib in self.getAllContributorNamedValues():
            if contrib.role == role:
                result.append(contrib)
        return tuple(result)

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


    # When deprecated setWorkId is removed, this dictionary can be removed as well.
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

    @deprecated('v8', 'v9', 'use `md.uniqueName = value` or `md[\'uniqueName\'] = [value]`')
    def setWorkId(self, idStr, value):
        idStr = idStr.lower()
        match = False
        for abbreviation, workId in self.workIdAbbreviationDict.items():
            if workId.lower() == idStr or abbreviation == idStr:
                setattr(self, workId, value)
                match = True
                break
        if not match:
            raise exceptions21.MetadataException(
                f'no work id available with id: {idStr}')

    @property
    def alternativeTitle(self):
        r'''
        Get or set the alternative title.

        >>> md = metadata.Metadata(popularTitle='Eroica')
        >>> md.alternativeTitle = 'Heroic Symphony'
        >>> md.alternativeTitle
        'Heroic Symphony'
        '''
        return self._getSingularAttribute('alternativeTitle')

    @property
    def composer(self):
        r'''
        Get or set the composer of this work. Only the first composer can be
        got or set via properties.

        The composer attribute does not live in Metadata, but creates a
        :class:`~music21.metadata.Contributor` object in the .contributors
        object.

        >>> md = metadata.Metadata(
        ...     title='...(Iphigenia)',
        ...     )
        >>> md.composer = 'Shorter, Wayne'

        You can set multiple composers by setting them dictionary-style
        or by using `md.add`.
        >>> md.add('composer', 'Spalding, Esperanza')

        The `Metadata.composer` attribute returns a summary string if there is
        more than one composer.

        >>> md.composer
        'Shorter, Wayne and Spalding, Esperanza'
        '''
        return self._getSingularAttribute('composer')

    @property
    def composers(self):
        r'''
        Get a tuple or set an iterable of strings of all composer roles.

        >>> md = metadata.Metadata(title='Yellow River Concerto')
        >>> md.composers = ['Xian Xinghai', 'Yin Chengzong']

        (Yin Chengzong might be better called "Arranger" but this is for
        illustrative purposes)

        >>> md.composers
        ('Xian Xinghai', 'Yin Chengzong')


        Might as well add a third composer to the concerto committee?

        >>> contrib3 = metadata.Contributor(role='composer', name='Chu Wanghua')
        >>> md.add('composer', contrib3)
        >>> md.composers
        ('Xian Xinghai', 'Yin Chengzong', 'Chu Wanghua')

        If there are no composers, returns an empty list:

        >>> md = metadata.Metadata(title='Sentient Algorithmic Composition')
        >>> md.composers
        ()
        '''
        return self._getPluralAttribute('composer')

    @property
    def date(self):
        '''
        The `.date` property is deprecated in v8 and will be removed in v10.
        Use `dateCreated` instead.
        '''
        return self.dateCreated

    @property
    def dateCreated(self):
        r'''
        Get or set the creation date of this work as one of the following date
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
        >>> md.dateCreated = '1805'
        >>> md.dateCreated
        '1805/--/--'

        >>> md.dateCreated = metadata.DateBetween(['1803/01/01', '1805/04/07'])
        >>> md.dateCreated
        '1803/01/01 to 1805/04/07'
        '''
        return self._getSingularAttribute('dateCreated')

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
    def fileNumber(self) -> t.Optional[str]:
        '''
        Get or set the file number that was parsed.
        '''
        if self.fileInfo.number:
            return str(self.fileInfo.number)

    @property
    def localeOfComposition(self):
        r'''
        Get or set the locale of composition, or origin, of the work.

        >>> md = metadata.Metadata(popularTitle='Eroica')
        >>> md.localeOfComposition = 'Paris, France'
        >>> md.localeOfComposition
        'Paris, France'
        '''
        return self._getSingularAttribute('localeOfComposition')

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
        return self._getSingularAttribute('librettist')

    @property
    def librettists(self):
        r'''
        Gets a tuple or sets an iterable of librettists for this work:

        >>> md = metadata.Metadata(title='Madama Butterfly')
        >>> md.librettists = ['Illica, Luigi', 'Giacosa, Giuseppe']
        >>> md.librettists
        ('Illica, Luigi', 'Giacosa, Giuseppe')

        Should be distinguished from lyricists etc.
        '''
        return self._getPluralAttribute('librettist')

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
        return self._getSingularAttribute('lyricist')

    @property
    def lyricists(self):
        r'''
        Gets a tuple or sets an iterable of lyricists for this work:

        >>> md = metadata.Metadata(title='Rumors')
        >>> md.lyricists = ['Buckingham, Lindsey', 'McVie, Christine', 'Nicks, Stevie']
        >>> md.lyricists
        ('Buckingham, Lindsey', 'McVie, Christine', 'Nicks, Stevie')

        Should be distinguished from librettists etc.
        '''
        return self._getPluralAttribute('lyricist')

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
        return self._getSingularAttribute('movementName')

    @property
    def movementNumber(self) -> t.Optional[str]:
        r'''
        Get or set the movement number as a string (or None)

        >>> md = metadata.Metadata(title='Ode to Joy')
        >>> md.movementNumber = 4

        Note that movement numbers are always returned as strings!  This may
        change in the future.

        >>> md.movementNumber
        '4'
        '''
        return self._getSingularAttribute('movementNumber')

    @property
    def number(self) -> t.Optional[str]:
        r'''
        Get or set the number of the work within a collection of pieces,
        as a string. (for instance, the number within a collection of ABC files)

        >>> md = metadata.Metadata()
        >>> md.number = '4'

        Note that numbers are always returned as strings!  This may
        change in the future.

        >>> md.number
        '4'

        However, it is acceptable to set it as an int:

        >>> md.number = 2
        >>> md.number
        '2'
        '''
        return self._getSingularAttribute('number')

    @property
    def opusNumber(self) -> t.Optional[str]:
        r'''
        Get or set the opus number.

        >>> md = metadata.Metadata()
        >>> md.opusNumber = 56

        Note that opusNumbers are always returned as strings!  This may
        change in the future, however, it is less likely to change
        than `.number` or `.movementNumber` since Opus numbers such as
        `18a` are common.

        >>> md.opusNumber
        '56'

        There is no enforcement that only numbers actually called "opus"
        are used, and it could be used for other catalogue numbers.

        >>> md.opusNumber = 'K.622'
        '''
        return self._getSingularAttribute('opusNumber')

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
        for uniqueName in searchId:
            titles = self._get(uniqueName, isCustom=False)
            if not titles:  # get first matched
                continue

            return self._getStringValueByNamespaceName(
                properties.UNIQUE_NAME_TO_NAMESPACE_NAME[uniqueName]
            )

        return None

# -----------------------------------------------------------------------------
# Internal support routines (many of them static).

    def _getStringValueByNamespaceName(self, namespaceName: str) -> t.Optional[str]:
        '''
        Gets a single str value (a summary if necessary) for a supported
        'namespace:name'.

        >>> md = metadata.Metadata()
        >>> md['title'] = ['The Title', 'A Second Title']
        >>> md._getStringValueByNamespaceName('dcterms:title')
        'The Title, A Second Title'

        Returns None  (rather than raising KeyError) if namespaceName
        is not a supported 'namespace:name'.

        >>> md.setCustom('average duration', '180 minutes')
        >>> md._getStringValueByNamespaceName('average duration') is None
        True

        Returns None if the namespaceName is supported, but no such
        metadata item exists.

        >>> md._getStringValueByNamespaceName('dcterms:alternative') is None
        True

        Performs article normalization on metadata properties that are declared
        as needing it (generally, title-like properties).

        >>> md['alternativeTitle'] = ['Alternative Title, The', 'Second Alternative Title, A']
        >>> md._getStringValueByNamespaceName('dcterms:alternative')
        'The Alternative Title, A Second Alternative Title'
        '''
        if namespaceName not in properties.ALL_NAMESPACE_NAMES:
            return None

        values: t.Tuple[ValueType, ...] = self._get(namespaceName, isCustom=False)
        if not values:
            return None

        if self._isContributorNamespaceName(namespaceName):
            if len(values) == 1:
                return str(values[0])
            if len(values) == 2:
                return str(values[0]) + ' and ' + str(values[1])
            return str(values[0]) + f' and {len(values)-1} others'

        if self._namespaceNameNeedsArticleNormalization(namespaceName):
            output: str = ''
            for i, value in enumerate(values):
                assert isinstance(value, Text)
                if i > 0:
                    output += ', '
                output += value.getNormalizedArticle()
            return output

        return ', '.join(str(value) for value in values)

    def _getStringValuesByNamespaceName(self, namespaceName: str) -> t.Tuple[str, ...]:
        '''
        Gets a tuple of str values for a supported 'namespace:name'.

        >>> md = metadata.Metadata()
        >>> md['title'] = ['The Title', 'A Second Title']
        >>> md._getStringValuesByNamespaceName('dcterms:title')
        ('The Title', 'A Second Title')

        Returns an empty tuple (rather than raising KeyError) if namespaceName
        is not a supported 'namespace:name'.

        >>> md.setCustom('average duration', '180 minutes')
        >>> md._getStringValuesByNamespaceName('average duration')
        ()

        Returns an empty tuple if the namespaceName is supported, but no such
        metadata item exists.

        >>> md._getStringValuesByNamespaceName('dcterms:alternative')
        ()

        Performs article normalization on metadata properties that are declared
        as needing it (generally, title-like properties).

        >>> md['alternativeTitle'] = ['Alternative Title, The', 'Second Alternative Title, A']
        >>> md._getStringValuesByNamespaceName('dcterms:alternative')
        ('The Alternative Title', 'A Second Alternative Title')
        '''
        if namespaceName not in properties.ALL_NAMESPACE_NAMES:
            return tuple()

        values: t.Tuple[ValueType, ...] = self._get(namespaceName, isCustom=False)
        if not values:
            return tuple()

        if self._namespaceNameNeedsArticleNormalization(namespaceName):
            output: t.List[str] = []
            for value in values:
                assert isinstance(value, Text)
                output.append(value.getNormalizedArticle())
            return tuple(output)

        return tuple(str(value) for value in values)

    def _getPluralAttribute(self, attributeName: str) -> t.Tuple[str, ...]:
        '''
        This does what __getattr__ would do if we supported plural attributeNames
        (but it takes singular attributeNames, of course).  It returns a tuple
        of strings (perhaps empty) for supported uniqueNames, grandfathered
        workIds, and grandfathered workId abbrevations.  It is used in search,
        as well as in the various plural properties, such as md.composers, etc.

        >>> md = metadata.Metadata()
        >>> md['dedicatedTo'] = ('The First Dedicatee', 'A Second Dedicatee')

        Example: _getPluralAttribute by uniqueName

        >>> md._getPluralAttribute('dedicatedTo')
        ('The First Dedicatee', 'A Second Dedicatee')

        Example: _getPluralAttribute by grandfathered workId

        >>> md._getPluralAttribute('dedication')
        ('The First Dedicatee', 'A Second Dedicatee')

        Example: _getPluralAttribute by grandfathered workId abbreviation

        >>> md._getPluralAttribute('ode')
        ('The First Dedicatee', 'A Second Dedicatee')

        It raises AttributeError if attributeName is not a valid uniqueName,
        workId, or workId abbreviation.

        Example: _getPluralAttribute by 'namespace:name'

        >>> md._getPluralAttribute('humdrum:ODE')
        Traceback (most recent call last):
        AttributeError: invalid attributeName: humdrum:ODE
        '''
        if attributeName in properties.UNIQUE_NAME_TO_NAMESPACE_NAME:
            return self._getStringValuesByNamespaceName(
                properties.UNIQUE_NAME_TO_NAMESPACE_NAME[attributeName]
            )

        # Is attributeName a grandfathered workId?
        if attributeName in properties.MUSIC21_WORK_ID_TO_NAMESPACE_NAME:
            return self._getStringValuesByNamespaceName(
                properties.MUSIC21_WORK_ID_TO_NAMESPACE_NAME[attributeName]
            )

        # Is attributeName a grandfathered workId abbreviation?
        if attributeName in properties.MUSIC21_ABBREVIATION_TO_NAMESPACE_NAME:
            return self._getStringValuesByNamespaceName(
                properties.MUSIC21_ABBREVIATION_TO_NAMESPACE_NAME[attributeName]
            )

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
            return (str(self.fileNumber),)

        raise AttributeError(f'invalid attributeName: {attributeName}')

    def _getSingularAttribute(self, attributeName: str) -> t.Optional[str]:
        '''
        This returns a single string (perhaps a summary) for supported uniqueNames,
        grandfathered workIds, and grandfathered workId abbrevations.

        >>> md = metadata.Metadata()
        >>> md['dedicatedTo'] = ('The First Dedicatee', 'A Second Dedicatee')

        Example: _getSingularAttribute by uniqueName

        >>> md._getSingularAttribute('dedicatedTo')
        'The First Dedicatee, A Second Dedicatee'

        Example: _getSingularAttribute by grandfathered workId

        >>> md._getSingularAttribute('dedication')
        'The First Dedicatee, A Second Dedicatee'

        Example: _getSingularAttribute by grandfathered workId abbreviation

        >>> md._getSingularAttribute('ode')
        'The First Dedicatee, A Second Dedicatee'

        It raises AttributeError if attributeName is not a valid uniqueName,
        workId, or workId abbreviation.

        Example: _getSingularAttribute by 'namespace:name'

        >>> md._getSingularAttribute('humdrum:ODE')
        Traceback (most recent call last):
        AttributeError: object has no attribute: humdrum:ODE
        '''
        if attributeName in properties.UNIQUE_NAME_TO_NAMESPACE_NAME:
            return self._getStringValueByNamespaceName(
                properties.UNIQUE_NAME_TO_NAMESPACE_NAME[attributeName]
            )

        # Is name a grandfathered workId?
        if attributeName in properties.MUSIC21_WORK_ID_TO_NAMESPACE_NAME:
            return self._getStringValueByNamespaceName(
                properties.MUSIC21_WORK_ID_TO_NAMESPACE_NAME[attributeName]
            )

        # Is name a grandfathered workId abbreviation?
        if attributeName in properties.MUSIC21_ABBREVIATION_TO_NAMESPACE_NAME:
            return self._getStringValueByNamespaceName(
                properties.MUSIC21_ABBREVIATION_TO_NAMESPACE_NAME[attributeName]
            )

        raise AttributeError(f'object has no attribute: {attributeName}')

    @staticmethod
    def _isStandardUniqueName(uniqueName: str) -> bool:
        '''
        Determines if a unique name is associated with a standard property.
        Returns False if no such associated standard property can be found.

        Example: a standard contributor uniqueName returns True

        >>> metadata.Metadata._isStandardUniqueName('librettist')
        True

        Example: a standard 'namespace:name' returns False (it is a standard
        namespaceName, but not a standard uniqueName)

        >>> metadata.Metadata._isStandardUniqueName('marcrel:LBT')
        False

        Example: a standard non-contributor uniqueName returns True

        >>> metadata.Metadata._isStandardUniqueName('alternativeTitle')
        True

        Example: a custom (non-standard) name returns False (it is not
        a standard name of any sort)

        >>> metadata.Metadata._isStandardUniqueName('average duration')
        False
        '''
        prop: t.Optional[PropertyDescription] = (
            properties.UNIQUE_NAME_TO_PROPERTY_DESCRIPTION.get(uniqueName, None)
        )
        if prop is None:
            return False

        return True

    @staticmethod
    def _isStandardNamespaceName(namespaceName: str) -> bool:
        '''
        Determines if a 'namespace:name' is associated with a standard property.
        Returns False if no such associated standard property can be found.

        Example: a standard 'namespace:name' returns True

        >>> metadata.Metadata._isStandardNamespaceName('marcrel:LBT')
        True

        Example: a standard contributor uniqueName returns False (it is a
        standard uniqueName, but not a standard namespaceName)

        >>> metadata.Metadata._isStandardNamespaceName('librettist')
        False

        Example: a namespaceName with a non-standard namespace returns False

        >>> metadata.Metadata._isStandardNamespaceName('nonstandardnamespace:LBT')
        False

        Example: a namespaceName with a standard namespace, but a non-standard name
        returns False

        >>> metadata.Metadata._isStandardNamespaceName('marcrel:nonstandardname')
        False

        Example: a custom (non-standard) name returns False (it is not
        a standard name of any sort)

        >>> metadata.Metadata._isStandardNamespaceName('average duration')
        False
        '''
        prop: t.Optional[PropertyDescription] = (
            properties.NAMESPACE_NAME_TO_PROPERTY_DESCRIPTION.get(namespaceName, None)
        )
        if prop is None:
            return False

        return True

    @staticmethod
    def _isContributorNamespaceName(namespaceName: str) -> bool:
        '''
        Determines if a 'namespace:name' is associated with a standard contributor
        property. Returns False if no such associated standard property can be found,
        or if the associated standard property is not a contributor property.

        Example: 'marcrel:LBT' returns True ('marcrel:LBT' is a standard contributor
        property: the librettist).

        >>> metadata.Metadata._isContributorNamespaceName('marcrel:LBT')
        True

        Example: 'dcterms:alternative' returns False (it is a standard namespaceName,
        but it is not a contributor).

        >>> metadata.Metadata._isContributorNamespaceName('dcterms:alternative')
        False

        Example: 'librettist' returns False (it is a standard contributor
        uniqueName, but not a standard contributor namespaceName)

        >>> metadata.Metadata._isContributorNamespaceName('librettist')
        False

        Example: a namespaceName with a non-standard namespace returns False

        >>> metadata.Metadata._isContributorNamespaceName('nonstandardnamespace:LBT')
        False

        Example: a namespaceName with a standard namespace, but a non-standard name
        returns False

        >>> metadata.Metadata._isContributorNamespaceName('marcrel:nonstandardname')
        False

        Example: a custom (non-standard) name returns False (it is not
        a standard name of any sort)

        >>> metadata.Metadata._isContributorNamespaceName('average duration')
        False
        '''
        prop: t.Optional[PropertyDescription] = (
            properties.NAMESPACE_NAME_TO_PROPERTY_DESCRIPTION.get(namespaceName, None)
        )
        if prop is None:
            return False

        return prop.isContributor

    @staticmethod
    def _namespaceNameNeedsArticleNormalization(namespaceName: str) -> bool:
        '''
        Determines if a 'namespace:name' is associated with a standard property that
        needs article normalization (generally title-like properties). Returns False
        if no such associated standard property can be found, or if the associated
        standard property is not a contributor property.

        Example: 'dcterms:title' returns True

        >>> metadata.Metadata._namespaceNameNeedsArticleNormalization('dcterms:title')
        True

        Example: 'title' returns False ('title' is the uniqueName of a standard property
        that needs article normalization, but it is not a namespaceName).

        >>> metadata.Metadata._namespaceNameNeedsArticleNormalization('title')
        False

        Example: 'marcrel:LBT' (the librettist) returns False (it doesn't need article
        normalization)

        >>> metadata.Metadata._namespaceNameNeedsArticleNormalization('marcrel:LBT')
        False

        Example: 'average duration' returns False (it is not a standard name)

        >>> metadata.Metadata._namespaceNameNeedsArticleNormalization('average duration')
        False
        '''
        prop: t.Optional[PropertyDescription] = (
            properties.NAMESPACE_NAME_TO_PROPERTY_DESCRIPTION.get(namespaceName, None)
        )
        if prop is None:
            return False

        return prop.needsArticleNormalization

    @staticmethod
    def _namespaceNameToContributorRole(namespaceName: str) -> t.Optional[str]:
        '''
        Translates a standard 'namespace:name' to it's associated contributor role.
        Returns None for standard non-contributors as well as for non-standard names.

        Example: 'marcrel:LBT' returns 'librettist'

        >>> metadata.Metadata._namespaceNameToContributorRole('marcrel:LBT')
        'librettist'

        Example: 'dcterms:title' returns None (not a contributor)

        >>> metadata.Metadata._namespaceNameToContributorRole('dcterms:title') is None
        True

        Example: 'librettist' returns None ('librettist' is the uniqueName of a
        standard contributor property, but it is not a namespaceName).

        >>> metadata.Metadata._namespaceNameToContributorRole('librettist') is None
        True

        Example: 'average duration' returns None (it is a non-standard name)

        >>> metadata.Metadata._namespaceNameToContributorRole('average duration') is None
        True
        '''
        prop: t.Optional[PropertyDescription] = (
            properties.NAMESPACE_NAME_TO_PROPERTY_DESCRIPTION.get(namespaceName, None)
        )
        if prop is None:
            return None
        if not prop.isContributor:
            return None

        # Return the uniqueName, which can be found one of two places in prop.
        # We must check them in this order:
        # 1. prop.uniqueName
        # 2. prop.name
        if prop.uniqueName:
            return prop.uniqueName
        return prop.name

    @staticmethod
    def _contributorRoleToNamespaceName(role: t.Optional[str]) -> str:
        '''
        Translates a contributor role to a standard 'namespace:name' that
        should be used to store that contributor.

        Example: 'composer' and 'lyricist' are standard contributor roles whose
        namespaceNames are 'marcrel:CMP' and 'marcrel:LYR', respectively

        >>> metadata.Metadata._contributorRoleToNamespaceName('composer')
        'marcrel:CMP'
        >>> metadata.Metadata._contributorRoleToNamespaceName('lyricist')
        'marcrel:LYR'

        Returns 'marcrel:CTB' (a.k.a. 'otherContributor') if the role is a
        non-standard role.  We allow role=None, because None is a valid
        non-standard contributor role.

        Example: 'interpretive dancer' is a non-standard contributor role, so
        'marcrel:CTB' is returned.

        >>> metadata.Metadata._contributorRoleToNamespaceName('interpretive dancer')
        'marcrel:CTB'

        Example: None is a non-standard contributor role, so 'marcrel:CTB' is returned.

        >>> metadata.Metadata._contributorRoleToNamespaceName(None)
        'marcrel:CTB'
        '''
        if role is None:
            return 'marcrel:CTB'

        namespaceName: t.Optional[str] = properties.UNIQUE_NAME_TO_NAMESPACE_NAME.get(role, None)
        if namespaceName is None:
            # it's a non-standard role, so add this contributor with uniqueName='otherContributor'
            return 'marcrel:CTB'  # aka. 'otherContributor'

        prop: t.Optional[PropertyDescription] = (
            properties.NAMESPACE_NAME_TO_PROPERTY_DESCRIPTION.get(namespaceName, None)
        )

        if prop is not None and not prop.isContributor:
            # It's not a contributor name, but it IS another metadata uniqueName, like
            # 'alternativeTitle' or something.  Weird, but we'll call it 'otherContributor'.
            return 'marcrel:CTB'  # a.k.a. 'otherContributor'

        return namespaceName

    def _get(self, name: str, isCustom: bool) -> t.Tuple[ValueType, ...]:
        '''
        Returns all the items stored in metadata with this name.
        The returned value is always a Tuple. If there are no items, an empty
        Tuple is returned.

        If isCustom is True, then the name will be used unconditionally as a custom name.

        If isCustom is False, and the name is not a standard uniqueName or a standard
        'namespace:name', KeyError will be raised.
        '''
        if not isCustom:
            namespaceName: str = name
            if self._isStandardUniqueName(name):
                namespaceName = properties.UNIQUE_NAME_TO_NAMESPACE_NAME.get(name, '')
            if not self._isStandardNamespaceName(namespaceName):
                raise KeyError(
                    f'Name=\'{name}\' is not a standard metadata name.'
                    ' Call addCustom/setCustom/getCustom for custom names.')
            name = namespaceName

        valueList: t.Optional[t.List[ValueType]] = self._contents.get(name, None)

        if not valueList:
            # return empty tuple
            return tuple()

        # return a tuple containing contents of list
        return tuple(valueList)

    def _add(self, name: str, value: t.Union[t.Any, t.Iterable[t.Any]], isCustom: bool):
        '''
        Adds a single item or multiple items with this name, leaving any existing
        items with this name in place.

        If isCustom is True, then the name will be used unconditionally as a custom name.

        If isCustom is False, and the name is not a standard uniqueName or a standard
        'namespace:name', KeyError will be raised.
        '''
        if not isCustom:
            namespaceName: str = name
            if self._isStandardUniqueName(name):
                namespaceName = properties.UNIQUE_NAME_TO_NAMESPACE_NAME.get(name, '')
            if not self._isStandardNamespaceName(namespaceName):
                raise KeyError(
                    f'Name=\'{name}\' is not a standard metadata name.'
                    ' Call addCustom/setCustom/getCustom for custom names.')
            name = namespaceName

        if not isinstance(value, t.Iterable):
            value = [value]

        if isinstance(value, str):
            # special case: str is iterable, but we don't want to iterate over it.
            value = [value]

        convertedValues: t.List[ValueType] = []
        for v in value:
            convertedValues.append(self._convertValue(name, v))

        prevValues: t.Optional[t.List[ValueType]] = self._contents.get(name, None)
        if not prevValues:  # None or []
            # set the convertedValues list in there
            # it's always a list, even if there's only one value
            self._contents[name] = convertedValues
        else:
            # add the convertedValues list to the existing list
            self._contents[name] = prevValues + convertedValues

    def _set(self, name: str, value: t.Union[t.Any, t.Iterable[t.Any]], isCustom: bool):
        '''
        Sets a single item or multiple items with this name, replacing any
        existing items with this name.  If isCustom is False, the name must
        be a standard uniqueName or a standard 'namespace:name'.  If isCustom
        is True, the name can be any custom name.

        >>> md = metadata.Metadata()

        Example: set the librettist

        >>> md._set('librettist', metadata.Text('Marie Červinková-Riegrová'), isCustom=False)
        >>> md['librettist']
        (<music21.metadata.primitives.Contributor librettist:Marie Červinková-Riegrová>,)

        Example: replace that librettist with two other librettists

        >>> md._set('librettist', ['Melissa Li', 'Kit Yan Win'], isCustom=False)
        >>> md['marcrel:LBT']
        (<music21.metadata.primitives.Contributor librettist:Melissa Li>,
         <music21.metadata.primitives.Contributor librettist:Kit Yan Win>)

        If isCustom is True, then the name will be used unconditionally as a custom name.

        >>> md._set('average duration', '180 minutes', isCustom=True)
        >>> md._get('average duration', isCustom=True)
        (<music21.metadata.primitives.Text 180 minutes>,)

        If isCustom is False, and the name is not a standard uniqueName or a standard
        'namespace:name', KeyError will be raised.

        >>> md._set('average duration', '180 minutes', isCustom=False)
        Traceback (most recent call last):
        KeyError: "Name='average duration' is not a standard metadata name...
        '''
        if not isCustom:
            namespaceName: str = name
            if self._isStandardUniqueName(name):
                namespaceName = properties.UNIQUE_NAME_TO_NAMESPACE_NAME.get(name, '')
            if not self._isStandardNamespaceName(namespaceName):
                raise KeyError(
                    f'Name=\'{name}\' is not a standard metadata name.'
                    ' Call addCustom/setCustom/getCustom for custom names.')
            name = namespaceName

        self._contents.pop(name, None)
        self._add(name, value, isCustom)

    @staticmethod
    def _convertValue(namespaceName: str, value: t.Any) -> ValueType:
        '''
        Converts a value to the appropriate valueType (looked up in STDPROPERTIES by
        namespaceName).

        Converts certain named values to Text

        >>> metadata.Metadata._convertValue('dcterms:title', 3.4)
        <music21.metadata.primitives.Text 3.4>
        >>> metadata.Metadata._convertValue('dcterms:title', '3.4')
        <music21.metadata.primitives.Text 3.4>
        >>> metadata.Metadata._convertValue('dcterms:title', metadata.Text('3.4'))
        <music21.metadata.primitives.Text 3.4>

        Converts certain named values to Copyright

        >>> metadata.Metadata._convertValue('dcterms:rights', 'copyright str')
        <music21.metadata.primitives.Copyright copyright str>
        >>> metadata.Metadata._convertValue('dcterms:rights', metadata.Text('copyright text'))
        <music21.metadata.primitives.Copyright copyright text>
        >>> metadata.Metadata._convertValue('dcterms:rights', metadata.Copyright('copyright'))
        <music21.metadata.primitives.Copyright copyright>

        Converts certain named values to Contributor

        >>> metadata.Metadata._convertValue('marcrel:CMP', 'composer str')
        <music21.metadata.primitives.Contributor composer:composer str>
        >>> metadata.Metadata._convertValue('marcrel:CMP', metadata.Text('composer text'))
        <music21.metadata.primitives.Contributor composer:composer text>
        >>> metadata.Metadata._convertValue('marcrel:CMP',
        ...     metadata.Contributor(role='random', name='Joe'))
        <music21.metadata.primitives.Contributor random:Joe>

        Converts certain named values to DateSingle

        >>> metadata.Metadata._convertValue('dcterms:created', '1938')
        <music21.metadata.primitives.DateSingle 1938/--/-->
        >>> metadata.Metadata._convertValue('dcterms:created', metadata.Text('1938'))
        <music21.metadata.primitives.DateSingle 1938/--/-->
        >>> metadata.Metadata._convertValue('dcterms:created',
        ...     metadata.DateBetween(['1938','1939']))
        <music21.metadata.primitives.DateBetween 1938/--/-- to 1939/--/-->
        '''
        valueType: t.Optional[t.Type[ValueType]] = properties.NAMESPACE_NAME_TO_VALUE_TYPE.get(
            namespaceName, None
        )
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

                # noinspection PyBroadException
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
                return Contributor(
                    role=Metadata._namespaceNameToContributorRole(namespaceName),
                    name=value
                )
            raise exceptions21.MetadataException(
                f'invalid type for Contributor: {type(value).__name__}')

        raise exceptions21.MetadataException('internal error: invalid valueType')

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

    RichMetadata's allUniqueNames/searchAttributes contain all the Metadata
    allUniqueNames/searchAttributes, plus some observed musical information
    analyzed from the score.  Here is a list of what information is added:

    >>> richMetadata.additionalRichSearchAttributes
    ('ambitus', 'keySignatureFirst', 'keySignatures', 'noteCount', 'numberOfParts',
     'pitchHighest', 'pitchLowest', 'quarterLength', 'sourcePath', 'tempoFirst',
     'tempos', 'timeSignatureFirst', 'timeSignatures')
    '''

    # CLASS VARIABLES #

    # When changing this, be sure to update freezeThaw.py
    additionalRichSearchAttributes = (
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

    allUniqueNames = tuple(sorted(Metadata.allUniqueNames + additionalRichSearchAttributes))
    searchAttributes = tuple(sorted(Metadata.searchAttributes + additionalRichSearchAttributes))

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

    def _getPluralAttribute(self, attributeName) -> t.Tuple[str, ...]:
        # we have to implement this to add the RichMetadata searchAttributes, since
        # Metadata.search calls it.
        if attributeName in self.additionalRichSearchAttributes:
            # We can treat additionalRichSearchAttributes as singletons,
            # so just call getattr, and put the result in a tuple.
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
            '_contents',
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
