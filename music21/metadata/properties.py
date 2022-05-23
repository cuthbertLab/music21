# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         properties.py
# Purpose:      Data describing the standard set of metadata properties
#
# Authors:      Greg Chapman
#               Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2022 Michael Scott Asato Cuthbert and the music21
#               Project
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------

import typing as t
from dataclasses import dataclass

from music21.metadata.primitives import (Date, DateSingle, DateRelative, DateBetween,
                                         DateSelection, Text, Contributor, Creator,
                                         Imprint, Copyright)


@dataclass
class PropertyDescription:
    '''
        Describes a single standard metadata property.

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
    '''
    abbrevCode: t.Optional[str] = None
    name: t.Optional[str] = None
    label: t.Optional[str] = None
    namespace: t.Optional[str] = None
    isContributor: t.Optional[bool] = None
    m21Abbrev: t.Optional[str] = None
    m21WorkId: t.Optional[str] = None
    uniqueName: t.Optional[str] = None
    valueType: t.Type = Text

STANDARD_PROPERTY_DESCRIPTIONS: t.Tuple[PropertyDescription, ...] = (
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
        m21WorkId='date',
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
        uniqueName='otherDate',
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
