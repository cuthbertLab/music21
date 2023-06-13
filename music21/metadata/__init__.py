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
from __future__ import annotations

__all__ = [
    'Metadata',
    'RichMetadata',
    'AmbitusShort',
]

from collections import namedtuple
from collections.abc import Iterable
import copy
from dataclasses import dataclass
import datetime
import pathlib
import re
import typing as t
from typing import overload
import unittest

from music21 import base
from music21 import common
from music21.common import deprecated
from music21 import defaults
from music21 import environment
from music21 import exceptions21

from music21.metadata import properties
from music21.metadata.properties import PropertyDescription
from music21.metadata import bundles
from music21.metadata import caching
from music21.metadata import primitives
from music21.metadata.primitives import (Date, DatePrimitive,
                                         DateSingle, DateRelative, DateBetween,
                                         DateSelection, Text, Contributor, Creator,
                                         Imprint, Copyright, ValueType)
# -----------------------------------------------------------------------------
environLocal = environment.Environment('metadata')

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

    Here is the list of grandfathered v7 synonyms, which may disappear in a
    future version:

    >>> sorted(metadata.properties.ALL_MUSIC21_WORK_IDS)
    ['commission', 'date', 'dedication', 'volume']

    And here are their new v8 standard unique names:

    >>> sorted(metadata.properties.MUSIC21_WORK_ID_TO_UNIQUE_NAME.values())
    ['commissionedBy', 'dateCreated', 'dedicatedTo', 'volumeNumber']
    '''

    # CLASS VARIABLES #

    classSortOrder = -30

    # INITIALIZER #

    def __init__(self, **keywords) -> None:
        m21BaseKeywords: dict[str, t.Any] = {}
        myKeywords: dict[str, t.Any] = {}

        # We allow the setting of metadata values (attribute-style) via **keywords.
        # Any keywords that are uniqueNames, grandfathered workIds, or grandfathered
        # workId abbreviations can be set this way.
        for attr, value in keywords.items():
            if attr in properties.ALL_LEGAL_ATTRIBUTES:
                myKeywords[attr] = value
            else:
                m21BaseKeywords[attr] = value

        super().__init__(**m21BaseKeywords)
        self._contents: dict[str, list[ValueType]] = {}

        for attr, value in myKeywords.items():
            setattr(self, attr, value)

        self['software'] = [defaults.software]
        # TODO: check pickling, etc.

# -----------------------------------------------------------------------------
# Public APIs

    def add(self,
            name: str,
            value: t.Any | Iterable[t.Any],
            ) -> None:
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

    def getCustom(self, name: str) -> tuple[ValueType, ...]:
        '''
        Gets any custom-named metadata items. The name can be free-form,
        or it can be a custom 'namespace:name'.

        getCustom always returns tuple[Text, ...], which may be empty.

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

    def addCustom(self, name: str, value: t.Any | Iterable[t.Any]):
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

    def setCustom(self, name: str, value: t.Any | Iterable[t.Any]):
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

# -----------------------------------------------------------------------------
#   A few utility routines for clients calling public APIs

    @staticmethod
    def uniqueNameToNamespaceName(uniqueName: str) -> str | None:
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
    def namespaceNameToUniqueName(namespaceName: str) -> str | None:
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
    def isContributorUniqueName(uniqueName: str | None) -> bool:
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
        prop: PropertyDescription | None = (
            properties.UNIQUE_NAME_TO_PROPERTY_DESCRIPTION.get(uniqueName, None)
        )
        if prop is None:
            return False

        return prop.isContributor

    def isStandardName(self, name: str) -> bool:
        '''
        Determines if name is either a 'namespace:name' or a 'uniqueName'
        associated with a standard property.

        Returns False if no such associated standard property can be found.

        >>> md = metadata.Metadata()
        >>> md.isStandardName('librettist')
        True

        'marcrel:LBT' is the namespace name of 'librettist'

        >>> md.isStandardName('marcrel:LBT')
        True

        Some examples of non-standard (custom) names.

        >>> md.isStandardName('average duration')
        False
        >>> md.isStandardName('soundtracker:SampleName')
        False
        '''
        if self._isStandardNamespaceName(name):
            return True

        if self._isStandardUniqueName(name):
            return True

        return False

