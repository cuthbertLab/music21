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

    - class Metadata is the class to use for backward compatibility. The guts are
        completely rewritten to support the new extensions, but Metadata's APIs
        are all backward compatible. ExtendedMetadata has the same underlying
        implementation, and is allowed to redefine existing APIs to behave in a
        new way.  For example, if you use Metadata directly, then the various
        properties like md.alternateTitle cast to str, as before. If you use
        ExtendedMetadata, md.alternateTitle will return the underlying Text
        type. (Note: Text is enhanced with a few new fields, but in a backward
        compatible way, so no new Text class is defined.)

        This class structure introduces a problem: if you get the metadata from a
        stream, you will get unpredictable behavior based on whether the parser
        placed a Metadata or ExtendedMetadata in the stream.  Solution: have a
        new Stream property (s.extendedMetadata) that always returns an
        ExtendedMetadata object. We will need to have one underlying ground
        truth object, with a conversion taking place if necessary.  Conversion
        should be straightforward, since there is only one underlying
        implementation.  There are other ways to get metadata from a stream
        (via the usual get-an-object-from-a-stream APIs), but in those, you are
        searching by type.  Old clients will need to always be able to find type
        Metadata, so Metadata must be in the class hierarchy of ExtendedMetadata.
        New clients will want to be able to get ExtendedMetadata, but we can't
        have both backward and forward compatibility here, so new clients will
        need to know to look for Metadata, and then if the result is not
        actually ExtendedMetadata, to do a conversion to ExtendedMetadata:

            metadata: [ExtendedMetadata] = stream.getElementsByClass(Metadata)
            for md in metadata:
                if not isinstance(metadata, ExtendedMetadata):
                    md = ExtendedMetadata(md)
                processExtendedMetadata(md)

        This implies that ExtendedMetadata.__init__ needs to have a way to
        initialize from a Metadata, or better from any MetadataBase, so
        clients don't actually need to check the type:

            metadata: [ExtendedMetadata] = stream.getElementsByClass(Metadata)
            for md in metadata:
                processExtendedMetadata(ExtendedMetadata(md))

        The class hierarchy to manage all this will be:
        MetadataBase (new implementation, has new "support" APIs)
            Metadata (uses MetadataBase's new "support" APIs, but has
                        only old client APIs with old behavior)
                ExtendedMetadata (uses MetadataBase's new "support" APIs,
                                    has only new behavior)
        I thought about doing:
        Metadata
            ExtendedMetadata

        or even just:
        Metadata (with both new and old APIs)

        but trying to combine new implementation with backward compatibility APIs
        (and new client APIs) gave me a headache.

        I also considered:
        MetadataBase (implementation)
            Metadata (thin compatible API)
            ExtendedMetadata (thin new API)

        but I needed ExtendedMetadata to be derived from Metadata, so old clients can
        find it via getElementsByClass(Metadata)

    - The old metadata had a list of supported workIds, and also a list of supported
        contributor roles.  You could have more than one of each role, but only one
        of each workId.
        In the new implementation, I don't really treat contributor roles differently
        from other metadata.  I have a list of supported property terms, which are
        pulled from Dublin Core (namespace = 'dcterm'), MARC Relator codes (a.k.a.
        contributor roles, namespace = 'marcrel'), and several music21-specific things
        that I have to continue supporting even though I can't find any official List
        of terms that support them (namespace = 'music21').  An example is 'popularTitle'.
        You can have more than one of any of these.  That implies that I need two APIs
        for adding a new piece of metadata.  One that does "this is the new (only) value
        for this metadata property term", and one that does "this is a new value to add in to any
        other values you might have for this metadata property term".  They are:
        addItem() and setItem().  addItem adds the new item to the (possibly empty)
        set of values, and setItem removes any current value(s) before adding the item.

    - Primitives: Old code had DateXxxx and Text.  DateXxxx still works for Dublin Core
        et al (it's a superset of what is needed), but Text needs to add the ability to
        know whether or not the text has been translated, as well as a specified encoding
        scheme (a.k.a. what standard should I use to parse this string) so I have added
        new fields to Text in a backward-compatible way.

    - I have not yet tried to support client-specified namespaces, but I do have a few
        APIs (getPersonalItem, addPersonalItem, setPersonalItem) that have no namespace
        at all, so clients can set anything they want and (hopefully) get it passed through.
        The first client-specified namespace I will try is 'humdrum' for all the crazy humdrum
        metadata that music21 doesn't really need to add as officially supported.

    - Copyright stuff: Everybody does this differently, so there's no straightforward mapping
        from (say) humdrum copyright stuff to Dublin Core copyright stuff. Dublin Core has
        'rights', 'accessRights', 'rightsHolder', 'dateCopyrighted', and 'license'.
        This will require, I think, some special code/data structure in music21, and then
        parsers and writers will need to deal specially with it.  For now I don't handle it
        well.  It might even be represented as a new 'copyright' property term with
        namespace='music21'.

    - A new type that drives a lot of the implementation: Property
        A Property is a namedtuple with (currently) four fields that describe a property
            code is a (possibly abbreviated) code for the property
            name is the official name of the property (tail of the property term URI)
            label is the human readable name of the Property
            namespace is the namespace in which the property is named (e.g. 'dcterm' for
                Dublin Core terms, 'marcrel' for MARC Relator terms, etc)
        The list of supported properties is STDPROPERTIES, and various lists and dicts are
        created from that for later use.

    - Data structure for all the metadata:
        Metadata contains a _metadata attribute which is a dict, where the keys are
        f'{namespace}:{name}', and the value is one of Text, DateXxxx, or a
        List of values of those types (for properties that have more than one value).

'''
from collections import OrderedDict, namedtuple
from dataclasses import dataclass
import os
import pathlib
import re
import copy
import unittest
import typing as t

from music21 import prebase
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
    'Metadata',         # the old API
    'ExtendedMetadata', # the new API (but derived from Metadata)
    'RichMetadata',
    'AmbitusShort',
    'Property'
]

from music21 import environment
environLocal = environment.Environment(os.path.basename(__file__))

_propertyFields = ('abbrevCode', 'name', 'label', 'namespace',
                   'isContributor', 'm21Abbrev', 'm21WorkId')
Property = namedtuple('Property', _propertyFields, defaults=(None,) * len(_propertyFields))

@dataclass
class FileInfo:
    path: t.Optional[Text] = None
    number: t.Optional[int] = None
    format: t.Optional[Text] = None

AmbitusShort = namedtuple('AmbitusShort',
                          ['semitones', 'diatonic', 'pitchLowest', 'pitchHighest'])

# -----------------------------------------------------------------------------

class MetadataBase(base.Music21Object):

    # CLASS VARIABLES #

    classSortOrder = -30

    # STDPROPERTIES: each Tuple in this list is
    # abbrevCode, name, label, namespace, m21Abbrev, m21WorkId, isContributor
    # where:
    # code is an abbreviation for the name
    # name is the tail of the property term URI
    # label is the human-readable name of the property term
    # namespace is a shortened form of the URI for the set of terms
    #   e.g. 'dcterm' means the property term is from the Dublin Core property terms.
    #   'dcterm' is the shortened form of <http://purl.org/dc/terms/>
    #   e.g. 'marcrel' means the property term is from the MARC Relator terms (a.k.a. 'roles').
    #   'marcrel' is the shortened form of <http://www.loc.gov/loc.terms/relators/>
    # isContributor: bool describes whether or not this property is a contributor role
    #   The following two are optional...
    # m21Abbrev is the old abbreviation (from Metadata.workIdAbbreviationDict)
    #       Note that this is None if namespace is 'music21' (abbrevCode is used in
    #       that case), and this is also None if the property doesn't map into the
    #       workId list at all.
    # m21WorkId is the old workID (from Metadata.workIdAbbreviationDict)
    #       Note that this is None if namespace is 'music21' (name is used in
    #       that case), and this is also None if the property doesn't map into the
    #       workId list at all, unless it is 'composer', 'copyright' or 'date',
    #       which are used in searchAttributes as (a sort of) workId with no abbrev.

    STDPROPERTIES: Tuple[Property] = (
        # The following 'dcterm' properties are the standard Dublin Core property terms
        # found at http://purl.org/dc/terms/

        # abstract: A summary of the resource.
        Property(abbrevCode='AB',
                 name='abstract',
                 label='Abstract',
                 namespace='dcterm',
                 isContributor=False),

        # accessRights: Information about who access the resource or an indication of
        #   its security status.
        Property(abbrevCode='AR',
                 name='accessRights',
                 label='Access Rights',
                 namespace='dcterm',
                 isContributor=False),

        # accrualMethod: The method by which items are added to a collection.
        Property(abbrevCode='AM',
                 name='accrualMethod',
                 label='Accrual Method',
                 namespace='dcterm',
                 isContributor=False),

        # accrualPeriodicity: The frequency with which items are added to a collection.
        Property(abbrevCode='AP',
                 name='accrualPeriodicity',
                 label='Accrual Periodicity',
                 namespace='dcterm',
                 isContributor=False),

        # accrualPolicy: The policy governing the addition of items to a collection.
        Property(abbrevCode='APL',
                 name='accrualPolicy',
                 label='Accrual Policy',
                 namespace='dcterm',
                 isContributor=False),

        # alternative: An alternative name for the resource.
        Property(abbrevCode='ALT',
                 name='alternative',
                 label='Alternative Title',
                 namespace='dcterm',
                 m21Abbrev='ota',
                 m21WorkId='alternativeTitle',
                 isContributor=False),

        # audience: A class of agents for whom the resource is intended or useful.
        Property(abbrevCode='AUD',
                 name='audience',
                 label='Audience',
                 namespace='dcterm',
                 isContributor=False),

        # available: Date that the resource became or will become available.
        Property(abbrevCode='AVL',
                 name='available',
                 label='Date Available',
                 namespace='dcterm',
                 isContributor=False),

        # bibliographicCitation: A bibliographic reference for the resource.
        Property(abbrevCode='BIB',
                 name='bibliographicCitation',
                 label='Bibliographic Citation',
                 namespace='dcterm',
                 isContributor=False),

        # conformsTo: An established standard to which the described resource conforms.
        Property(abbrevCode='COT',
                 name='conformsTo',
                 label='Conforms To',
                 namespace='dcterm',
                 isContributor=False),

        # contributor: An entity responsible for making contributions to the resource.
        # NOTE: You should use one of the 'marcrel' properties below instead, since
        # this property is very vague. The 'marcrel' properties are considered to be
        # refinements of dcterm:contributor (this property), so if someone asks for
        # everything as Dublin Core metadata, those will all be translated into
        # dcterm:contributor properties.
        Property(abbrevCode='CN',
                 name='contributor',
                 label='Contributor',
                 namespace='dcterm',
                 isContributor=True),

        # coverage: The spatial or temporal topic of the resource, spatial applicability
        #   of the resource, or jurisdiction under which the resource is relevant.
        Property(abbrevCode='CVR',
                 name='coverage',
                 label='Coverage',
                 namespace='dcterm',
                 isContributor=False),

        # created: Date of creation of the resource.
        Property(abbrevCode='CRD',
                 name='created',
                 label='Date Created',
                 namespace='dcterm',
                 m21WorkId='date',  # needed for searchAttributes (no abbrev)
                 isContributor=False),

        # creator: An entity responsible for making the resource.
        Property(abbrevCode='CR',
                 name='creator',
                 label='Creator',
                 namespace='dcterm',
                 isContributor=True),

        # date: A point or period of time associated with an event in the lifecycle
        #   of the resource.
        Property(abbrevCode='DT',
                 name='date',
                 label='Date',
                 namespace='dcterm',
                 isContributor=False),

        # dateAccepted: Date of acceptance of the resource.
        Property(abbrevCode='DTA',
                 name='dateAccepted',
                 label='Date Accepted',
                 namespace='dcterm',
                 isContributor=False),

        # dateCopyrighted: Date of copyright of the resource.
        Property(abbrevCode='DTC',
                 name='dateCopyrighted',
                 label='Date Copyrighted',
                 namespace='dcterm',
                 isContributor=False),

        # dateSubmitted: Date of submission of the resource.
        Property(abbrevCode='DTS',
                 name='dateSubmitted',
                 label='Date Submitted',
                 namespace='dcterm',
                 isContributor=False),

        # description: An account of the resource.
        Property(abbrevCode='DSC',
                 name='description',
                 label='Description',
                 namespace='dcterm',
                 isContributor=False),

        # educationLevel: A class of agents, defined in terms of progression
        #   through an educational or training context, for which the described
        #   resource is intended.
        Property(abbrevCode='EL',
                 name='educationLevel',
                 label='Audience Education Level',
                 namespace='dcterm',
                 isContributor=False),

        # extent: The size or duration of the resource.
        Property(abbrevCode='EXT',
                 name='extent',
                 label='Extent',
                 namespace='dcterm',
                 isContributor=False),

        # format: The file format, physical medium, or dimensions of the resource.
        Property(abbrevCode='FMT',
                 name='format',
                 label='Format',
                 namespace='dcterm',
                 isContributor=False),

        # hasFormat: A related resource that is substantially the same as the
        #   pre-existing described resource, but in another format.
        Property(abbrevCode='HFMT',
                 name='hasFormat',
                 label='Has Format',
                 namespace='dcterm',
                 isContributor=False),

        # hasPart: A related resource that is included either physically or
        #   logically in the described resource.
        Property(abbrevCode='HPT',
                 name='hasPart',
                 label='Has Part',
                 namespace='dcterm',
                 isContributor=False),

        # hasVersion: A related resource that is a version, edition, or adaptation
        #   of the described resource.
        Property(abbrevCode='HVS',
                 name='hasVersion',
                 label='Has Version',
                 namespace='dcterm',
                 isContributor=False),

        # identifier: An unambiguous reference to the resource within a given context.
        Property(abbrevCode='ID',
                 name='identifier',
                 label='Identifier',
                 namespace='dcterm',
                 isContributor=False),

        # instructionalMethod: A process, used to engender knowledge, attitudes and
        #   skills, that the described resource is designed to support.
        Property(abbrevCode='IM',
                 name='instructionalMethod',
                 label='Instructional Method',
                 namespace='dcterm',
                 isContributor=False),

        # isFormatOf: A pre-existing related resource that is substantially the same
        #   as the described resource, but in another format.
        Property(abbrevCode='IFMT',
                 name='isFormatOf',
                 label='Is Format Of',
                 namespace='dcterm',
                 isContributor=False),

        # isPartOf: A related resource in which the described resource is physically
        #   or logically included.
        Property(abbrevCode='IPT',
                 name='isPartOf',
                 label='Is Part Of',
                 namespace='dcterm',
                 isContributor=False),

        # isReferencedBy: A related resource that references, cites, or otherwise
        #   points to the described resource.
        Property(abbrevCode='IREF',
                 name='isReferencedBy',
                 label='Is Referenced By',
                 namespace='dcterm',
                 isContributor=False),

        # isReplacedBy: A related resource that supplants, displaces, or supersedes
        #   the described resource.
        Property(abbrevCode='IREP',
                 name='isReplacedBy',
                 label='Is Replaced By',
                 namespace='dcterm',
                 isContributor=False),

        # isRequiredBy: A related resource that requires the described resource
        #   to support its function, delivery, or coherence.
        Property(abbrevCode='IREQ',
                 name='isRequiredBy',
                 label='Is Required By',
                 namespace='dcterm',
                 isContributor=False),

        # issued: Date of formal issuance of the resource.
        Property(abbrevCode='IS',
                 name='issued',
                 label='Date Issued',
                 namespace='dcterm',
                 isContributor=False),

        # isVersionOf: A related resource of which the described resource is a
        #   version, edition, or adaptation.
        Property(abbrevCode='IVSN',
                 name='isVersionOf',
                 label='Is Version Of',
                 namespace='dcterm',
                 isContributor=False),

        # language: A language of the resource.
        Property(abbrevCode='LG',
                 name='language',
                 label='Language',
                 namespace='dcterm',
                 isContributor=False),

        # license: A legal document giving official permission to do something
        #   with the resource.
        Property(abbrevCode='LI',
                 name='license',
                 label='License',
                 namespace='dcterm',
                 isContributor=False),

        # mediator: An entity that mediates access to the resource.
        Property(abbrevCode='ME',
                 name='mediator',
                 label='Mediator',
                 namespace='dcterm',
                 isContributor=False),

        # medium: The material or physical carrier of the resource.
        Property(abbrevCode='MED',
                 name='medium',
                 label='Medium',
                 namespace='dcterm',
                 isContributor=False),

        # modified: Date on which the resource was changed.
        Property(abbrevCode='MOD',
                 name='modified',
                 label='Date Modified',
                 namespace='dcterm',
                 isContributor=False),

        # provenance: A statement of any changes in ownership and custody of
        #   the resource since its creation that are significant for its
        #   authenticity, integrity, and interpretation.
        Property(abbrevCode='PRV',
                 name='provenance',
                 label='Provenance',
                 namespace='dcterm',
                 isContributor=False),

        # publisher: An entity responsible for making the resource available.
        Property(abbrevCode='PBL',
                 name='publisher',
                 label='Publisher',
                 namespace='dcterm',
                 isContributor=True),

        # references: A related resource that is referenced, cited, or
        #   otherwise pointed to by the described resource.
        Property(abbrevCode='REF',
                 name='references',
                 label='References',
                 namespace='dcterm',
                 isContributor=False),

        # relation: A related resource.
        Property(abbrevCode='REL',
                 name='relation',
                 label='Relation',
                 namespace='dcterm',
                 isContributor=False),

        # replaces: A related resource that is supplanted, displaced, or
        #   superseded by the described resource.
        Property(abbrevCode='REP',
                 name='replaces',
                 label='Replaces',
                 namespace='dcterm',
                 isContributor=False),

        # requires: A related resource that is required by the described
        #   resource to support its function, delivery, or coherence.
        Property(abbrevCode='REQ',
                 name='requires',
                 label='Requires',
                 namespace='dcterm',
                 isContributor=False),

        # rights: Information about rights held in and over the resource.
        Property(abbrevCode='RT',
                 name='rights',
                 label='Rights',
                 namespace='dcterm',
                 m21WorkId='copyright', # no abbrev
                 isContributor=False),

        # rightsHolder: A person or organization owning or managing rights
        #   over the resource.
        Property(abbrevCode='RH',
                 name='rightsHolder',
                 label='Rights Holder',
                 namespace='dcterm',
                 isContributor=True),

        # source: A related resource from which the described resource
        #   is derived.
        Property(abbrevCode='SRC',
                 name='source',
                 label='Source',
                 namespace='dcterm',
                 isContributor=False),

        # spatial: Spatial characteristics of the resource.
        Property(abbrevCode='SP',
                 name='spatial',
                 label='Spatial Coverage',
                 namespace='dcterm',
                 isContributor=False),

        # subject: A topic of the resource.
        Property(abbrevCode='SUB',
                 name='subject',
                 label='Subject',
                 namespace='dcterm',
                 isContributor=False),

        # tableOfContents: A list of subunits of the resource.
        Property(abbrevCode='TOC',
                 name='tableOfContents',
                 label='Table Of Contents',
                 namespace='dcterm',
                 isContributor=False),

        # temporal: Temporal characteristics of the resource.
        Property(abbrevCode='TE',
                 name='temporal',
                 label='Temporal Coverage',
                 namespace='dcterm',
                 isContributor=False),

        # title: A name given to the resource.
        Property(abbrevCode='T',
                 name='title',
                 label='Title',
                 namespace='dcterm',
                 m21Abbrev='otl',
                 m21WorkId='title',
                 isContributor=False),

        # type : The nature or genre of the resource.
        Property(abbrevCode='TYP',
                 name='type',
                 label='Type',
                 namespace='dcterm',
                 isContributor=False),

        # valid: Date (often a range) of validity of a resource.
        Property(abbrevCode='VA',
                 name='valid',
                 label='Date Valid',
                 namespace='dcterm',
                 isContributor=False),

        # The following 'marcrel' property terms are the MARC Relator terms
        # that are refinements of dcterm:contributor, and can be used anywhere
        # dcterm:contributor can be used if you want to be more specific (and
        # you will want to). The MARC Relator terms are defined at:
        # http://www.loc.gov/loc.terms/relators/
        # and this particular sublist can be found at:
        # https://memory.loc.gov/diglib/loc.terms/relators/dc-contributor.html

        # ACT/Actor: a person or organization who principally exhibits acting
        #   skills in a musical or dramatic presentation or entertainment.
        Property(abbrevCode='act',
                 name='ACT',
                 label='Actor',
                 namespace='marcrel',
                 isContributor=True),

        # ADP/Adapter: a person or organization who 1) reworks a musical composition,
        #   usually for a different medium, or 2) rewrites novels or stories
        #   for motion pictures or other audiovisual medium.
        Property(abbrevCode='adp',
                 name='ADP',
                 label='Adapter',
                 namespace='marcrel',
                 isContributor=True),

        # ANM/Animator: a person or organization who draws the two-dimensional
        #   figures, manipulates the three dimensional objects and/or also
        #   programs the computer to move objects and images for the purpose
        #   of animated film processing.
        Property(abbrevCode='anm',
                 name='ANM',
                 label='Animator',
                 namespace='marcrel',
                 isContributor=True),

        # ANN/Annotator: a person who writes manuscript annotations on a printed item.
        Property(abbrevCode='ann',
                 name='ANN',
                 label='Annotator',
                 namespace='marcrel',
                 isContributor=True),

        # ARC/Architect: a person or organization who designs structures or oversees
        #   their construction.
        Property(abbrevCode='arc',
                 name='ARC',
                 label='Architect',
                 namespace='marcrel',
                 isContributor=True),

        # ARR/Arranger: a person or organization who transcribes a musical
        #   composition, usually for a different medium from that of the original;
        #   in an arrangement the musical substance remains essentially unchanged.
        Property(abbrevCode='arr',
                 name='ARR',
                 label='Arranger',
                 namespace='marcrel',
                 m21WorkId='arranger',
                 m21Abbrev='lar',
                 isContributor=True),

        # ART/Artist: a person (e.g., a painter) or organization who conceives, and
        #   perhaps also implements, an original graphic design or work of art, if
        #   specific codes (e.g., [egr], [etr]) are not desired. For book illustrators,
        #   prefer Illustrator [ill].
        Property(abbrevCode='art',
                 name='ART',
                 label='Artist',
                 namespace='marcrel',
                 isContributor=True),

        # AUT/Author: a person or organization chiefly responsible for the
        #   intellectual or artistic content of a work, usually printed text.
        Property(abbrevCode='aut',
                 name='AUT',
                 label='Author',
                 namespace='marcrel',
                 isContributor=True),

        # AQT/Author in quotations or text extracts: a person or organization
        #   whose work is largely quoted or extracted in works to which he or
        #   she did not contribute directly.
        Property(abbrevCode='aqt',
                 name='AQT',
                 label='Author in quotations or text extracts',
                 namespace='marcrel',
                 isContributor=True),

        # AFT/Author of afterword, colophon, etc.: a person or organization
        #   responsible for an afterword, postface, colophon, etc. but who
        #   is not the chief author of a work.
        Property(abbrevCode='aft',
                 name='AFT',
                 label='Author of afterword, colophon, etc.',
                 namespace='marcrel',
                 isContributor=True),

        # AUD/Author of dialog: a person or organization responsible for
        #   the dialog or spoken commentary for a screenplay or sound
        #   recording.
        Property(abbrevCode='aud',
                 name='AUD',
                 label='Author of dialog',
                 namespace='marcrel',
                 isContributor=True),

        # AUI/Author of introduction, etc.:  a person or organization
        #   responsible for an introduction, preface, foreword, or other
        #   critical introductory matter, but who is not the chief author.
        Property(abbrevCode='aui',
                 name='AUI',
                 label='Author of introduction, etc.',
                 namespace='marcrel',
                 isContributor=True),

        # AUS/Author of screenplay, etc.:  a person or organization responsible
        #   for a motion picture screenplay, dialog, spoken commentary, etc.
        Property(abbrevCode='aus',
                 name='AUS',
                 label='Author of screenplay, etc.',
                 namespace='marcrel',
                 isContributor=True),

        # CLL/Calligrapher: a person or organization who writes in an artistic
        #   hand, usually as a copyist and or engrosser.
        Property(abbrevCode='cll',
                 name='CLL',
                 label='Calligrapher',
                 namespace='marcrel',
                 isContributor=True),

        # CTG/Cartographer: a person or organization responsible for the
        #   creation of maps and other cartographic materials.
        Property(abbrevCode='ctg',
                 name='CTG',
                 label='Cartographer',
                 namespace='marcrel',
                 isContributor=True),

        # CHR/Choreographer: a person or organization who composes or arranges
        #   dances or other movements (e.g., "master of swords") for a musical
        #   or dramatic presentation or entertainment.
        Property(abbrevCode='chr',
                 name='CHR',
                 label='Choreographer',
                 namespace='marcrel',
                 isContributor=True),

        # CNG/Cinematographer: a person or organization who is in charge of
        #   the images captured for a motion picture film. The cinematographer
        #   works under the supervision of a director, and may also be referred
        #   to as director of photography. Do not confuse with videographer.
        Property(abbrevCode='cng',
                 name='CNG',
                 label='Cinematographer',
                 namespace='marcrel',
                 isContributor=True),

        # CLB/Collaborator: a person or organization that takes a limited part
        #   in the elaboration of a work of another person or organization that
        #   brings complements (e.g., appendices, notes) to the work.
        Property(abbrevCode='clb',
                 name='CLB',
                 label='Collaborator',
                 namespace='marcrel',
                 isContributor=True),

        # CLT/Collotyper: a person or organization responsible for the production
        #   of photographic prints from film or other colloid that has ink-receptive
        #   and ink-repellent surfaces.
        Property(abbrevCode='clt',
                 name='CLT',
                 label='Collotyper',
                 namespace='marcrel',
                 isContributor=True),

        # CMM/Commentator: a person or organization who provides interpretation,
        #   analysis, or a discussion of the subject matter on a recording,
        #   motion picture, or other audiovisual medium.
        Property(abbrevCode='cmm',
                 name='CMM',
                 label='Commentator',
                 namespace='marcrel',
                 isContributor=True),

        # CWT/Commentator for written text: a person or organization responsible
        #   for the commentary or explanatory notes about a text. For the writer
        #   of manuscript annotations in a printed book, use Annotator [ann].
        Property(abbrevCode='cwt',
                 name='CWT',
                 label='Commentator for written text',
                 namespace='marcrel',
                 isContributor=True),

        # COM/Compiler: a person or organization who produces a work or
        #   publication by selecting and putting together material from the
        #   works of various persons or bodies.
        Property(abbrevCode='com',
                 name='COM',
                 label='Compiler',
                 namespace='marcrel',
                 isContributor=True),

        # CMP/Composer: a person or organization who creates a musical work,
        #   usually a piece of music in manuscript or printed form.
        Property(abbrevCode='cmp',
                 name='CMP',
                 label='Composer',
                 namespace='marcrel',
                 m21WorkId='composer',
                 m21Abbrev='com',
                 isContributor=True),

        # CCP/Conceptor: a person or organization responsible for the original
        #   idea on which a work is based, this includes the scientific author
        #   of an audio-visual item and the conceptor of an advertisement.
        Property(abbrevCode='ccp',
                 name='CCP',
                 label='Conceptor',
                 namespace='marcrel',
                 isContributor=True),

        # CND/Conductor: a person who directs a performing group (orchestra,
        #   chorus, opera, etc.) in a musical or dramatic presentation or
        #   entertainment.
        Property(abbrevCode='cnd',
                 name='CND',
                 label='Conductor',
                 namespace='marcrel',
                 isContributor=True),

        # CSL/Consultant: a person or organization relevant to a resource, who
        #   is called upon for professional advice or services in a specialized
        #   field of knowledge or training.
        Property(abbrevCode='csl',
                 name='CSL',
                 label='Consultant',
                 namespace='marcrel',
                 isContributor=True),

        # CSP/Consultant to a project: a person or organization relevant to a
        #   resource, who is engaged specifically to provide an intellectual
        #   overview of a strategic or operational task and by analysis,
        #   specification, or instruction, to create or propose a cost-effective
        #   course of action or solution.
        Property(abbrevCode='csp',
                 name='CSP',
                 label='Consultant to a project',
                 namespace='marcrel',
                 isContributor=True),

        # CTR/Contractor: a person or organization relevant to a resource, who
        #   enters into a contract with another person or organization to
        #   perform a specific task.
        Property(abbrevCode='ctr',
                 name='CTR',
                 label='Contractor',
                 namespace='marcrel',
                 isContributor=True),

        # CTB/Contributor: a person or organization one whose work has been
        #   contributed to a larger work, such as an anthology, serial
        #   publication, or other compilation of individual works. Do not
        #   use if the sole function in relation to a work is as author,
        #   editor, compiler or translator.
        # Note: this is in fact a refinement of dcterm:contributor, since
        # it is more specific than that one.
        Property(abbrevCode='ctb',
                 name='CTB',
                 label='Contributor',
                 namespace='marcrel',
                 isContributor=True),

        # CRP/Correspondent: a person or organization who was either
        #   the writer or recipient of a letter or other communication.
        Property(abbrevCode='crp',
                 name='CRP',
                 label='Correspondent',
                 namespace='marcrel',
                 isContributor=True),

        # CST/Costume designer: a person or organization who designs
        #   or makes costumes, fixes hair, etc., for a musical or
        #   dramatic presentation or entertainment.
        Property(abbrevCode='cst',
                 name='CST',
                 label='Costume designer',
                 namespace='marcrel',
                 isContributor=True),

        # CRE/Creator: a person or organization responsible for the
        #   intellectual or artistic content of a work.
        Property(abbrevCode='cre',
                 name='CRE',
                 label='Creator',
                 namespace='marcrel',
                 isContributor=True),

        # CUR/Curator of an exhibition: a person or organization
        #   responsible for conceiving and organizing an exhibition.
        Property(abbrevCode='cur',
                 name='CUR',
                 label='Curator of an exhibition',
                 namespace='marcrel',
                 isContributor=True),

        # DNC/Dancer: a person or organization who principally
        #   exhibits dancing skills in a musical or dramatic
        #   presentation or entertainment.
        Property(abbrevCode='dnc',
                 name='DNC',
                 label='Dancer',
                 namespace='marcrel',
                 isContributor=True),

        # DLN/Delineator: a person or organization executing technical
        #   drawings from others' designs.
        Property(abbrevCode='dln',
                 name='DLN',
                 label='Delineator',
                 namespace='marcrel',
                 isContributor=True),

        # DSR/Designer: a person or organization responsible for the design
        #   if more specific codes (e.g., [bkd], [tyd]) are not desired.
        Property(abbrevCode='dsr',
                 name='DSR',
                 label='Designer',
                 namespace='marcrel',
                 isContributor=True),

        # DRT/Director: a person or organization who is responsible for the
        #   general management of a work or who supervises the production of
        #   a performance for stage, screen, or sound recording.
        Property(abbrevCode='drt',
                 name='DRT',
                 label='Director',
                 namespace='marcrel',
                 isContributor=True),

        # DIS/Dissertant: a person who presents a thesis for a university or
        #   higher-level educational degree.
        Property(abbrevCode='dis',
                 name='DIS',
                 label='Dissertant',
                 namespace='marcrel',
                 isContributor=True),

        # DRM/Draftsman: a person or organization who prepares artistic or
        #   technical drawings.
        Property(abbrevCode='drm',
                 name='DRM',
                 label='Draftsman',
                 namespace='marcrel',
                 isContributor=True),

        # EDT/Editor: a person or organization who prepares for publication
        #   a work not primarily his/her own, such as by elucidating text,
        #   adding introductory or other critical matter, or technically
        #   directing an editorial staff.
        Property(abbrevCode='edt',
                 name='EDT',
                 label='Editor',
                 namespace='marcrel',
                 isContributor=True),

        # ENG/Engineer: a person or organization that is responsible for
        #   technical planning and design, particularly with construction.
        Property(abbrevCode='eng',
                 name='ENG',
                 label='Engineer',
                 namespace='marcrel',
                 isContributor=True),

        # EGR/Engraver: a person or organization who cuts letters, figures,
        #   etc. on a surface, such as a wooden or metal plate, for printing.
        Property(abbrevCode='egr',
                 name='EGR',
                 label='Engraver',
                 namespace='marcrel',
                 isContributor=True),

        # ETR/Etcher: a person or organization who produces text or images
        #   for printing by subjecting metal, glass, or some other surface
        #   to acid or the corrosive action of some other substance.
        Property(abbrevCode='etr',
                 name='ETR',
                 label='Etcher',
                 namespace='marcrel',
                 isContributor=True),

        # FAC/Facsimilist: a person or organization that executed the facsimile.
        Property(abbrevCode='fac',
                 name='FAC',
                 label='Facsimilist',
                 namespace='marcrel',
                 isContributor=True),

        # FLM/Film editor: a person or organization who is an editor of a
        #   motion picture film. This term is used regardless of the medium
        #   upon which the motion picture is produced or manufactured (e.g.,
        #   acetate film, video tape).
        Property(abbrevCode='flm',
                 name='FLM',
                 label='Film editor',
                 namespace='marcrel',
                 isContributor=True),

        # FRG/Forger: a person or organization who makes or imitates something
        #   of value or importance, especially with the intent to defraud.
        Property(abbrevCode='frg',
                 name='FRG',
                 label='Forger',
                 namespace='marcrel',
                 isContributor=True),

        # HST/Host: a person who is invited or regularly leads a program
        #   (often broadcast) that includes other guests, performers, etc.
        #   (e.g., talk show host).
        Property(abbrevCode='hst',
                 name='HST',
                 label='Host',
                 namespace='marcrel',
                 isContributor=True),

        # ILU/Illuminator: a person or organization responsible for the
        #   decoration of a work (especially manuscript material) with
        #   precious metals or color, usually with elaborate designs and
        #   motifs.
        Property(abbrevCode='ilu',
                 name='ILU',
                 label='Illuminator',
                 namespace='marcrel',
                 isContributor=True),

        # ILL/Illustrator: a person or organization who conceives, and
        #   perhaps also implements, a design or illustration, usually
        #   to accompany a written text.
        Property(abbrevCode='ill',
                 name='ILL',
                 label='Illustrator',
                 namespace='marcrel',
                 isContributor=True),

        # ITR/Instrumentalist: a person or organization who principally
        #   plays an instrument in a musical or dramatic presentation
        #   or entertainment.
        Property(abbrevCode='itr',
                 name='ITR',
                 label='Instrumentalist',
                 namespace='marcrel',
                 isContributor=True),

        # IVE/Interviewee: a person or organization who is interviewed
        #   at a consultation or meeting, usually by a reporter, pollster,
        #   or some other information gathering agent.
        Property(abbrevCode='ive',
                 name='IVE',
                 label='Interviewee',
                 namespace='marcrel',
                 isContributor=True),

        # IVR/Interviewer: a person or organization who acts as a reporter,
        #   pollster, or other information gathering agent in a consultation
        #   or meeting involving one or more individuals.
        Property(abbrevCode='ivr',
                 name='IVR',
                 label='Interviewer',
                 namespace='marcrel',
                 isContributor=True),

        # INV/Inventor: a person or organization who first produces a
        #   particular useful item, or develops a new process for
        #   obtaining a known item or result.
        Property(abbrevCode='inv',
                 name='INV',
                 label='Inventor',
                 namespace='marcrel',
                 isContributor=True),

        # LSA/Landscape architect: a person or organization whose work
        #   involves coordinating the arrangement of existing and
        #   proposed land features and structures.
        Property(abbrevCode='lsa',
                 name='LSA',
                 label='Landscape architect',
                 namespace='marcrel',
                 isContributor=True),

        # LBT/Librettist: a person or organization who is a writer of
        #   the text of an opera, oratorio, etc.
        Property(abbrevCode='lbt',
                 name='LBT',
                 label='Librettist',
                 namespace='marcrel',
                 m21WorkId='librettist',
                 m21Abbrev='lib',
                 isContributor=True),

        # LGD/Lighting designer: a person or organization who designs the
        #   lighting scheme for a theatrical presentation, entertainment,
        #   motion picture, etc.
        Property(abbrevCode='lgd',
                 name='LGD',
                 label='Lighting designer',
                 namespace='marcrel',
                 isContributor=True),

        # LTG/Lithographer: a person or organization who prepares the stone
        #   or plate for lithographic printing, including a graphic artist
        #   creating a design directly on the surface from which printing
        #   will be done.
        Property(abbrevCode='ltg',
                 name='LTG',
                 label='Lithographer',
                 namespace='marcrel',
                 isContributor=True),

        # LYR/Lyricist: a person or organization who is the a writer of the
        #   text of a song.
        Property(abbrevCode='lyr',
                 name='LYR',
                 label='Lyricist',
                 namespace='marcrel',
                 m21WorkId='lyricist',
                 m21Abbrev='lyr',
                 isContributor=True),

        # MFR/Manufacturer: a person or organization that makes an
        #   artifactual work (an object made or modified by one or
        #   more persons). Examples of artifactual works include vases,
        #   cannons or pieces of furniture.
        Property(abbrevCode='mfr',
                 name='MFR',
                 label='Manufacturer',
                 namespace='marcrel',
                 isContributor=True),

        # MTE/Metal-engraver: a person or organization responsible for
        #   decorations, illustrations, letters, etc. cut on a metal
        #   surface for printing or decoration.
        Property(abbrevCode='mte',
                 name='MTE',
                 label='Metal-engraver',
                 namespace='marcrel',
                 isContributor=True),

        # MOD/Moderator: a person who leads a program (often broadcast)
        #   where topics are discussed, usually with participation of
        #   experts in fields related to the discussion.
        Property(abbrevCode='mod',
                 name='MOD',
                 label='Moderator',
                 namespace='marcrel',
                 isContributor=True),

        # MUS/Musician: a person or organization who performs music or
        #   contributes to the musical content of a work when it is not
        #   possible or desirable to identify the function more precisely.
        Property(abbrevCode='mus',
                 name='MUS',
                 label='Musician',
                 namespace='marcrel',
                 isContributor=True),

        # NRT/Narrator: a person who is a speaker relating the particulars
        #   of an act, occurrence, or course of events.
        Property(abbrevCode='nrt',
                 name='NRT',
                 label='Narrator',
                 namespace='marcrel',
                 isContributor=True),

        # ORM/Organizer of meeting: a person or organization responsible
        #   for organizing a meeting for which an item is the report or
        #   proceedings.
        Property(abbrevCode='orm',
                 name='ORM',
                 label='Organizer of meeting',
                 namespace='marcrel',
                 isContributor=True),

        # ORG/Originator: a person or organization performing the work,
        #   i.e., the name of a person or organization associated with
        #   the intellectual content of the work. This category does not
        #   include the publisher or personal affiliation, or sponsor
        #   except where it is also the corporate author.
        Property(abbrevCode='org',
                 name='ORG',
                 label='Originator',
                 namespace='marcrel',
                 isContributor=True),

        # PRF/Performer: a person or organization who exhibits musical
        #   or acting skills in a musical or dramatic presentation or
        #   entertainment, if specific codes for those functions ([act],
        #   [dnc], [itr], [voc], etc.) are not used. If specific codes
        #   are used, [prf] is used for a person whose principal skill
        #   is not known or specified.
        Property(abbrevCode='prf',
                 name='PRF',
                 label='Performer',
                 namespace='marcrel',
                 isContributor=True),

        # PHT/Photographer: a person or organization responsible for
        #   taking photographs, whether they are used in their original
        #   form or as reproductions.
        Property(abbrevCode='pht',
                 name='PHT',
                 label='Photographer',
                 namespace='marcrel',
                 isContributor=True),

        # PLT/Platemaker: a person or organization responsible for the
        #   production of plates, usually for the production of printed
        #   images and/or text.
        Property(abbrevCode='plt',
                 name='PLT',
                 label='Platemaker',
                 namespace='marcrel',
                 isContributor=True),

        # PRM/Printmaker: a person or organization who makes a relief,
        #   intaglio, or planographic printing surface.
        Property(abbrevCode='prm',
                 name='PRM',
                 label='Printmaker',
                 namespace='marcrel',
                 isContributor=True),

        # PRO/Producer: a person or organization responsible for the
        #   making of a motion picture, including business aspects,
        #   management of the productions, and the commercial success
        #   of the work.
        Property(abbrevCode='pro',
                 name='PRO',
                 label='Producer',
                 namespace='marcrel',
                 isContributor=True),

        # PRD/Production personnel: a person or organization associated
        #   with the production (props, lighting, special effects, etc.)
        #   of a musical or dramatic presentation or entertainment.
        Property(abbrevCode='prd',
                 name='PRD',
                 label='Production personnel',
                 namespace='marcrel',
                 isContributor=True),

        # PRG/Programmer: a person or organization responsible for the
        #   creation and/or maintenance of computer program design
        #   documents, source code, and machine-executable digital files
        #   and supporting documentation.
        Property(abbrevCode='prg',
                 name='PRG',
                 label='Programmer',
                 namespace='marcrel',
                 isContributor=True),

        # PPT/Puppeteer: a person or organization who manipulates, controls,
        #   or directs puppets or marionettes in a musical or dramatic
        #   presentation or entertainment.
        Property(abbrevCode='ppt',
                 name='PPT',
                 label='Puppeteer',
                 namespace='marcrel',
                 isContributor=True),

        # RCE/Recording engineer: a person or organization who supervises
        #   the technical aspects of a sound or video recording session.
        Property(abbrevCode='rce',
                 name='RCE',
                 label='Recording engineer',
                 namespace='marcrel',
                 isContributor=True),

        # REN/Renderer: a person or organization who prepares drawings
        #   of architectural designs (i.e., renderings) in accurate,
        #   representational perspective to show what the project will
        #   look like when completed.
        Property(abbrevCode='ren',
                 name='REN',
                 label='Renderer',
                 namespace='marcrel',
                 isContributor=True),

        # RPT/Reporter: a person or organization who writes or presents
        #   reports of news or current events on air or in print.
        Property(abbrevCode='rpt',
                 name='RPT',
                 label='Reporter',
                 namespace='marcrel',
                 isContributor=True),

        # RTH/Research team head: a person who directed or managed a
        #   research project.
        Property(abbrevCode='rth',
                 name='RTH',
                 label='Research team head',
                 namespace='marcrel',
                 isContributor=True),

        # RTM/Research team member:  a person who participated in a
        #   research project but whose role did not involve direction
        #   or management of it.
        Property(abbrevCode='rtm',
                 name='RTM',
                 label='Research team member',
                 namespace='marcrel',
                 isContributor=True),

        # RES/Researcher: a person or organization responsible for
        #   performing research.
        Property(abbrevCode='res',
                 name='RES',
                 label='Researcher',
                 namespace='marcrel',
                 isContributor=True),

        # RPY/Responsible party: a person or organization legally
        #   responsible for the content of the published material.
        Property(abbrevCode='rpy',
                 name='RPY',
                 label='Responsible party',
                 namespace='marcrel',
                 isContributor=True),

        # RSG/Restager: a person or organization, other than the
        #   original choreographer or director, responsible for
        #   restaging a choreographic or dramatic work and who
        #   contributes minimal new content.
        Property(abbrevCode='rsg',
                 name='RSG',
                 label='Restager',
                 namespace='marcrel',
                 isContributor=True),

        # REV/Reviewer:  a person or organization responsible for
        #   the review of a book, motion picture, performance, etc.
        Property(abbrevCode='rev',
                 name='REV',
                 label='Reviewer',
                 namespace='marcrel',
                 isContributor=True),

        # SCE/Scenarist: a person or organization who is the author
        #   of a motion picture screenplay.
        Property(abbrevCode='sce',
                 name='SCE',
                 label='Scenarist',
                 namespace='marcrel',
                 isContributor=True),

        # SAD/Scientific advisor: a person or organization who brings
        #   scientific, pedagogical, or historical competence to the
        #   conception and realization on a work, particularly in the
        #   case of audio-visual items.
        Property(abbrevCode='sad',
                 name='SAD',
                 label='Scientific advisor',
                 namespace='marcrel',
                 isContributor=True),

        # SCR/Scribe: a person who is an amanuensis and for a writer of
        #   manuscripts proper. For a person who makes pen-facsimiles,
        #   use Facsimilist [fac].
        Property(abbrevCode='scr',
                 name='SCR',
                 label='Scribe',
                 namespace='marcrel',
                 isContributor=True),

        # SCL/Sculptor: a person or organization who models or carves
        #   figures that are three-dimensional representations.
        Property(abbrevCode='scl',
                 name='SCL',
                 label='Sculptor',
                 namespace='marcrel',
                 isContributor=True),

        # SEC/Secretary: a person or organization who is a recorder,
        #   redactor, or other person responsible for expressing the
        #   views of a organization.
        Property(abbrevCode='sec',
                 name='SEC',
                 label='Secretary',
                 namespace='marcrel',
                 isContributor=True),

        # STD/Set designer:  a person or organization who translates the
        #   rough sketches of the art director into actual architectural
        #   structures for a theatrical presentation, entertainment, motion
        #   picture, etc. Set designers draw the detailed guides and
        #   specifications for building the set.
        Property(abbrevCode='std',
                 name='STD',
                 label='Set designer',
                 namespace='marcrel',
                 isContributor=True),

        # SNG/Singer: a person or organization who uses his/her/their voice
        #   with or without instrumental accompaniment to produce music.
        #   A performance may or may not include actual words.
        Property(abbrevCode='sng',
                 name='SNG',
                 label='Singer',
                 namespace='marcrel',
                 isContributor=True),

        # SPK/Speaker: a person who participates in a program (often broadcast)
        #   and makes a formalized contribution or presentation generally
        #   prepared in advance.
        Property(abbrevCode='spk',
                 name='SPK',
                 label='Speaker',
                 namespace='marcrel',
                 isContributor=True),

        # STN/Standards body: an organization responsible for the development
        #   or enforcement of a standard.
        Property(abbrevCode='stn',
                 name='STN',
                 label='Standards body',
                 namespace='marcrel',
                 isContributor=True),

        # STL/Storyteller: a person relaying a story with creative and/or
        #   theatrical interpretation.
        Property(abbrevCode='stl',
                 name='STL',
                 label='Storyteller',
                 namespace='marcrel',
                 isContributor=True),

        # SRV/Surveyor: a person or organization who does measurements of
        #   tracts of land, etc. to determine location, forms, and boundaries.
        Property(abbrevCode='srv',
                 name='SRV',
                 label='Surveyor',
                 namespace='marcrel',
                 isContributor=True),

        # TCH/Teacher: a person who, in the context of a resource, gives
        #   instruction in an intellectual subject or demonstrates while
        #   teaching physical skills.
        Property(abbrevCode='tch',
                 name='TCH',
                 label='Teacher',
                 namespace='marcrel',
                 isContributor=True),

        # TRC/Transcriber: a person who prepares a handwritten or typewritten copy
        #   from original material, including from dictated or orally recorded
        #   material. For makers of pen-facsimiles, use Facsimilist [fac].
        Property(abbrevCode='trc',
                 name='TRC',
                 label='Transcriber',
                 namespace='marcrel',
                 isContributor=True),

        # TRL/Translator: a person or organization who renders a text from one
        #   language into another, or from an older form of a language into the
        #   modern form.
        Property(abbrevCode='trl',
                 name='TRL',
                 label='Translator',
                 namespace='marcrel',
                 m21WorkId='translator',
                 m21Abbrev='trn',
                 isContributor=True),

        # VDG/Videographer: a person or organization in charge of a video production,
        #   e.g. the video recording of a stage production as opposed to a commercial
        #   motion picture. The videographer may be the camera operator or may
        #   supervise one or more camera operators. Do not confuse with cinematographer.
        Property(abbrevCode='vdg',
                 name='VDG',
                 label='Videographer',
                 namespace='marcrel',
                 isContributor=True),

        # VOC/Vocalist: a person or organization who principally exhibits singing
        #   skills in a musical or dramatic presentation or entertainment.
        Property(abbrevCode='voc',
                 name='VOC',
                 label='Vocalist',
                 namespace='marcrel',
                 isContributor=True),

        # WDE/Wood-engraver: a person or organization who makes prints by cutting
        #   the image in relief on the end-grain of a wood block.
        Property(abbrevCode='wde',
                 name='WDE',
                 label='Wood-engraver',
                 namespace='marcrel',
                 isContributor=True),

        # WDC/Woodcutter: a person or organization who makes prints by cutting the
        #   image in relief on the plank side of a wood block.
        Property(abbrevCode='wdc',
                 name='WDC',
                 label='Woodcutter',
                 namespace='marcrel',
                 isContributor=True),

        # WAM/Writer of accompanying material: a person or organization who writes
        #   significant material which accompanies a sound recording or other
        #   audiovisual material.
        Property(abbrevCode='wam',
                 name='WAM',
                 label='Writer of accompanying material',
                 namespace='marcrel',
                 isContributor=True),

        # The following marcrel property term refines dcterm:publisher

        # DST/Distributor: a person or organization that has exclusive or shared
        #   marketing rights for an item.
        Property(abbrevCode='dst',
                 name='DST',
                 label='Distributor',
                 namespace='marcrel',
                 isContributor=True),

        # The following music21 property terms have historically been supported
        # by music21, so we must add them as standard property terms here:

        # textOriginalLanguage: original language of vocal/choral text
        Property(abbrevCode='txo',
                 name='textOriginalLanguage',
                 label='Original Text Language',
                 namespace='music21',
                 isContributor=False),

        # textLanguage: language of the encoded vocal/choral text
        Property(abbrevCode='txl',
                 name='textLanguage',
                 label='Text Language',
                 namespace='music21',
                 isContributor=False),

        # popularTitle: popular title
        Property(abbrevCode='otp',
                 name='popularTitle',
                 label='Popular Title',
                 namespace='music21',
                 isContributor=False),

        # parentTitle: parent title
        Property(abbrevCode='opr',
                 name='parentTitle',
                 label='Parent Title',
                 namespace='music21',
                 isContributor=False),

        # actNumber: act number (e.g. '2' or 'Act 2')
        Property(abbrevCode='oac',
                 name='actNumber',
                 label='Act Number',
                 namespace='music21',
                 isContributor=False),

        # sceneNumber: scene number (e.g. '3' or 'Scene 3')
        Property(abbrevCode='osc',
                 name='sceneNumber',
                 label='Scene Number',
                 namespace='music21',
                 isContributor=False),

        # movementNumber: movement number (e.g. '4', or 'mov. 4', or...)
        Property(abbrevCode='omv',
                 name='movementNumber',
                 label='Movement Number',
                 namespace='music21',
                 isContributor=False),

        # movementName: movement name (often a tempo description)
        Property(abbrevCode='omd',
                 name='movementName',
                 label='Movement Name',
                 namespace='music21',
                 isContributor=False),

        # opusNumber: opus number (e.g. '23', or 'Opus 23')
        Property(abbrevCode='ops',
                 name='opusNumber',
                 label='Opus Number',
                 namespace='music21',
                 isContributor=False),

        # number: number (e.g. '5', or 'No. 5')
        Property(abbrevCode='onm',
                 name='number',
                 label='Number',
                 namespace='music21',
                 isContributor=False),

        # volume: volume number (e.g. '6' or 'Vol. 6')
        Property(abbrevCode='ovm',
                 name='volume',
                 label='Volume Number',
                 namespace='music21',
                 isContributor=False),

        # dedication: dedicated to
        Property(abbrevCode='ode',
                 name='dedication',
                 label='Dedicated To',
                 namespace='music21',
                 isContributor=False),

        # commission: commissioned by
        Property(abbrevCode='oco',
                 name='commission',
                 label='Commissioned By',
                 namespace='music21',
                 isContributor=False),

        # countryOfComposition: country of composition
        Property(abbrevCode='ocy',
                 name='countryOfComposition',
                 label='Country of Composition',
                 namespace='music21',
                 isContributor=False),

        # localeOfComposition: city, town, or village of composition
        Property(abbrevCode='opc',
                 name='localeOfComposition',
                 label='Locale of Composition',
                 namespace='music21',
                 isContributor=False),

        # groupTitle: group title (e.g. 'The Seasons')
        Property(abbrevCode='gtl',
                 name='groupTitle',
                 label='Group Title',
                 namespace='music21',
                 isContributor=False),

        # associatedWork: associated work, such as a play or film
        Property(abbrevCode='gaw',
                 name='associatedWork',
                 label='Associated Work',
                 namespace='music21',
                 isContributor=False),

        # collectionDesignation: This is a free-form text record that can be used to
        #   identify a collection of pieces, such as works appearing in a compendium
        #   or anthology. E.g. Norton Scores, Smithsonian Collection, Burkhart Anthology.
        Property(abbrevCode='gco',
                 name='collectionDesignation',
                 label='Collection Designation',
                 namespace='music21',
                 isContributor=False),

        # attributedComposer: attributed composer
        Property(abbrevCode='coa',
                 name='attributedComposer',
                 label='Attributed Composer',
                 namespace='music21',
                 isContributor=True),

        # suspectedComposer: suspected composer
        Property(abbrevCode='cos',
                 name='suspectedComposer',
                 label='Suspected Composer',
                 namespace='music21',
                 isContributor=True),

        # composerAlias: composer's abbreviated, alias, or stage name
        Property(abbrevCode='col',
                 name='composerAlias',
                 label='Composer Alias',
                 namespace='music21',
                 isContributor=True),

        # composerCorporate: composer's corporate name
        Property(abbrevCode='coc',
                 name='composerCorporate',
                 label='Composer Corporate Name',
                 namespace='music21',
                 isContributor=True),

        # orchestrator: orchestrator
        Property(abbrevCode='lor',
                 name='orchestrator',
                 label='Orchestrator',
                 namespace='music21',
                 isContributor=True),
    )

    NSKEY2STDPROPERTY: dict = {f'{x.namespace}:{x.name}':x for x in STDPROPERTIES}

    CODE2NSKEY:      dict = {x[0]:f'{x.namespace}:{x.name}' for x in STDPROPERTIES}
    NAME2NSKEY:      dict = {x[1]:f'{x.namespace}:{x.name}' for x in STDPROPERTIES}

    M21ABBREV2NSKEY: dict = {x.m21Abbrev if x.m21Abbrev
                                else x.abbrevCode if x.namespace=='music21'
                                else None # shouldn't ever happen due to condition below
                             :
                             f'{x.namespace}:{x.name}'
                                for x in STDPROPERTIES
                                    if x.m21Abbrev or x.namespace=='music21'}

    M21WORKID2NSKEY: dict = {x.m21WorkId if x.m21WorkId
                                else x.name if x.namespace=='music21'
                                else None # shouldn't ever happen due to condition below
                                :
                                f'{x.namespace}:{x.name}'
                                    for x in STDPROPERTIES
                                        if x.m21WorkId or x.namespace=='music21'}

    STDPROPERTY_CODES:   Tuple[str, ...] = tuple(x.abbrevCode for x in STDPROPERTIES)
    STDPROPERTY_NAMES:   Tuple[str, ...] = tuple(x.name for x in STDPROPERTIES)


    # Someday allow any new property code vocab to be specified, both property codes/names
    # and implied (or specified) encoding types.  Take a look at MEI to see what might be needed.
    # Hopefully this is where "humdrum:XXX" codes will go.

    # The parsers themselves are the ones responsible for putting together the
    # Dublin Core metadata plus their own ("here's some better stuff that got
    # lost during translation to Dublin Core").

    # INITIALIZER #
    def __init__(self):
        # for now (experimental) use 'namespace:name' for key, and either a single value
        # or a list (for more than one value).

        # Where original metadata could contain multiples of various contributor roles,
        # this new metadata will be able to store multiple of any property.

        # Values (whether in a list or not) can also be dictionaries, where the keys
        # are either DublinCore property keys, or our own ('music21') keys, (for
        # example, for contributor roles).
        # TODO: I do not yet have a way to differentiate between two composers vs two
        # TODO: translations of one composer's name (same for all other properties)

        super().__init__()
        self._metadata: Dict = {}
        self.software: List[str] = [defaults.software]

    @staticmethod
    def nsKey(key: str, namespace: Optional[str] = None) -> str:
        if namespace:
            return f'{namespace}:{key}'

        if key in MetadataBase.NAME2NSKEY:
            return MetadataBase.NAME2NSKEY[key]

        if key in MetadataBase.CODE2NSKEY:
            return MetadataBase.CODE2NSKEY[key]

#         if key in MetadataBase.UNIQUENAME2NSKEY:
#             return MetadataBase.UNIQUENAME2NSKEY[key]

        # it might already be of the form 'namespace:name', or it might
        # be a personal name, so just return it.
        return key

    @staticmethod
    def propertyDefinitionToNSKey(prop: Property) -> str:
        return MetadataBase.nsKey(prop.name, prop.namespace)

    @staticmethod
    def nsKeyToPropertyDefinition(nsKey: str) -> Property:
        if not nsKey:
            return None
        return MetadataBase.NSKEY2STDPROPERTY.get(nsKey, None)

    @staticmethod
    def isContributorNSKey(nsKey: str) -> bool:
        prop: Property = MetadataBase.NSKEY2STDPROPERTY.get(nsKey, None)
        if prop is None:
            return False
        return prop.isContributor and (prop.namespace == 'music21' or prop.m21WorkId is not None)

    @staticmethod
    def nsKeyToContributorRole(nsKey: str) -> str:
        prop: Property = MetadataBase.NSKEY2STDPROPERTY.get(nsKey, None)
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
            # it maps to a big-C Contributor role, which can be found in prop.m21WorkId.
            return prop.m21WorkId

        # it's a small-c contributor that doesn't map to a big-C Contributor role
        return None

    @staticmethod
    def contributorRoleToNSKey(role: str) -> str:
        nsKey: str = MetadataBase.M21WORKID2NSKEY.get(role, None)
        if nsKey is None:
            return None

        prop: Property = MetadataBase.NSKEY2STDPROPERTY.get(nsKey, None)
        if prop is None:
            return None

        if not prop.isContributor:
            return None

        return nsKey

    # if namespace is provided, key should be name or abbrevCode (within that namespace)
    # if namespace is None, key should be uniqueName or 'namespace:name', or personalName
    def _getItem(self,
                 key: str,
                 namespace: Optional[str] = None) -> Optional[Union[Text, DateSingle, dict]]:
        nsKey: str = self.nsKey(key, namespace)
        return self._metadata.get(nsKey, None)

    # if namespace is provided, key should be name or abbrevCode (within that namespace)
    # if namespace is None, key should be uniqueName or 'namespace:name', or personalName
    def _addItem(self,
                 key: str,
                 value: Union[Text, DateSingle, str, dict],
                 namespace: Optional[str] = None):
        if isinstance(value, str):
            value = Text(value)

        nsKey: str = self.nsKey(key, namespace)

        prevValue: Union[List, Text, DateSingle, str, dict]
        prevValue = self._metadata.get(nsKey, None)
        if prevValue is None:
            # set a single value
            self._metadata[nsKey] = value
        elif isinstance(prevValue, list):
            # add value to the list
            prevValue.append(value)
        else:
            # overwrite prevValue with a list containing prevValue and value
            self._metadata[nsKey] = [prevValue, value]

    # if namespace is provided, key should be name or abbrevCode (within that namespace)
    # if namespace is None, key should be uniqueName or 'namespace:name', or personalName
    def _setItem(self,
                 key: str,
                 value: Union[Text, DateSingle, str, dict],
                 namespace: Optional[str] = None):
        nsKey: str = self.nsKey(key, namespace)
        self._metadata.pop(nsKey, None)
        self._addItem(key, value, namespace)

    def _addContributor(self, c: Contributor):
        nsKey: str = self.contributorRoleToNSKey(c.role)
        if not nsKey:
            return
        # TODO: when I support multiple names for one contributor,
        # TODO: here is where I will add everything in c.names.
        self._addItem(nsKey, c.names[0])

    def _getAllContributorsAsNSKeysAndValues(self) -> List[Tuple[str, Union[Text, Date]]]:
        allOut: List[Tuple[str, Union[Text, DateSingle]]] = []

        for nsKey, value in self._metadata.items():
            if not self.isContributorNSKey(nsKey):
                continue

            if not value:
                continue

            if isinstance(value, list):
                for v in value:
                    allOut.append( (nsKey, v) )
            else:
                allOut.append( (nsKey, value) )

        return allOut

# -----------------------------------------------------------------------------

# Metadata is the backward-compatible interface for metadata
class Metadata(MetadataBase):
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

    def __init__(self, **keywords):
        # for now (experimental) use 'namespace:name' for key, and either a single value
        # or a list (for more than one value).

        # Where original metadata could contain multiples of various contributor roles,
        # this new metadata will be able to store multiple of any property.

        # Values (whether in a list or not) can also be dictionaries, where the keys
        # are either DublinCore property keys, or our own ('music21') keys, (for
        # example, for contributor roles).
        # TODO: I do not yet have a way to differentiate between two composers vs two
        # TODO: translations of one composer's name (same for all other properties)

        super().__init__()

        # For backward compatibility, we allow the setting of workIds or
        # abbreviations via **keywords
        for abbreviation, workId in self.workIdAbbreviationDict.items():
            # abbreviation = workIdToAbbreviation(id)
            if workId in keywords:
                nsKey: str = MetadataBase.M21WORKID2NSKEY[workId]
                self._metadata[nsKey] = Text(keywords[workId])
            elif abbreviation in keywords:
                nsKey: str = MetadataBase.M21ABBREV2NSKEY[abbreviation]
                self._metadata[nsKey] = Text(keywords[abbreviation])

        # search for any keywords that match attributes
        # these are for direct Contributor access, must have defined
        # properties
        for attr in ['composer', 'date', 'title']:
            if attr in keywords:
                setattr(self, attr, keywords[attr])


    # Here are some old APIs, implemented in terms of the new data structures
    # for backward compatibility

    def _getBackwardCompatibleItemNoConversion(self, workId: str) -> str:
        result: List[Any] = self._getBackwardCompatibleItemsNoConversion(workId)
        if not result: # None or empty list
            return None
        return result[0]

    def _getBackwardCompatibleItem(self, workId: str) -> str:
        return str(self._getBackwardCompatibleItemNoConversion(workId))

    def _addBackwardCompatibleItem(self, workId: str, value: Union[str, Text, DateSingle]):
        nsKey: str = MetadataBase.M21WORKID2NSKEY.get(workId, None)
        if nsKey is not None:
            self._addItem(nsKey, value)

    def _setBackwardCompatibleItem(self, workId: str, value: Union[str, Text, DateSingle]):
        nsKey: str = MetadataBase.M21WORKID2NSKEY.get(workId, None)
        if nsKey is not None:
            self._setItem(nsKey, value)

    def _getBackwardCompatibleItemsNoConversion(self, workId: str) -> List[Any]:
        nsKey: str = MetadataBase.M21WORKID2NSKEY.get(workId, None)
        if nsKey is None:
            return None

        result = self._getItem(nsKey)
        if result is None:
            return None

        if not isinstance(result, list):
            result = [result]

        return result

    def _getBackwardCompatibleItems(self, workId: str) -> List[str]:
        output: List[str] = []
        values: List[Any] = self._getBackwardCompatibleItemsNoConversion(workId)
        for v in values:
            output.append(str(v))
        return output

    def _setBackwardCompatibleItems(self, workId: str, names: List[str]):
        values: List[Text] = []
        for name in names:
            values.append(Text(name))
        self._setBackwardCompatibleItem(workId, values)

    @property
    def contributors(self) -> List[Contributor]:
        # This was just a data attribute before.  Hopefully no-one is calling
        # md.contributors.append(c).  I did a global search on github for
        # 'music21' 'contributors', and all code that modified it that I found
        # were in music21 forks.  So I think we're OK making this a read-only
        # property that we generate on the fly.
        output: List[Contributor] = []
        for nsKey, value in self._metadata.items():
            role: str = MetadataBase.nsKeyToContributorRole(nsKey)
            if role is None:
                # That nsKey wasn't a Contributor (in the backward compatibility sense)
                continue

            # TODO: Once we start storing multiple names per _metadata item (and maybe
            # TODO: even birth and death dates for contributor _metadata items), we
            # TODO: should set them here via:
            # TODO:     Contributor(names=[name1, name2], birth='1855', death=DateSingle('1923'))

            # for now we assume the value is something like Text('Ludwig von Beethoven')
            contrib: Contributor = Contributor(role=role, name=value)
            output.append(contrib)
        return output

    # This was just a data attribute before that could be set/get directly to anything.
    # There was hope of changing that to convert to Copyright during set, but I won't
    # do that yet, so I don't trigger any backward compatibility issues.  Here's the
    # original comment:
    # copyright can be None or a Copyright object
    # TODO: Change to property to prevent setting as a plain string
    #     (but need to regenerate CoreCorpus() after doing so.)
    @property
    def copyright(self) -> Copyright:
        return self._getBackwardCompatibleItemNoConversion('copyright')

    @copyright.setter
    def copyright(self, newCopyright: Union[str, Copyright]):
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
        @@@ NEEDS WORK (not needed for backward compatibility, as long as we
        we have all the property definitions, but maybe this is where we give
        uniqueNames to all the STDPROPERTIES, and instead of adding 100 new
        properties, just implement this properly)  Do we also need __setattr__?
        I think I remember some big issues trying to implement that.  Maybe we
        just lose this altogether and just define uniquenames that can be used
        without namespaces via getItem, setItem, addItem.
        '''
        raise AttributeError(f'why are you calling __getattr__?: {name}')
#         match = None
#         for abbreviation, workId in self.workIdAbbreviationDict.items():
#             # for id in WORK_IDS:
#             # abbreviation = workIdToAbbreviation(id)
#             if name == workId:
#                 match = workId
#                 break
#             elif name == abbreviation:
#                 match = workId
#                 break
#         if match is None:
#             raise AttributeError(f'object has no attribute: {name}')
#         result = self._workIds[match]
#         # always return string representation for now
#         return str(result)

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
        self._addContributor(c)

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


        >>> md.setWorkId('sdf', None)
        Traceback (most recent call last):
        music21.exceptions21.MetadataException: no work id available with id: sdf
        '''
        idStr = idStr.lower()
        match = False
        for abbreviation, workId in self.workIdAbbreviationDict.items():
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
        return self._getBackwardCompatibleItems('composer')

    @composers.setter
    def composers(self, value: List[str]) -> None:
        self._setBackwardCompatibleItems('composer', value)


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
        return self._getBackwardCompatibleItem('date')

    @date.setter
    def date(self, value):
        self._setBackwardCompatibleItem('date', value)
#         # all inherit date single
#         if isinstance(value, DateSingle):
#             self._date = value
#         else:
#             # assume date single; could be other subclass
#             ds = DateSingle(value)
#             self._date = ds

    @property
    def localeOfComposition(self):
        r'''
        Get or set the locale of composition, or origin, of the work.
        '''
        return self._getBackwardCompatibleItem('localeOfComposition')

    @localeOfComposition.setter
    def localeOfComposition(self, value):
        self._setBackwardCompatibleItem('localeOfComposition', value)

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
        return self._contributor_role_getter('librettist')

    @librettist.setter
    def librettist(self, value):
        self._addBackwardCompatibleItem('librettist', value)

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
        return self._getBackwardCompatibleContributorName('lyricist')

    @lyricist.setter
    def lyricist(self, value):
        self._addBackwardCompatibleItem('lyricist', value)

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
        result = self._getBackwardCompatibleItem('movementName')
        if result is not None:
            return str(result)

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
        self._setBackwardCompatibleItem('movementNumber', value)

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
        self._setBackwardCompatibleItem('number', value)

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
        self._setBackwardCompatibleItem('opusNumber', value)

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
        self._setBackwardCompatibleItem('title', value)

# -----------------------------------------------------------------------------

class ExtendedMetadata(Metadata):
    # TODO: Should we allow **keywords initialization of ExtendedMetadata?
    # TODO: We could allow keys that are uniqueName or 'namespace:name', but
    # TODO: not personalName (if we allow personalName, that would be any name
    # TODO: at all)
    def __init__(self, metadata=None):
        super().__init__() # sets up default software and empty _metadata

        if metadata is not None:
            # This is a conversion (from Metadata or from ExtendedMetadata).
            # In all cases it must be a copy operation. We can't have two
            # metadata objects that share instance data!
            self.software = copy.deepcopy(metadata.software)
            self._metadata = copy.deepcopy(metadata._metadata)

    # if namespace is provided, key should be name or abbrevCode (within that namespace)
    # if namespace is None, key should be uniqueName or 'namespace:name', or personalName
    def getItem(self,
                key: str,
                namespace: Optional[str] = None) -> Optional[Any]:
        return self._getItem(key, namespace)

    # if namespace is provided, key should be name or abbrevCode (within that namespace)
    # if namespace is None, key should be uniqueName or 'namespace:name', or personalName
    def addItem(self,
                key: str,
                value: Any,
                namespace: Optional[str] = None):
        self._addItem(key, value, namespace)

    # if namespace is provided, key should be name or abbrevCode (within that namespace)
    # if namespace is None, key should be uniqueName or 'namespace:name', or personalName
    def setItem(self,
                key: str,
                value: Any,
                namespace: Optional[str] = None):
        self._setItem(key, value, namespace)

    def getPersonalItem(self, key: str) -> Any:
        # uniqueNames and standard property nsKeys are reserved.
        # You can use nonstandard nsKeys like 'humdrum:XXX' though.
        if key in MetadataBase.NSKEY2STDPROPERTY:
            return None
# TODO: implement uniqueNames for all std properties
#         if key in MetadataBase.UNIQUENAME2STDPROPERTY:
#             return None
        return self._getItem(key, namespace=None)

    def addPersonalItem(self, key: str, value: Union[Text, DateSingle, str, dict]):
        # uniqueNames and standard property nsKeys are reserved.
        # You can use nonstandard nsKeys like 'humdrum:XXX' though.
        if key in MetadataBase.NSKEY2STDPROPERTY:
            raise KeyError
# TODO: implement uniqueNames for all std properties
#         if key in MetadataBase.UNIQUENAME2STDPROPERTY:
#             raise KeyError
        self._addItem(key, value, namespace=None)

    def setPersonalItem(self, key: str, value: Union[Text, DateSingle, str, dict]):
        # uniqueNames and standard property nsKeys are reserved.
        # You can use nonstandard nsKeys like 'humdrum:XXX' though.
        if key in MetadataBase.NSKEY2STDPROPERTY:
            raise KeyError
# TODO: implement uniqueNames for all std properties
#         if key in MetadataBase.UNIQUENAME2STDPROPERTY:
#             raise KeyError
        self._setItem(key, value, namespace=None)

    # This is the extended version of all().  The tuple's key is an nsKey (but of course
    # there may be no namespace for personal metadata items).
    def getAllItems(self, skipContributors=False) -> List[Tuple[str, Any]]:
        '''
        Returns all values stored in this metadata as a list of (nsKey, value) tuples.
        Items in the metadata that have a list of values are flattened into the output
        list as multiple tuples with the same nsKey.
        '''
        allOut: List[Tuple[str, Union[Text, DateSingle]]] = []

        for nsKey, value in self._metadata.items():
            if skipContributors and self.isContributorNSKey(nsKey):
                continue

            if not value:
                continue

            if isinstance(value, list):
                for v in value:
                    allOut.append( (nsKey, v) )
            else:
                allOut.append( (nsKey, value) )

        # Metadata sorts here, but when I'm doing passthru export, it's nice to
        # have the order in the output file be the same as the order in the input
        # file. If sorting is intereresting, though, I can add a sorted param that
        # defaults to False.  Not sure what to sort by: by namespace and then by name
        # within that namespace?  By uniqueName?
        return allOut

# -----------------------------------------------------------------------------

# TODO: RichMetadata hasn't been modified beyond deriving it from ExtendedMetadata
# TODO: in anticipation of enhancing the rich metadata.  For now it depends on
# TODO: backward compatibility, and doesn't do anything that non-extended metadata
# TODO: APIs can't do.
# TODO: Well, crap, RichMetadata looks inside Metadata's internals (e.g. _workIds),
# TODO: so it will need to be re-implemented a bit.
class RichMetadata(ExtendedMetadata):
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
            'contributors', '_date', '_urls', '_imprint', 'copyright',
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