# -----------------------------------------------------------------------------
#   Public APIs

    @property
    def software(self) -> tuple[str, ...]:
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

        Note that `.software` is an exception to the general rule that
        singular looking properties return a string.  In fact, it is always
        plural and returns a tuple of strings.  There is no singular version
        '''
        return self._getPluralAttribute('software')

    @property
    def contributors(self) -> tuple[Contributor, ...]:
        '''
        Returns a tuple of all the Contributors found in the metadata.
        Returns an empty tuple if no Contributors exist.

        >>> md = metadata.Metadata()
        >>> md.composer = 'Richard Strauss'
        >>> md.librettist = 'Oscar Wilde'

        When we add something that is not a person, such as a title
        (whether through `.attribute` setting, `[item]` setting,
        or the :meth:`~music21.metadata.Metadata.add` method), it will not show up
        in the list of contributors.

        >>> md.add('title', 'Salome')
        >>> contribs = md.contributors
        >>> contribs
        (<music21.metadata.primitives.Contributor composer:Richard Strauss>,
         <music21.metadata.primitives.Contributor librettist:Oscar Wilde>)

        Note that `.contributors` cannot be set.  Add them separately via
        specific setters or the `.addContributor()` method.
        '''
        output: list[Contributor] = []
        for _, contrib in self.all(
                skipNonContributors=True,  # we only want the contributors
                returnPrimitives=True,     # we want Contributor values
                returnSorted=False):
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

    @copyright.setter
    def copyright(self, value: str) -> None:
        '''
        For type checking only. Does not run.
        '''
        setattr(self, 'copyright', value)

    # SPECIAL METHODS #
    def all(
            self,
            *,
            skipContributors: bool = False,
            skipNonContributors: bool = False,
            returnPrimitives: bool = False,
            returnSorted: bool = True
    ) -> tuple[tuple[str, t.Any], ...]:
        # noinspection SpellCheckingInspection,PyShadowingNames
        '''
        Returns the values stored in this metadata as a Tuple of (uniqueName, value) pairs.
        There are four bool options. The three that are new in v8 (skipNonContributors,
        returnPrimitives, returnSorted) are defaulted to behave like v7.

        If skipContributors is True, only non-contributor metadata will be returned.  If
        skipNonContributors is True, only contributor metadata will be returned.  If both
        of these are True, the returned Tuple will be empty. If returnPrimitives is False
        (default), values are all converted to str.  If returnPrimitives is True, the values
        will retain their original ValueType (e.g. Text, Contributor, Copyright, etc).  If
        returnSorted is False, the returned Tuple will not be sorted by uniqueName (the
        default behavior is to sort).

        Note that we cannot properly type-hint the return value, since derived classes (such
        as RichMetadata) are allowed to return their own typed values that might not be str
        or ValueType.

        >>> c = corpus.parse('corelli/opus3no1/1grave')
        >>> c.metadata.all()
        (('arranger', 'Michael Scott Cuthbert'),
         ('composer', 'Arcangelo Corelli'),
         ('copyright', '© 2014, Creative Commons License (CC-BY)'),
         ('corpusFilePath', 'corelli/opus3no1/1grave.xml'),
         ('fileFormat', 'musicxml'),
         ('filePath', '...corpus/corelli/opus3no1/1grave.xml'),
         ('movementName', 'Sonata da Chiesa, No. I (opus 3, no. 1)'),
         ('software', 'Dolet...'),
         ('software', 'Finale...'),
         ('software', 'music21 v...'))

        >>> c.metadata.date = metadata.DateRelative('1689', 'onOrBefore')
        >>> c.metadata.localeOfComposition = 'Rome'
        >>> c.metadata.all(skipContributors=True)
        (('copyright', '© 2014, Creative Commons License (CC-BY)'),
         ('corpusFilePath', 'corelli/opus3no1/1grave.xml'),
         ('dateCreated', '1689/--/-- or earlier'),
         ('fileFormat', 'musicxml'),
         ('filePath', '...corpus/corelli/opus3no1/1grave.xml'),
         ('localeOfComposition', 'Rome'),
         ('movementName', 'Sonata da Chiesa, No. I (opus 3, no. 1)'),
         ('software', 'Dolet...'),
         ('software', 'Finale...'),
         ('software', 'music21 v...'))

        >>> c.metadata.all(returnPrimitives=True, returnSorted=False)
        (('software', <music21.metadata.primitives.Text music21 v...>),
         ('software', <music21.metadata.primitives.Text Finale ...>),
         ('software', <music21.metadata.primitives.Text Dolet Light...>),
         ('movementName', <...Text Sonata da Chiesa, No. I (opus 3, no. 1)>),
         ('composer', <music21.metadata.primitives.Contributor composer:Arcangelo Corelli>),
         ...
         ('dateCreated', <music21.metadata.primitives.DateRelative 1689/--/-- or earlier>),
         ('localeOfComposition', <music21.metadata.primitives.Text Rome>))

        >>> c.metadata.all(skipNonContributors=True, returnPrimitives=True, returnSorted=True)
        (('arranger', <music21.metadata.primitives.Contributor arranger:Michael Scott Cuthbert>),
         ('composer', <music21.metadata.primitives.Contributor composer:Arcangelo Corelli>))
        '''
        allOut: list[tuple[str, t.Any]] = []

        valueList: list[ValueType]
        for uniqueName, valueList in self._contents.items():
            isContributor: bool = self._isContributorUniqueName(uniqueName)
            if skipContributors and isContributor:
                continue
            if skipNonContributors and not isContributor:
                continue

            value: ValueType
            for value in valueList:
                if returnPrimitives:
                    allOut.append((uniqueName, value))
                else:
                    allOut.append((uniqueName, str(value)))

        if returnSorted:
            return tuple(sorted(allOut))
        return tuple(allOut)

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
        # so all property.setters are just to help type checkers,
        # and are handled explicitly here.

        if name in properties.ALL_SINGLE_ATTRIBUTE_NAMES:
            if (value is not None
                    and isinstance(value, Iterable)
                    and not isinstance(value, str)):
                raise ValueError(f'md.{name} can only be set to a single value; '
                                 f'set md[{name}] to multiple values instead.')

        if name in properties.ALL_PLURAL_ATTRIBUTE_NAMES:
            if not isinstance(value, Iterable) or isinstance(value, str):
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

        # OK, we've covered everything we know about; fall back to setting
        # bare attributes (including the ones in base classes).
        super().__setattr__(name, value)


    @overload
    def __getitem__(self,
                    key: t.Literal[
                        'movementName',
                        'movementNumber',
                        'title',
                    ]) -> tuple[Text, ...]:
        pass

    @overload
    def __getitem__(self,
                    key: t.Literal[
                        'copyright',
                    ]) -> tuple[Copyright, ...]:
        pass

    @overload
    def __getitem__(self, key: str) -> tuple[Text, ...]:
        pass

    def __getitem__(self, key: str) -> tuple[ValueType, ...] | tuple[Text, ...]:
        '''
        "Dictionary key" access for all standard uniqueNames and
        standard keys of the form 'namespace:name'.

        These always return tuple[ValueType, ...], which may be empty.

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

    def __setitem__(self, key: str, value: t.Any | Iterable[t.Any]):
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

    def addContributor(self, c: Contributor):
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
        uniqueName: str = self._contributorRoleToUniqueName(c.role)
        self._add(uniqueName, c, isCustom=False)

    def getContributorsByRole(self, role: str | None) -> tuple[Contributor, ...]:
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
        result: list[Contributor] = []  # there may be more than one per role
        for _, contrib in self.all(
                skipNonContributors=True,  # we only want the contributors
                returnPrimitives=True,     # we want Contributor values
                returnSorted=False):
            if contrib.role == role:
                result.append(contrib)
        return tuple(result)

    def search(
        self,
        query: str | t.Pattern | t.Callable[[str], bool] | None = None,
        field: str | None = None,
        **keywords
    ) -> tuple[bool, str | None]:
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


        * New in v4: use a keyword argument to search
          that field directly:

        >>> md.search(composer='Joplin')
        (True, 'composer')
        '''
        # TODO: Change to a namedtuple and add as a third element
        #    during a successful search, the full value of the retrieved
        #    field (so that 'Joplin' would return 'Joplin, Scott')
        reQuery: t.Pattern | None = None
        valueFieldPairs = []
        if query is None and field is None and not keywords:
            return (False, None)
        elif query is None and field is None and keywords:
            field, query = keywords.popitem()

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
                for uniqueName, value in self.all(skipContributors=True):
                    if not self._isStandardUniqueName(uniqueName):
                        # custom metadata, don't search it
                        continue

                    # environLocal.printDebug(['comparing fields:', f, field])
                    # look for partial match in all fields
                    if field.lower() in uniqueName.lower():
                        valueFieldPairs.append((value, uniqueName))
                        match = True
                        break

                    # see if there is an associated grandfathered workId, and if so,
                    # search for that, too.
                    workId: str | None = properties.UNIQUE_NAME_TO_MUSIC21_WORK_ID.get(
                        uniqueName, None
                    )

                    if not workId:
                        # there is no associated grandfathered workId, don't search it
                        continue

                    # look for partial match in all fields
                    if field.lower() in workId.lower():
                        valueFieldPairs.append((value, workId))
                        match = True
                        break
        else:  # get all fields
            for uniqueName, value in self.all(skipContributors=True):
                if not self._isStandardUniqueName(uniqueName):
                    # custom metadata, don't search it
                    continue
                valueFieldPairs.append((value, uniqueName))

        # now get all (or field-matched) contributor names, using contrib.role
        # as field name, so clients can search by custom contributor role.
        for _, contrib in self.all(
                skipNonContributors=True,  # we only want the contributors
                returnPrimitives=True,     # we want Contributor values
                returnSorted=False):
            if field is not None:
                if contrib.role is None and field.lower() != 'contributor':
                    continue
                if contrib.role is not None and field.lower() not in contrib.role.lower():
                    continue
            for name in contrib.names:
                # name is Text, so convert to str
                valueFieldPairs.append((str(name), contrib.role))

        # for now, make all queries strings
        # ultimately, can look for regular expressions by checking for
        # .search
        useRegex = False
        if isinstance(query, t.Pattern):
            useRegex = True
            reQuery = query  # already compiled
        # look for regex characters
        elif (isinstance(query, str)
              and any(character in query for character in '*.|+?{}')):
            useRegex = True
            reQuery = re.compile(query, flags=re.IGNORECASE)

        if useRegex and reQuery is not None:
            for value, innerField in valueFieldPairs:
                # "re.IGNORECASE" makes case-insensitive search
                if isinstance(value, str):
                    matchReSearch = reQuery.search(value)
                    if matchReSearch is not None:
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


    # # No longer used.
    # workIdAbbreviationDict = {
    #     'gaw': 'associatedWork',
    #     'gco': 'collectionDesignation',
    #     'gtl': 'groupTitle',
    #     'oac': 'actNumber',
    #     'oco': 'commission',
    #     'ocy': 'countryOfComposition',
    #     'ode': 'dedication',
    #     'omd': 'movementName',
    #     'omv': 'movementNumber',
    #     'onm': 'number',
    #     'opc': 'localeOfComposition',  # origin in abc
    #     'opr': 'parentTitle',
    #     'ops': 'opusNumber',
    #     'osc': 'sceneNumber',
    #     'ota': 'alternativeTitle',
    #     'otl': 'title',
    #     'otp': 'popularTitle',
    #     'ovm': 'volume',
    #     'txl': 'textLanguage',
    #     'txo': 'textOriginalLanguage',
    # }

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

    @alternativeTitle.setter
    def alternativeTitle(self, value: str) -> None:
        '''
        For type checking only. Does not run.
        '''
        setattr(self, 'alternativeTitle', value)

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

    @composer.setter
    def composer(self, value: str) -> None:
        '''
        For type checking only. Does not run.
        '''
        setattr(self, 'composer', value)

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

    @composers.setter
    def composers(self, value: Iterable[str]) -> None:
        '''
        For type checking only. Does not run.
        '''
        setattr(self, 'composers', value)

    @property
    def date(self):
        '''
        The `.date` property is deprecated in v8 and will be removed in v10.
        Use `dateCreated` instead.
        '''
        return self.dateCreated

    @date.setter
    def date(self, value: str) -> None:
        '''
        For type checking only. Does not run.
        '''
        setattr(self, 'date', value)

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

    @dateCreated.setter
    def dateCreated(self, value: str) -> None:
        '''
        For type checking only. Does not run.
        '''
        setattr(self, 'dateCreated', value)

    @property
    def fileFormat(self) -> str | None:
        '''
        Get or set the file format that was parsed.
        '''
        return self._getSingularAttribute('fileFormat')

    @fileFormat.setter
    def fileFormat(self, value: str) -> None:
        '''
        For type checking only. Does not run.
        '''
        setattr(self, 'fileFormat', value)

    @property
    def filePath(self) -> str | None:
        '''
        Get or set the file path that was parsed.
        '''
        return self._getSingularAttribute('filePath')

    @filePath.setter
    def filePath(self, value: str) -> None:
        '''
        For type checking only. Does not run.
        '''
        setattr(self, 'filePath', value)

    @property
    def corpusFilePath(self) -> str | None:
        '''
        Get or set the path within the corpus that was parsed.
        '''
        return self._getSingularAttribute('corpusFilePath')

    @corpusFilePath.setter
    def corpusFilePath(self, value: str) -> None:
        '''
        For type checking only. Does not run.
        '''
        setattr(self, 'corpusFilePath', value)

    @property
    def fileNumber(self) -> str | None:
        '''
        Get or set the file number that was parsed.
        '''
        return self._getSingularAttribute('fileNumber')

    @fileNumber.setter
    def fileNumber(self, value: str) -> None:
        '''
        For type checking only. Does not run.
        '''
        setattr(self, 'fileNumber', value)

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

    @localeOfComposition.setter
    def localeOfComposition(self, value: str) -> None:
        '''
        For type checking only. Does not run.
        '''
        setattr(self, 'localeOfComposition', value)

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

    @librettist.setter
    def librettist(self, value: str) -> None:
        '''
        For type checking only. Does not run.
        '''
        setattr(self, 'librettist', value)

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

    @librettists.setter
    def librettists(self, value: Iterable[str]) -> None:
        '''
        For type checking only. Does not run.
        '''
        setattr(self, 'librettists', value)

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

    @lyricist.setter
    def lyricist(self, value: str) -> None:
        '''
        For type checking only. Does not run.
        '''
        setattr(self, 'lyricist', value)

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

    @lyricists.setter
    def lyricists(self, value: Iterable[str]) -> None:
        '''
        For type checking only. Does not run.
        '''
        setattr(self, 'lyricists', value)

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

    @movementName.setter
    def movementName(self, value: str) -> None:
        '''
        For type checking only. Does not run.
        '''
        setattr(self, 'movementName', value)

    @property
    def movementNumber(self) -> str | None:
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

    @movementNumber.setter
    def movementNumber(self, value: str) -> None:
        '''
        For type checking only. Does not run.
        '''
        setattr(self, 'movementNumber', value)

    @property
    def number(self) -> str | None:
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

    @number.setter
    def number(self, value: str) -> None:
        '''
        For type checking only. Does not run.
        '''
        setattr(self, 'number', value)

    @property
    def opusNumber(self) -> str | None:
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

    @opusNumber.setter
    def opusNumber(self, value: str) -> None:
        '''
        For type checking only. Does not run.
        '''
        setattr(self, 'opusNumber', value)

    @property
    def title(self):
        r'''
        Get the title of the work.

        >>> md = metadata.Metadata(title='Third Symphony')
        >>> md.title
        'Third Symphony'

        >>> md = metadata.Metadata(popularTitle='Eroica')
        >>> md.title is None
        True
        '''
        return self._getSingularAttribute('title')

    @title.setter
    def title(self, value: str) -> None:
        '''
        For type checking only. Does not run.
        '''
        setattr(self, 'title', value)

    @property
    def bestTitle(self) -> str | None:
        r'''
        Get the title of the work, or the next-matched title string
        available from a related parameter fields.

        >>> md = metadata.Metadata(title='Third Symphony')
        >>> md.bestTitle
        'Third Symphony'

        >>> md = metadata.Metadata(popularTitle='Eroica')
        >>> md.bestTitle
        'Eroica'

        >>> md = metadata.Metadata(
        ...     title='Third Symphony',
        ...     popularTitle='Eroica',
        ...     )
        >>> md.bestTitle
        'Third Symphony'

        >>> md.popularTitle
        'Eroica'

        >>> md.otp
        'Eroica'

        bestTitle cannot be set:

        >>> md.bestTitle = 'Bonaparte'
        Traceback (most recent call last):
        AttributeError: ...'bestTitle'...
        '''
        # TODO: once Py3.11 is the minimum, change doctest output to:
        #    AttributeError: property 'bestTitle' of 'Metadata' object has no setter

        searchId = (
            'title',
            'popularTitle',
            'alternativeTitle',
            'movementName',
        )
        for uniqueName in searchId:
            titleSummary: str | None = self._getStringValueByNamespaceName(
                properties.UNIQUE_NAME_TO_NAMESPACE_NAME[uniqueName]
            )
            if titleSummary:
                return titleSummary  # return first matched

        return None

# -----------------------------------------------------------------------------
# Internal support routines (many of them static).

    def _getStringValueByNamespaceName(self, namespaceName: str) -> str | None:
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

        values: tuple[ValueType, ...] = self._get(namespaceName, isCustom=False)
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

    def _getStringValuesByNamespaceName(self, namespaceName: str) -> tuple[str, ...]:
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

        values: tuple[ValueType, ...] = self._get(namespaceName, isCustom=False)
        if not values:
            return tuple()

        if self._namespaceNameNeedsArticleNormalization(namespaceName):
            output: list[str] = []
            for value in values:
                assert isinstance(value, Text)
                output.append(value.getNormalizedArticle())
            return tuple(output)

        return tuple(str(value) for value in values)

    def _getPluralAttribute(self, attributeName: str) -> tuple[str, ...]:
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

        raise AttributeError(f'invalid attributeName: {attributeName}')

    def _getSingularAttribute(self, attributeName: str) -> str | None:
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
        AttributeError: 'Metadata' object has no attribute: 'humdrum:ODE'
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

        raise AttributeError(
            f'{self.__class__.__name__!r} object has no attribute: {attributeName!r}'
        )

    def _isStandardUniqueName(self, uniqueName: str) -> bool:
        '''
        Determines if a unique name is associated with a standard property.
        Returns False if no such associated standard property can be found.

        Example: a standard contributor uniqueName returns True

        >>> md = metadata.Metadata()
        >>> md._isStandardUniqueName('librettist')
        True

        Example: a standard 'namespace:name' returns False (it is a standard
        namespaceName, but not a standard uniqueName)

        >>> md._isStandardUniqueName('marcrel:LBT')
        False

        Example: a standard non-contributor uniqueName returns True

        >>> md._isStandardUniqueName('alternativeTitle')
        True

        Example: a custom (non-standard) name returns False (it is not
        a standard name of any sort)

        >>> md._isStandardUniqueName('average duration')
        False

        Example: a RichMetadata additional attribute name returns False

        >>> md._isStandardUniqueName('ambitus')
        False

        '''
        prop: PropertyDescription | None = (
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
        prop: PropertyDescription | None = (
            properties.NAMESPACE_NAME_TO_PROPERTY_DESCRIPTION.get(namespaceName, None)
        )
        if prop is None:
            return False

        return True

    @staticmethod
    def _isContributorUniqueName(uniqueName: str) -> bool:
        '''
        Determines if a uniqueName is associated with a standard contributor
        property. Returns False if no such associated standard property can be found,
        or if the associated standard property is not a contributor property.

        Example: 'librettist' returns True ('librettist' is a standard contributor
        property).

        >>> metadata.Metadata._isContributorUniqueName('librettist')
        True

        Example: 'alternativeTitle' returns False (it is a standard namespaceName,
        but it is not a contributor).

        >>> metadata.Metadata._isContributorUniqueName('alternativeTitle')
        False

        Example: 'marcrel:LBT' returns False (it is a standard contributor
        namespaceName, but not a standard contributor uniqueName)

        >>> metadata.Metadata._isContributorUniqueName('marcrel:LBT')
        False

        Example: a custom (non-standard) name returns False (it is not
        a standard name of any sort)

        >>> metadata.Metadata._isContributorUniqueName('average duration')
        False
        '''
        prop: PropertyDescription | None = (
            properties.UNIQUE_NAME_TO_PROPERTY_DESCRIPTION.get(uniqueName, None)
        )
        if prop is None:
            return False

        return prop.isContributor

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
        prop: PropertyDescription | None = (
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
        prop: PropertyDescription | None = (
            properties.NAMESPACE_NAME_TO_PROPERTY_DESCRIPTION.get(namespaceName, None)
        )
        if prop is None:
            return False

        return prop.needsArticleNormalization

    @staticmethod
    def _contributorRoleToUniqueName(role: str | None) -> str:
        '''
        Translates a contributor role to a standard uniqueName that
        should be used to store that contributor.  For standard contributor
        roles, this simply returns role, because standard roles are their
        own standard uniqueNames. But for non-standard roles, 'otherContributor'
        is returned. This is the standard uniqueName that should be used for
        contributors with custom roles.

        Example: 'composer' and 'lyricist' are standard contributor roles whose
        uniqueNames are 'composer' and 'lyricist', respectively.

        >>> metadata.Metadata._contributorRoleToUniqueName('composer')
        'composer'
        >>> metadata.Metadata._contributorRoleToUniqueName('lyricist')
        'lyricist'

        Example: 'interpretive dancer' is a non-standard contributor role, so
        'otherContributor' is returned.

        >>> metadata.Metadata._contributorRoleToUniqueName('interpretive dancer')
        'otherContributor'

        Example: None is a non-standard contributor role, so 'otherContributor' is returned.

        >>> metadata.Metadata._contributorRoleToUniqueName(None)
        'otherContributor'
        '''
        if role is None:
            return 'otherContributor'

        prop: PropertyDescription | None = (
            properties.UNIQUE_NAME_TO_PROPERTY_DESCRIPTION.get(role, None)
        )

        if prop is None:
            # It's not a standard uniqueName
            return 'otherContributor'

        if not prop.isContributor:
            # It's not a standard contributor role
            return 'otherContributor'

        return role

    def _get(self, name: str, isCustom: bool) -> tuple[ValueType, ...]:
        '''
        Returns all the items stored in metadata with this name.
        The returned value is always a Tuple. If there are no items, an empty
        Tuple is returned.

        If isCustom is True, then the name will be used unconditionally as a custom name.

        If isCustom is False, and the name is not a standard uniqueName or a standard
        'namespace:name', KeyError will be raised.
        '''
        if not isCustom:
            uniqueName: str = name
            if self._isStandardNamespaceName(name):
                uniqueName = properties.NAMESPACE_NAME_TO_UNIQUE_NAME.get(name, '')
            if not self._isStandardUniqueName(uniqueName):
                raise KeyError(
                    f'Name={name!r} is not a standard metadata name.'
                    ' Call addCustom/setCustom/getCustom for custom names.')
            name = uniqueName

        valueList: list[ValueType] | None = self._contents.get(name, None)

        if not valueList:
            # return empty tuple
            return tuple()

        # return a tuple containing contents of list
        return tuple(valueList)

    def _add(self, name: str, value: t.Any | Iterable[t.Any], isCustom: bool):
        '''
        Adds a single item or multiple items with this name, leaving any existing
        items with this name in place.

        If isCustom is True, then the name will be used unconditionally as a custom name.

        If isCustom is False, and the name is not a standard uniqueName or a standard
        'namespace:name', KeyError will be raised.
        '''
        if not isCustom:
            uniqueName: str = name
            if self._isStandardNamespaceName(name):
                uniqueName = properties.NAMESPACE_NAME_TO_UNIQUE_NAME.get(name, '')
            if not self._isStandardUniqueName(uniqueName):
                raise KeyError(
                    f'Name={name!r} is not a standard metadata name.'
                    ' Call addCustom/setCustom/getCustom for custom names.')
            name = uniqueName

        if not isinstance(value, Iterable):
            value = [value]

        if isinstance(value, str):
            # special case: str is iterable, but we don't want to iterate over it.
            value = [value]

        convertedValues: list[ValueType] = []
        for v in value:
            convertedValues.append(self._convertValue(name, v))

        prevValues: list[ValueType] | None = self._contents.get(name, None)
        if not prevValues:  # None or []
            # set the convertedValues list in there
            # it's always a list, even if there's only one value
            self._contents[name] = convertedValues
        else:
            # add the convertedValues list to the existing list
            self._contents[name] = prevValues + convertedValues

    def _set(self, name: str, value: t.Any | Iterable[t.Any], isCustom: bool):
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
            uniqueName: str = name
            if self._isStandardNamespaceName(name):
                uniqueName = properties.NAMESPACE_NAME_TO_UNIQUE_NAME.get(name, '')
            if not self._isStandardUniqueName(uniqueName):
                raise KeyError(
                    f'Name={name!r} is not a standard metadata name.'
                    ' Call addCustom/setCustom/getCustom for custom names.')
            name = uniqueName

        self._contents.pop(name, None)
        if value is not None:
            self._add(name, value, isCustom)

    @staticmethod
    def _convertValue(uniqueName: str, value: t.Any) -> ValueType:
        '''
        Converts a value to the appropriate valueType (looked up in STDPROPERTIES by
        uniqueName).

        Converts certain named values to Text

        >>> metadata.Metadata._convertValue('title', 3.4)
        <music21.metadata.primitives.Text 3.4>
        >>> metadata.Metadata._convertValue('title', '3.4')
        <music21.metadata.primitives.Text 3.4>
        >>> metadata.Metadata._convertValue('title', metadata.Text('3.4'))
        <music21.metadata.primitives.Text 3.4>

        Converts certain named values to Copyright

        >>> metadata.Metadata._convertValue('copyright', 'copyright str')
        <music21.metadata.primitives.Copyright copyright str>
        >>> metadata.Metadata._convertValue('copyright', metadata.Text('copyright text'))
        <music21.metadata.primitives.Copyright copyright text>
        >>> metadata.Metadata._convertValue('copyright', metadata.Copyright('copyright'))
        <music21.metadata.primitives.Copyright copyright>

        Converts certain named values to Contributor

        >>> metadata.Metadata._convertValue('composer', 'composer str')
        <music21.metadata.primitives.Contributor composer:composer str>
        >>> metadata.Metadata._convertValue('composer', metadata.Text('composer text'))
        <music21.metadata.primitives.Contributor composer:composer text>
        >>> metadata.Metadata._convertValue('composer',
        ...     metadata.Contributor(role='random', name='Joe'))
        <music21.metadata.primitives.Contributor random:Joe>

        Converts certain named values to DateSingle

        >>> metadata.Metadata._convertValue('dateCreated', '1938')
        <music21.metadata.primitives.DateSingle 1938/--/-->
        >>> metadata.Metadata._convertValue('dateCreated', metadata.Text('1938'))
        <music21.metadata.primitives.DateSingle 1938/--/-->
        >>> metadata.Metadata._convertValue('dateCreated',
        ...     metadata.DateBetween(['1938','1939']))
        <music21.metadata.primitives.DateBetween 1938/--/-- to 1939/--/-->
        '''
        valueType: type[ValueType] | None = properties.UNIQUE_NAME_TO_VALUE_TYPE.get(
            uniqueName, None
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

        if valueType is DatePrimitive:
            # note -- this may return something other than DateSingle depending
            #    on the context.
            if isinstance(value, Text):
                value = str(value)

            if isinstance(value, DatePrimitive):
                # If you want other DateSingle-derived types (DateRelative,
                # DateBetween, or DateSelection), you have to create those
                # yourself before adding/setting them.
                return value

            if isinstance(value, (str, datetime.datetime, Date)):
                # noinspection PyBroadException
                # pylint: disable=bare-except
                try:
                    return DateSingle(value)
                except:
                    # Couldn't convert; just return a generic text.
                    return Text(str(originalValue))
                # pylint: enable=bare-except

            raise exceptions21.MetadataException(
                f'invalid type for DateSingle: {type(value).__name__}')

        if valueType is Contributor:
            if isinstance(value, str):
                value = Text(value)

            if isinstance(value, Text):
                return Contributor(role=uniqueName, name=value)

            raise exceptions21.MetadataException(
                f'invalid type for Contributor: {type(value).__name__}')

        if valueType is int:
            # noinspection PyBroadException
            # pylint: disable=bare-except
            try:
                return int(value)
            except:
                raise exceptions21.MetadataException(
                    f'invalid type for int: {type(value).__name__}')
            # pylint: enable=bare-except

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
    >>> 'keySignatureFirst' in richMetadata.additionalRichMetadataAttributes
    True

    RichMetadata objects contain all the usual Metadata items, plus some observed
    musical information analyzed from the score.  Here is a list of what information
    is added:

    >>> richMetadata.additionalRichMetadataAttributes
    ('ambitus', 'keySignatureFirst', 'keySignatures', 'noteCount', 'numberOfParts',
     'pitchHighest', 'pitchLowest', 'quarterLength', 'sourcePath', 'tempoFirst',
     'tempos', 'timeSignatureFirst', 'timeSignatures')
    '''

    # CLASS VARIABLES #

    # When changing this, be sure to update freezeThaw.py
    additionalRichMetadataAttributes = (
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

    # INITIALIZER #

    def __init__(self, **keywords):
        super().__init__(**keywords)
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

    def _getPluralAttribute(self, attributeName) -> tuple[str, ...]:
        # we have to implement this to add the RichMetadata attributes, since
        # Metadata.search calls it.
        if attributeName in self.additionalRichMetadataAttributes:
            # We can treat additionalRichMetadataAttributes as singletons,
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

    def getSourcePath(self, streamObj) -> str:
        '''
        Get a string of the path after the corpus for the piece...useful for
        searching on corpus items without proper composer data...

        >>> rmd = metadata.RichMetadata()
        >>> b = corpus.parse('bwv66.6')
        >>> rmd.getSourcePath(b)
        'bach/bwv66.6.mxl'
        '''
        if not streamObj.metadata:
            return ''

        md = streamObj.metadata

        if md.corpusFilePath:
            return md.corpusFilePath

        streamFp = md.filePath
        if not streamFp:
            return ''

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

    def all(
            self,
            *,
            skipContributors: bool = False,
            skipNonContributors: bool = False,
            returnPrimitives: bool = False,
            returnSorted: bool = True
    ) -> tuple[tuple[str, t.Any], ...]:
        '''
        Returns all values stored in this RichMetadata as a Tuple of Tuples.
        Each individual Metadata Tuple is (uniqueName, value) and each additional
        RichMetadata tuple is (name, richAttributeValue).

        >>> rmd = metadata.RichMetadata()
        >>> c = corpus.parse('corelli/opus3no1/1grave')
        >>> rmd.merge(c.metadata)
        >>> rmd.update(c)
        >>> rmd.all()
        (('ambitus',
            AmbitusShort(semitones=48, diatonic='P1', pitchLowest='C2', pitchHighest='C6')),
         ('arranger', 'Michael Scott Cuthbert'),
         ('composer', 'Arcangelo Corelli'),
         ...
         ('sourcePath', 'corelli/opus3no1/1grave.xml'),
         ('tempoFirst', '<music21.tempo.MetronomeMark Quarter=60 (playback only)>'),
         ('tempos', ['<music21.tempo.MetronomeMark Quarter=60 (playback only)>']),
         ('timeSignatureFirst', '4/4'),
         ('timeSignatures', ['4/4']))

        >>> rmd.dateCreated = metadata.DateRelative('1689', 'onOrBefore')
        >>> rmd.localeOfComposition = 'Rome'
        >>> rmd.all(skipContributors=True)
        (('ambitus',
            AmbitusShort(semitones=48, diatonic='P1', pitchLowest='C2', pitchHighest='C6')),
         ('copyright', '© 2014, Creative Commons License (CC-BY)'),
         ('corpusFilePath', 'corelli/opus3no1/1grave.xml'),
         ('dateCreated', '1689/--/-- or earlier'),
         ('fileFormat', 'musicxml'),
         ...
         ('keySignatures', [-1]),
         ('localeOfComposition', 'Rome'),
         ('movementName', 'Sonata da Chiesa, No. I (opus 3, no. 1)'),
         ...
         ('timeSignatures', ['4/4']))

        >>> rmd.all(returnPrimitives=True, returnSorted=False)
        (('software', <music21.metadata.primitives.Text music21 ...>),
         ('software', <music21.metadata.primitives.Text Finale 2014 for Mac>),
         ('software', <music21.metadata.primitives.Text Dolet Light for Finale 2014>),
         ('movementName', <...Text Sonata da Chiesa, No. I (opus 3, no. 1)>),
         ('composer', <music21.metadata.primitives.Contributor composer:Arcangelo Corelli>),
         ...
         ('timeSignatures', ['4/4']))

        >>> rmd.all(skipNonContributors=True, returnPrimitives=True, returnSorted=True)
        (('arranger', <music21.metadata.primitives.Contributor arranger:Michael Scott Cuthbert>),
         ('composer', <music21.metadata.primitives.Contributor composer:Arcangelo Corelli>))
        '''
        allOut: list[tuple[str, t.Any]] = list(super().all(
            skipContributors=skipContributors,
            skipNonContributors=skipNonContributors,
            returnPrimitives=returnPrimitives,
            returnSorted=returnSorted))

        # All RichMetadata additions are considered non-contributors
        if skipNonContributors:
            # it's already sorted if requested
            return tuple(allOut)

        # Note that RichMetadata values do not pay attention to returnPrimitives.
        for name in self.additionalRichMetadataAttributes:
            allOut.append((name, getattr(self, name)))

        if returnSorted:
            return tuple(sorted(allOut))
        return tuple(allOut)

    def _isStandardUniqueName(self, uniqueName: str) -> bool:
        '''
        Determines if a unique name is associated with a standard property.
        Returns False if no such associated standard property can be found.

        Example: a RichMetadata additional attribute name returns True

        >>> rmd = metadata.RichMetadata()
        >>> rmd._isStandardUniqueName('ambitus')
        True

        Example: a standard contributor uniqueName returns True

        >>> rmd._isStandardUniqueName('librettist')
        True

        Example: a standard 'namespace:name' returns False (it is a standard
        namespaceName, but not a standard uniqueName)

        >>> rmd._isStandardUniqueName('marcrel:LBT')
        False

        Example: a standard non-contributor uniqueName returns True

        >>> rmd._isStandardUniqueName('alternativeTitle')
        True

        Example: a custom (non-standard) name returns False (it is not
        a standard name of any sort)

        >>> rmd._isStandardUniqueName('average duration')
        False
        '''
        if super()._isStandardUniqueName(uniqueName):
            return True
        if uniqueName in self.additionalRichMetadataAttributes:
            return True
        return False


# -----------------------------------------------------------------------------
# tests are in test/test_metadata
_DOC_ORDER: list[type] = []


if __name__ == '__main__':
    import music21
    music21.mainTest()


# -----------------------------------------------------------------------------
