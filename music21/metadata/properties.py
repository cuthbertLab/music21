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

from music21.metadata.primitives import (DateSingle, Text, Contributor, Copyright)


@dataclass
class PropertyDescription:
    '''
        Describes a single standard metadata property.

        name: str is the namespace's name of the property (the tail of the property term URI).
        namespace: str is a shortened form of the URI for the set of terms.
            e.g. 'dcterms' means the property term is from the Dublin Core terms.
            'dcterms' is the shortened form of <http://purl.org/dc/terms/>
            e.g. 'marcrel' means the property term is from the MARC Relator terms.
            'marcrel' is the shortened form of <http://www.loc.gov/loc.terms/relators/>
        isContributor: bool is whether or not the property describes a contributor.
        oldMusic21Abbrev: str is the backward compatible music21 abbreviation for this
            property.
        oldMusic21WorkId: str is the backward compatible music21 name for this property.
            Note that we use oldMusic21WorkId for music21 contributor roles when necessary,
            as well.
        uniqueName: str is the official music21 name for this property, that is unique
            within the list of properties. There is always a unique name, but the
            uniqueName field is only set if oldMusic21WorkId or name is not unique enough.
            To get the unique name from a particular PropertyDescription, we do:
                (desc.uniqueName if desc.uniqueName
                    else desc.oldMusic21WorkId if desc.oldMusic21WorkId
                    else desc.name)
        valueType: Type is the actual type of the value that will be stored in the metadata.
            This allows auto-conversion to take place inside set/add, and is
            the type clients will always receive from get.

    '''
    name: t.Optional[str] = None
    namespace: t.Optional[str] = None
    isContributor: bool = False
    oldMusic21Abbrev: t.Optional[str] = None
    oldMusic21WorkId: t.Optional[str] = None
    uniqueName: t.Optional[str] = None
    valueType: t.Type = Text


STANDARD_PROPERTY_DESCRIPTIONS: t.Tuple[PropertyDescription, ...] = (
    # The following 'dcterms' properties are the standard Dublin Core property terms
    # found at http://purl.org/dc/terms/

    # abstract: A summary of the resource.
    PropertyDescription(
        name='abstract',
        namespace='dcterms',
        isContributor=False),

    # accessRights: Information about who access the resource or an indication of
    #   its security status.
    PropertyDescription(
        name='accessRights',
        namespace='dcterms',
        isContributor=False),

    # accrualMethod: The method by which items are added to a collection.
    PropertyDescription(
        name='accrualMethod',
        namespace='dcterms',
        isContributor=False),

    # accrualPeriodicity: The frequency with which items are added to a collection.
    PropertyDescription(
        name='accrualPeriodicity',
        namespace='dcterms',
        isContributor=False),

    # accrualPolicy: The policy governing the addition of items to a collection.
    PropertyDescription(
        name='accrualPolicy',
        namespace='dcterms',
        isContributor=False),

    # alternative: An alternative name for the resource.
    PropertyDescription(
        name='alternative',
        namespace='dcterms',
        oldMusic21Abbrev='ota',
        oldMusic21WorkId='alternativeTitle',
        isContributor=False),

    # audience: A class of agents for whom the resource is intended or useful.
    PropertyDescription(
        name='audience',
        namespace='dcterms',
        isContributor=False),

    # available: Date that the resource became or will become available.
    PropertyDescription(
        name='available',
        namespace='dcterms',
        uniqueName='dateAvailable',
        valueType=DateSingle,   # including DateRelative, DateBetween, DateSelection
        isContributor=False),

    # bibliographicCitation: A bibliographic reference for the resource.
    PropertyDescription(
        name='bibliographicCitation',
        namespace='dcterms',
        isContributor=False),

    # conformsTo: An established standard to which the described resource conforms.
    PropertyDescription(
        name='conformsTo',
        namespace='dcterms',
        isContributor=False),

    # contributor: An entity responsible for making contributions to the resource.
    # NOTE: You should use one of the 'marcrel' properties below instead, since
    # this property is very vague. The 'marcrel' properties are considered to be
    # refinements of dcterms:contributor (this property).
    PropertyDescription(
        name='contributor',
        namespace='dcterms',
        uniqueName='genericContributor',
        valueType=Contributor,
        isContributor=True),

    # coverage: The spatial or temporal topic of the resource, spatial applicability
    #   of the resource, or jurisdiction under which the resource is relevant.
    PropertyDescription(
        name='coverage',
        namespace='dcterms',
        isContributor=False),

    # created: Date of creation of the resource.
    PropertyDescription(
        name='created',
        namespace='dcterms',
        oldMusic21WorkId='date',
        uniqueName='dateCreated',
        valueType=DateSingle,   # including DateRelative, DateBetween, DateSelection
        isContributor=False),

    # creator: An entity responsible for making the resource.
    PropertyDescription(
        name='creator',
        namespace='dcterms',
        valueType=Contributor,
        isContributor=True),

    # date: A point or period of time associated with an event in the lifecycle
    #   of the resource.
    PropertyDescription(
        name='date',
        namespace='dcterms',
        uniqueName='otherDate',
        valueType=DateSingle,   # including DateRelative, DateBetween, DateSelection
        isContributor=False),

    # dateAccepted: Date of acceptance of the resource.
    PropertyDescription(
        name='dateAccepted',
        namespace='dcterms',
        valueType=DateSingle,   # including DateRelative, DateBetween, DateSelection
        isContributor=False),

    # dateCopyrighted: Date of copyright of the resource.
    PropertyDescription(
        name='dateCopyrighted',
        namespace='dcterms',
        valueType=DateSingle,   # including DateRelative, DateBetween, DateSelection
        isContributor=False),

    # dateSubmitted: Date of submission of the resource.
    PropertyDescription(
        name='dateSubmitted',
        namespace='dcterms',
        valueType=DateSingle,   # including DateRelative, DateBetween, DateSelection
        isContributor=False),

    # description: An account of the resource.
    PropertyDescription(
        name='description',
        namespace='dcterms',
        isContributor=False),

    # educationLevel: A class of agents, defined in terms of progression
    #   through an educational or training context, for which the described
    #   resource is intended.
    PropertyDescription(
        name='educationLevel',
        namespace='dcterms',
        isContributor=False),

    # extent: The size or duration of the resource.
    PropertyDescription(
        name='extent',
        namespace='dcterms',
        isContributor=False),

    # format: The file format, physical medium, or dimensions of the resource.
    PropertyDescription(
        name='format',
        namespace='dcterms',
        isContributor=False),

    # hasFormat: A related resource that is substantially the same as the
    #   pre-existing described resource, but in another format.
    PropertyDescription(
        name='hasFormat',
        namespace='dcterms',
        isContributor=False),

    # hasPart: A related resource that is included either physically or
    #   logically in the described resource.
    PropertyDescription(
        name='hasPart',
        namespace='dcterms',
        isContributor=False),

    # hasVersion: A related resource that is a version, edition, or adaptation
    #   of the described resource.
    PropertyDescription(
        name='hasVersion',
        namespace='dcterms',
        isContributor=False),

    # identifier: An unambiguous reference to the resource within a given context.
    PropertyDescription(
        name='identifier',
        namespace='dcterms',
        isContributor=False),

    # instructionalMethod: A process, used to engender knowledge, attitudes and
    #   skills, that the described resource is designed to support.
    PropertyDescription(
        name='instructionalMethod',
        namespace='dcterms',
        isContributor=False),

    # isFormatOf: A pre-existing related resource that is substantially the same
    #   as the described resource, but in another format.
    PropertyDescription(
        name='isFormatOf',
        namespace='dcterms',
        isContributor=False),

    # isPartOf: A related resource in which the described resource is physically
    #   or logically included.
    PropertyDescription(
        name='isPartOf',
        namespace='dcterms',
        isContributor=False),

    # isReferencedBy: A related resource that references, cites, or otherwise
    #   points to the described resource.
    PropertyDescription(
        name='isReferencedBy',
        namespace='dcterms',
        isContributor=False),

    # isReplacedBy: A related resource that supplants, displaces, or supersedes
    #   the described resource.
    PropertyDescription(
        name='isReplacedBy',
        namespace='dcterms',
        isContributor=False),

    # isRequiredBy: A related resource that requires the described resource
    #   to support its function, delivery, or coherence.
    PropertyDescription(
        name='isRequiredBy',
        namespace='dcterms',
        isContributor=False),

    # issued: Date of formal issuance of the resource.
    PropertyDescription(
        name='issued',
        namespace='dcterms',
        uniqueName='dateIssued',
        valueType=DateSingle,   # including DateRelative, DateBetween, DateSelection
        isContributor=False),

    # isVersionOf: A related resource of which the described resource is a
    #   version, edition, or adaptation.
    PropertyDescription(
        name='isVersionOf',
        namespace='dcterms',
        isContributor=False),

    # language: A language of the resource.
    PropertyDescription(
        name='language',
        namespace='dcterms',
        isContributor=False),

    # license: A legal document giving official permission to do something
    #   with the resource.
    PropertyDescription(
        name='license',
        namespace='dcterms',
        isContributor=False),

    # mediator: An entity that mediates access to the resource.
    PropertyDescription(
        name='mediator',
        namespace='dcterms',
        isContributor=False),

    # medium: The material or physical carrier of the resource.
    PropertyDescription(
        name='medium',
        namespace='dcterms',
        isContributor=False),

    # modified: Date on which the resource was changed.
    PropertyDescription(
        name='modified',
        namespace='dcterms',
        uniqueName='dateModified',
        valueType=DateSingle,   # including DateRelative, DateBetween, DateSelection
        isContributor=False),

    # provenance: A statement of any changes in ownership and custody of
    #   the resource since its creation that are significant for its
    #   authenticity, integrity, and interpretation.
    PropertyDescription(
        name='provenance',
        namespace='dcterms',
        isContributor=False),

    # publisher: An entity responsible for making the resource available.
    PropertyDescription(
        name='publisher',
        namespace='dcterms',
        valueType=Contributor,
        isContributor=True),

    # references: A related resource that is referenced, cited, or
    #   otherwise pointed to by the described resource.
    PropertyDescription(
        name='references',
        namespace='dcterms',
        isContributor=False),

    # relation: A related resource.
    PropertyDescription(
        name='relation',
        namespace='dcterms',
        isContributor=False),

    # replaces: A related resource that is supplanted, displaced, or
    #   superseded by the described resource.
    PropertyDescription(
        name='replaces',
        namespace='dcterms',
        isContributor=False),

    # requires: A related resource that is required by the described
    #   resource to support its function, delivery, or coherence.
    PropertyDescription(
        name='requires',
        namespace='dcterms',
        isContributor=False),

    # rights: Information about rights held in and over the resource.
    PropertyDescription(
        name='rights',
        namespace='dcterms',
        oldMusic21WorkId='copyright',
        valueType=Copyright,
        isContributor=False),

    # rightsHolder: A person or organization owning or managing rights
    #   over the resource.
    PropertyDescription(
        name='rightsHolder',
        namespace='dcterms',
        valueType=Contributor,
        isContributor=True),

    # source: A related resource from which the described resource
    #   is derived.
    PropertyDescription(
        name='source',
        namespace='dcterms',
        isContributor=False),

    # spatial: Spatial characteristics of the resource.
    PropertyDescription(
        name='spatial',
        namespace='dcterms',
        uniqueName='spatialCoverage',
        isContributor=False),

    # subject: A topic of the resource.
    PropertyDescription(
        name='subject',
        namespace='dcterms',
        isContributor=False),

    # tableOfContents: A list of subunits of the resource.
    PropertyDescription(
        name='tableOfContents',
        namespace='dcterms',
        isContributor=False),

    # temporal: Temporal characteristics of the resource.
    PropertyDescription(
        name='temporal',
        namespace='dcterms',
        uniqueName='temporalCoverage',
        isContributor=False),

    # title: A name given to the resource.
    PropertyDescription(
        name='title',
        namespace='dcterms',
        oldMusic21Abbrev='otl',
        oldMusic21WorkId='title',
        isContributor=False),

    # type : The nature or genre of the resource.
    PropertyDescription(
        name='type',
        namespace='dcterms',
        isContributor=False),

    # valid: Date (often a range) of validity of a resource.
    PropertyDescription(
        name='valid',
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
        name='ACT',
        namespace='marcrel',
        uniqueName='actor',
        valueType=Contributor,
        isContributor=True),

    # ADP/Adapter: a person or organization who 1) reworks a musical composition,
    #   usually for a different medium, or 2) rewrites novels or stories
    #   for motion pictures or other audiovisual medium.
    PropertyDescription(
        name='ADP',
        namespace='marcrel',
        uniqueName='adapter',
        valueType=Contributor,
        isContributor=True),

    # ANM/Animator: a person or organization who draws the two-dimensional
    #   figures, manipulates the three dimensional objects and/or also
    #   programs the computer to move objects and images for the purpose
    #   of animated film processing.
    PropertyDescription(
        name='ANM',
        namespace='marcrel',
        uniqueName='animator',
        valueType=Contributor,
        isContributor=True),

    # ANN/Annotator: a person who writes manuscript annotations on a printed item.
    PropertyDescription(
        name='ANN',
        namespace='marcrel',
        uniqueName='annotator',
        valueType=Contributor,
        isContributor=True),

    # ARC/Architect: a person or organization who designs structures or oversees
    #   their construction.
    PropertyDescription(
        name='ARC',
        namespace='marcrel',
        uniqueName='architect',
        valueType=Contributor,
        isContributor=True),

    # ARR/Arranger: a person or organization who transcribes a musical
    #   composition, usually for a different medium from that of the original;
    #   in an arrangement the musical substance remains essentially unchanged.
    PropertyDescription(
        name='ARR',
        namespace='marcrel',
        oldMusic21WorkId='arranger',
        valueType=Contributor,
        isContributor=True),

    # ART/Artist: a person (e.g., a painter) or organization who conceives, and
    #   perhaps also implements, an original graphic design or work of art, if
    #   specific codes (e.g., [egr], [etr]) are not desired. For book illustrators,
    #   prefer Illustrator [ill].
    PropertyDescription(
        name='ART',
        namespace='marcrel',
        uniqueName='artist',
        valueType=Contributor,
        isContributor=True),

    # AUT/Author: a person or organization chiefly responsible for the
    #   intellectual or artistic content of a work, usually printed text.
    PropertyDescription(
        name='AUT',
        namespace='marcrel',
        uniqueName='author',
        valueType=Contributor,
        isContributor=True),

    # AQT/Author in quotations or text extracts: a person or organization
    #   whose work is largely quoted or extracted in works to which he or
    #   she did not contribute directly.
    PropertyDescription(
        name='AQT',
        namespace='marcrel',
        uniqueName='quotationsAuthor',
        valueType=Contributor,
        isContributor=True),

    # AFT/Author of afterword, colophon, etc.: a person or organization
    #   responsible for an afterword, postface, colophon, etc. but who
    #   is not the chief author of a work.
    PropertyDescription(
        name='AFT',
        namespace='marcrel',
        uniqueName='afterwordAuthor',
        valueType=Contributor,
        isContributor=True),

    # AUD/Author of dialog: a person or organization responsible for
    #   the dialog or spoken commentary for a screenplay or sound
    #   recording.
    PropertyDescription(
        name='AUD',
        namespace='marcrel',
        uniqueName='dialogAuthor',
        valueType=Contributor,
        isContributor=True),

    # AUI/Author of introduction, etc.:  a person or organization
    #   responsible for an introduction, preface, foreword, or other
    #   critical introductory matter, but who is not the chief author.
    PropertyDescription(
        name='AUI',
        namespace='marcrel',
        uniqueName='introductionAuthor',
        valueType=Contributor,
        isContributor=True),

    # AUS/Author of screenplay, etc.:  a person or organization responsible
    #   for a motion picture screenplay, dialog, spoken commentary, etc.
    PropertyDescription(
        name='AUS',
        namespace='marcrel',
        uniqueName='screenplayAuthor',
        valueType=Contributor,
        isContributor=True),

    # CLL/Calligrapher: a person or organization who writes in an artistic
    #   hand, usually as a copyist and or engrosser.
    PropertyDescription(
        name='CLL',
        namespace='marcrel',
        uniqueName='calligrapher',
        valueType=Contributor,
        isContributor=True),

    # CTG/Cartographer: a person or organization responsible for the
    #   creation of maps and other cartographic materials.
    PropertyDescription(
        name='CTG',
        namespace='marcrel',
        uniqueName='cartographer',
        valueType=Contributor,
        isContributor=True),

    # CHR/Choreographer: a person or organization who composes or arranges
    #   dances or other movements (e.g., "master of swords") for a musical
    #   or dramatic presentation or entertainment.
    PropertyDescription(
        name='CHR',
        namespace='marcrel',
        uniqueName='choreographer',
        valueType=Contributor,
        isContributor=True),

    # CNG/Cinematographer: a person or organization who is in charge of
    #   the images captured for a motion picture film. The cinematographer
    #   works under the supervision of a director, and may also be referred
    #   to as director of photography. Do not confuse with videographer.
    PropertyDescription(
        name='CNG',
        namespace='marcrel',
        uniqueName='cinematographer',
        valueType=Contributor,
        isContributor=True),

    # CLB/Collaborator: a person or organization that takes a limited part
    #   in the elaboration of a work of another person or organization that
    #   brings complements (e.g., appendices, notes) to the work.
    PropertyDescription(
        name='CLB',
        namespace='marcrel',
        uniqueName='collaborator',
        valueType=Contributor,
        isContributor=True),

    # CLT/Collotyper: a person or organization responsible for the production
    #   of photographic prints from film or other colloid that has ink-receptive
    #   and ink-repellent surfaces.
    PropertyDescription(
        name='CLT',
        namespace='marcrel',
        uniqueName='collotyper',
        valueType=Contributor,
        isContributor=True),

    # CMM/Commentator: a person or organization who provides interpretation,
    #   analysis, or a discussion of the subject matter on a recording,
    #   motion picture, or other audiovisual medium.
    PropertyDescription(
        name='CMM',
        namespace='marcrel',
        uniqueName='commentator',
        valueType=Contributor,
        isContributor=True),

    # CWT/Commentator for written text: a person or organization responsible
    #   for the commentary or explanatory notes about a text. For the writer
    #   of manuscript annotations in a printed book, use Annotator [ann].
    PropertyDescription(
        name='CWT',
        namespace='marcrel',
        uniqueName='writtenCommentator',
        valueType=Contributor,
        isContributor=True),

    # COM/Compiler: a person or organization who produces a work or
    #   publication by selecting and putting together material from the
    #   works of various persons or bodies.
    PropertyDescription(
        name='COM',
        namespace='marcrel',
        uniqueName='compiler',
        valueType=Contributor,
        isContributor=True),

    # CMP/Composer: a person or organization who creates a musical work,
    #   usually a piece of music in manuscript or printed form.
    PropertyDescription(
        name='CMP',
        namespace='marcrel',
        oldMusic21WorkId='composer',
        valueType=Contributor,
        isContributor=True),

    # CCP/Conceptor: a person or organization responsible for the original
    #   idea on which a work is based, this includes the scientific author
    #   of an audio-visual item and the conceptor of an advertisement.
    PropertyDescription(
        name='CCP',
        namespace='marcrel',
        uniqueName='conceptor',
        valueType=Contributor,
        isContributor=True),

    # CND/Conductor: a person who directs a performing group (orchestra,
    #   chorus, opera, etc.) in a musical or dramatic presentation or
    #   entertainment.
    PropertyDescription(
        name='CND',
        namespace='marcrel',
        uniqueName='conductor',
        valueType=Contributor,
        isContributor=True),

    # CSL/Consultant: a person or organization relevant to a resource, who
    #   is called upon for professional advice or services in a specialized
    #   field of knowledge or training.
    PropertyDescription(
        name='CSL',
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
        name='CSP',
        namespace='marcrel',
        uniqueName='projectConsultant',
        valueType=Contributor,
        isContributor=True),

    # CTR/Contractor: a person or organization relevant to a resource, who
    #   enters into a contract with another person or organization to
    #   perform a specific task.
    PropertyDescription(
        name='CTR',
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
        name='CTB',
        namespace='marcrel',
        uniqueName='otherContributor',  # more specific than 'genericContributor'
        valueType=Contributor,
        isContributor=True),

    # CRP/Correspondent: a person or organization who was either
    #   the writer or recipient of a letter or other communication.
    PropertyDescription(
        name='CRP',
        namespace='marcrel',
        uniqueName='correspondent',
        valueType=Contributor,
        isContributor=True),

    # CST/Costume designer: a person or organization who designs
    #   or makes costumes, fixes hair, etc., for a musical or
    #   dramatic presentation or entertainment.
    PropertyDescription(
        name='CST',
        namespace='marcrel',
        uniqueName='costumeDesigner',
        valueType=Contributor,
        isContributor=True),

    # We already have 'dcterms:creator', so we won't use the marcrel equivalent
    # CRE/Creator: a person or organization responsible for the
    #   intellectual or artistic content of a work.
    #         PropertyDescription(
    #             name='CRE',
    #             namespace='marcrel',
    #             uniqueName='creator',
    #             valueType=Contributor,
    #             isContributor=True),

    # CUR/Curator of an exhibition: a person or organization
    #   responsible for conceiving and organizing an exhibition.
    PropertyDescription(
        name='CUR',
        namespace='marcrel',
        uniqueName='curator',
        valueType=Contributor,
        isContributor=True),

    # DNC/Dancer: a person or organization who principally
    #   exhibits dancing skills in a musical or dramatic
    #   presentation or entertainment.
    PropertyDescription(
        name='DNC',
        namespace='marcrel',
        uniqueName='dancer',
        valueType=Contributor,
        isContributor=True),

    # DLN/Delineator: a person or organization executing technical
    #   drawings from others' designs.
    PropertyDescription(
        name='DLN',
        namespace='marcrel',
        uniqueName='delineator',
        valueType=Contributor,
        isContributor=True),

    # DSR/Designer: a person or organization responsible for the design
    #   if more specific codes (e.g., [bkd], [tyd]) are not desired.
    PropertyDescription(
        name='DSR',
        namespace='marcrel',
        uniqueName='designer',
        valueType=Contributor,
        isContributor=True),

    # DRT/Director: a person or organization who is responsible for the
    #   general management of a work or who supervises the production of
    #   a performance for stage, screen, or sound recording.
    PropertyDescription(
        name='DRT',
        namespace='marcrel',
        uniqueName='director',
        valueType=Contributor,
        isContributor=True),

    # DIS/Dissertant: a person who presents a thesis for a university or
    #   higher-level educational degree.
    PropertyDescription(
        name='DIS',
        namespace='marcrel',
        uniqueName='dissertant',
        valueType=Contributor,
        isContributor=True),

    # DRM/Draftsman: a person or organization who prepares artistic or
    #   technical drawings.
    PropertyDescription(
        name='DRM',
        namespace='marcrel',
        uniqueName='draftsman',
        valueType=Contributor,
        isContributor=True),

    # EDT/Editor: a person or organization who prepares for publication
    #   a work not primarily his/her own, such as by elucidating text,
    #   adding introductory or other critical matter, or technically
    #   directing an editorial staff.
    PropertyDescription(
        name='EDT',
        namespace='marcrel',
        uniqueName='editor',
        valueType=Contributor,
        isContributor=True),

    # ENG/Engineer: a person or organization that is responsible for
    #   technical planning and design, particularly with construction.
    PropertyDescription(
        name='ENG',
        namespace='marcrel',
        uniqueName='engineer',
        valueType=Contributor,
        isContributor=True),

    # EGR/Engraver: a person or organization who cuts letters, figures,
    #   etc. on a surface, such as a wooden or metal plate, for printing.
    PropertyDescription(
        name='EGR',
        namespace='marcrel',
        uniqueName='engraver',
        valueType=Contributor,
        isContributor=True),

    # ETR/Etcher: a person or organization who produces text or images
    #   for printing by subjecting metal, glass, or some other surface
    #   to acid or the corrosive action of some other substance.
    PropertyDescription(
        name='ETR',
        namespace='marcrel',
        uniqueName='etcher',
        valueType=Contributor,
        isContributor=True),

    # FAC/Facsimilist: a person or organization that executed the facsimile.
    PropertyDescription(
        name='FAC',
        namespace='marcrel',
        uniqueName='facsimilist',
        valueType=Contributor,
        isContributor=True),

    # FLM/Film editor: a person or organization who is an editor of a
    #   motion picture film. This term is used regardless of the medium
    #   upon which the motion picture is produced or manufactured (e.g.,
    #   acetate film, video tape).
    PropertyDescription(
        name='FLM',
        namespace='marcrel',
        uniqueName='filmEditor',
        valueType=Contributor,
        isContributor=True),

    # FRG/Forger: a person or organization who makes or imitates something
    #   of value or importance, especially with the intent to defraud.
    PropertyDescription(
        name='FRG',
        namespace='marcrel',
        uniqueName='forger',
        valueType=Contributor,
        isContributor=True),

    # HST/Host: a person who is invited or regularly leads a program
    #   (often broadcast) that includes other guests, performers, etc.
    #   (e.g., talk show host).
    PropertyDescription(
        name='HST',
        namespace='marcrel',
        uniqueName='host',
        valueType=Contributor,
        isContributor=True),

    # ILU/Illuminator: a person or organization responsible for the
    #   decoration of a work (especially manuscript material) with
    #   precious metals or color, usually with elaborate designs and
    #   motifs.
    PropertyDescription(
        name='ILU',
        namespace='marcrel',
        uniqueName='illuminator',
        valueType=Contributor,
        isContributor=True),

    # ILL/Illustrator: a person or organization who conceives, and
    #   perhaps also implements, a design or illustration, usually
    #   to accompany a written text.
    PropertyDescription(
        name='ILL',
        namespace='marcrel',
        uniqueName='illustrator',
        valueType=Contributor,
        isContributor=True),

    # ITR/Instrumentalist: a person or organization who principally
    #   plays an instrument in a musical or dramatic presentation
    #   or entertainment.
    PropertyDescription(
        name='ITR',
        namespace='marcrel',
        uniqueName='instrumentalist',
        valueType=Contributor,
        isContributor=True),

    # IVE/Interviewee: a person or organization who is interviewed
    #   at a consultation or meeting, usually by a reporter, pollster,
    #   or some other information gathering agent.
    PropertyDescription(
        name='IVE',
        namespace='marcrel',
        uniqueName='interviewee',
        valueType=Contributor,
        isContributor=True),

    # IVR/Interviewer: a person or organization who acts as a reporter,
    #   pollster, or other information gathering agent in a consultation
    #   or meeting involving one or more individuals.
    PropertyDescription(
        name='IVR',
        namespace='marcrel',
        uniqueName='interviewer',
        valueType=Contributor,
        isContributor=True),

    # INV/Inventor: a person or organization who first produces a
    #   particular useful item, or develops a new process for
    #   obtaining a known item or result.
    PropertyDescription(
        name='INV',
        namespace='marcrel',
        uniqueName='inventor',
        valueType=Contributor,
        isContributor=True),

    # LSA/Landscape architect: a person or organization whose work
    #   involves coordinating the arrangement of existing and
    #   proposed land features and structures.
    PropertyDescription(
        name='LSA',
        namespace='marcrel',
        uniqueName='landscapeArchitect',
        valueType=Contributor,
        isContributor=True),

    # LBT/Librettist: a person or organization who is a writer of
    #   the text of an opera, oratorio, etc.
    PropertyDescription(
        name='LBT',
        namespace='marcrel',
        oldMusic21WorkId='librettist',
        valueType=Contributor,
        isContributor=True),

    # LGD/Lighting designer: a person or organization who designs the
    #   lighting scheme for a theatrical presentation, entertainment,
    #   motion picture, etc.
    PropertyDescription(
        name='LGD',
        namespace='marcrel',
        uniqueName='lightingDesigner',
        valueType=Contributor,
        isContributor=True),

    # LTG/Lithographer: a person or organization who prepares the stone
    #   or plate for lithographic printing, including a graphic artist
    #   creating a design directly on the surface from which printing
    #   will be done.
    PropertyDescription(
        name='LTG',
        namespace='marcrel',
        uniqueName='lithographer',
        valueType=Contributor,
        isContributor=True),

    # LYR/Lyricist: a person or organization who is the a writer of the
    #   text of a song.
    PropertyDescription(
        name='LYR',
        namespace='marcrel',
        oldMusic21WorkId='lyricist',
        valueType=Contributor,
        isContributor=True),

    # MFR/Manufacturer: a person or organization that makes an
    #   artifactual work (an object made or modified by one or
    #   more persons). Examples of artifactual works include vases,
    #   cannons or pieces of furniture.
    PropertyDescription(
        name='MFR',
        namespace='marcrel',
        uniqueName='manufacturer',
        valueType=Contributor,
        isContributor=True),

    # MTE/Metal-engraver: a person or organization responsible for
    #   decorations, illustrations, letters, etc. cut on a metal
    #   surface for printing or decoration.
    PropertyDescription(
        name='MTE',
        namespace='marcrel',
        uniqueName='metalEngraver',
        valueType=Contributor,
        isContributor=True),

    # MOD/Moderator: a person who leads a program (often broadcast)
    #   where topics are discussed, usually with participation of
    #   experts in fields related to the discussion.
    PropertyDescription(
        name='MOD',
        namespace='marcrel',
        uniqueName='moderator',
        valueType=Contributor,
        isContributor=True),

    # MUS/Musician: a person or organization who performs music or
    #   contributes to the musical content of a work when it is not
    #   possible or desirable to identify the function more precisely.
    PropertyDescription(
        name='MUS',
        namespace='marcrel',
        uniqueName='musician',
        valueType=Contributor,
        isContributor=True),

    # NRT/Narrator: a person who is a speaker relating the particulars
    #   of an act, occurrence, or course of events.
    PropertyDescription(
        name='NRT',
        namespace='marcrel',
        uniqueName='narrator',
        valueType=Contributor,
        isContributor=True),

    # ORM/Organizer of meeting: a person or organization responsible
    #   for organizing a meeting for which an item is the report or
    #   proceedings.
    PropertyDescription(
        name='ORM',
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
        name='ORG',
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
        name='PRF',
        namespace='marcrel',
        uniqueName='performer',
        valueType=Contributor,
        isContributor=True),

    # PHT/Photographer: a person or organization responsible for
    #   taking photographs, whether they are used in their original
    #   form or as reproductions.
    PropertyDescription(
        name='PHT',
        namespace='marcrel',
        uniqueName='photographer',
        valueType=Contributor,
        isContributor=True),

    # PLT/Platemaker: a person or organization responsible for the
    #   production of plates, usually for the production of printed
    #   images and/or text.
    PropertyDescription(
        name='PLT',
        namespace='marcrel',
        uniqueName='platemaker',
        valueType=Contributor,
        isContributor=True),

    # PRM/Printmaker: a person or organization who makes a relief,
    #   intaglio, or planographic printing surface.
    PropertyDescription(
        name='PRM',
        namespace='marcrel',
        uniqueName='printmaker',
        valueType=Contributor,
        isContributor=True),

    # PRO/Producer: a person or organization responsible for the
    #   making of a motion picture, including business aspects,
    #   management of the productions, and the commercial success
    #   of the work.
    PropertyDescription(
        name='PRO',
        namespace='marcrel',
        uniqueName='producer',
        valueType=Contributor,
        isContributor=True),

    # PRD/Production personnel: a person or organization associated
    #   with the production (props, lighting, special effects, etc.)
    #   of a musical or dramatic presentation or entertainment.
    PropertyDescription(
        name='PRD',
        namespace='marcrel',
        uniqueName='productionPersonnel',
        valueType=Contributor,
        isContributor=True),

    # PRG/Programmer: a person or organization responsible for the
    #   creation and/or maintenance of computer program design
    #   documents, source code, and machine-executable digital files
    #   and supporting documentation.
    PropertyDescription(
        name='PRG',
        namespace='marcrel',
        uniqueName='programmer',
        valueType=Contributor,
        isContributor=True),

    # PPT/Puppeteer: a person or organization who manipulates, controls,
    #   or directs puppets or marionettes in a musical or dramatic
    #   presentation or entertainment.
    PropertyDescription(
        name='PPT',
        namespace='marcrel',
        uniqueName='puppeteer',
        valueType=Contributor,
        isContributor=True),

    # RCE/Recording engineer: a person or organization who supervises
    #   the technical aspects of a sound or video recording session.
    PropertyDescription(
        name='RCE',
        namespace='marcrel',
        uniqueName='recordingEngineer',
        valueType=Contributor,
        isContributor=True),

    # REN/Renderer: a person or organization who prepares drawings
    #   of architectural designs (i.e., renderings) in accurate,
    #   representational perspective to show what the project will
    #   look like when completed.
    PropertyDescription(
        name='REN',
        namespace='marcrel',
        uniqueName='renderer',
        valueType=Contributor,
        isContributor=True),

    # RPT/Reporter: a person or organization who writes or presents
    #   reports of news or current events on air or in print.
    PropertyDescription(
        name='RPT',
        namespace='marcrel',
        uniqueName='reporter',
        valueType=Contributor,
        isContributor=True),

    # RTH/Research team head: a person who directed or managed a
    #   research project.
    PropertyDescription(
        name='RTH',
        namespace='marcrel',
        uniqueName='researchTeamHead',
        valueType=Contributor,
        isContributor=True),

    # RTM/Research team member:  a person who participated in a
    #   research project but whose role did not involve direction
    #   or management of it.
    PropertyDescription(
        name='RTM',
        namespace='marcrel',
        uniqueName='researchTeamMember',
        valueType=Contributor,
        isContributor=True),

    # RES/Researcher: a person or organization responsible for
    #   performing research.
    PropertyDescription(
        name='RES',
        namespace='marcrel',
        uniqueName='researcher',
        valueType=Contributor,
        isContributor=True),

    # RPY/Responsible party: a person or organization legally
    #   responsible for the content of the published material.
    PropertyDescription(
        name='RPY',
        namespace='marcrel',
        uniqueName='responsibleParty',
        valueType=Contributor,
        isContributor=True),

    # RSG/Restager: a person or organization, other than the
    #   original choreographer or director, responsible for
    #   restaging a choreographic or dramatic work and who
    #   contributes minimal new content.
    PropertyDescription(
        name='RSG',
        namespace='marcrel',
        uniqueName='restager',
        valueType=Contributor,
        isContributor=True),

    # REV/Reviewer:  a person or organization responsible for
    #   the review of a book, motion picture, performance, etc.
    PropertyDescription(
        name='REV',
        namespace='marcrel',
        uniqueName='reviewer',
        valueType=Contributor,
        isContributor=True),

    # SCE/Scenarist: a person or organization who is the author
    #   of a motion picture screenplay.
    PropertyDescription(
        name='SCE',
        namespace='marcrel',
        uniqueName='scenarist',
        valueType=Contributor,
        isContributor=True),

    # SAD/Scientific advisor: a person or organization who brings
    #   scientific, pedagogical, or historical competence to the
    #   conception and realization on a work, particularly in the
    #   case of audio-visual items.
    PropertyDescription(
        name='SAD',
        namespace='marcrel',
        uniqueName='scientificAdvisor',
        valueType=Contributor,
        isContributor=True),

    # SCR/Scribe: a person who is an amanuensis and for a writer of
    #   manuscripts proper. For a person who makes pen-facsimiles,
    #   use Facsimilist [fac].
    PropertyDescription(
        name='SCR',
        namespace='marcrel',
        uniqueName='scribe',
        valueType=Contributor,
        isContributor=True),

    # SCL/Sculptor: a person or organization who models or carves
    #   figures that are three-dimensional representations.
    PropertyDescription(
        name='SCL',
        namespace='marcrel',
        uniqueName='sculptor',
        valueType=Contributor,
        isContributor=True),

    # SEC/Secretary: a person or organization who is a recorder,
    #   redactor, or other person responsible for expressing the
    #   views of a organization.
    PropertyDescription(
        name='SEC',
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
        name='STD',
        namespace='marcrel',
        uniqueName='setDesigner',
        valueType=Contributor,
        isContributor=True),

    # SNG/Singer: a person or organization who uses his/her/their voice
    #   with or without instrumental accompaniment to produce music.
    #   A performance may or may not include actual words.
    PropertyDescription(
        name='SNG',
        namespace='marcrel',
        uniqueName='singer',
        valueType=Contributor,
        isContributor=True),

    # SPK/Speaker: a person who participates in a program (often broadcast)
    #   and makes a formalized contribution or presentation generally
    #   prepared in advance.
    PropertyDescription(
        name='SPK',
        namespace='marcrel',
        uniqueName='speaker',
        valueType=Contributor,
        isContributor=True),

    # STN/Standards body: an organization responsible for the development
    #   or enforcement of a standard.
    PropertyDescription(
        name='STN',
        namespace='marcrel',
        uniqueName='standardsBody',
        valueType=Contributor,
        isContributor=True),

    # STL/Storyteller: a person relaying a story with creative and/or
    #   theatrical interpretation.
    PropertyDescription(
        name='STL',
        namespace='marcrel',
        uniqueName='storyteller',
        valueType=Contributor,
        isContributor=True),

    # SRV/Surveyor: a person or organization who does measurements of
    #   tracts of land, etc. to determine location, forms, and boundaries.
    PropertyDescription(
        name='SRV',
        namespace='marcrel',
        uniqueName='surveyor',
        valueType=Contributor,
        isContributor=True),

    # TCH/Teacher: a person who, in the context of a resource, gives
    #   instruction in an intellectual subject or demonstrates while
    #   teaching physical skills.
    PropertyDescription(
        name='TCH',
        namespace='marcrel',
        uniqueName='teacher',
        valueType=Contributor,
        isContributor=True),

    # TRC/Transcriber: a person who prepares a handwritten or typewritten copy
    #   from original material, including from dictated or orally recorded
    #   material. For makers of pen-facsimiles, use Facsimilist [fac].
    PropertyDescription(
        name='TRC',
        namespace='marcrel',
        uniqueName='transcriber',
        valueType=Contributor,
        isContributor=True),

    # TRL/Translator: a person or organization who renders a text from one
    #   language into another, or from an older form of a language into the
    #   modern form.
    PropertyDescription(
        name='TRL',
        namespace='marcrel',
        oldMusic21WorkId='translator',
        valueType=Contributor,
        isContributor=True),

    # VDG/Videographer: a person or organization in charge of a video production,
    #   e.g. the video recording of a stage production as opposed to a commercial
    #   motion picture. The videographer may be the camera operator or may
    #   supervise one or more camera operators. Do not confuse with cinematographer.
    PropertyDescription(
        name='VDG',
        namespace='marcrel',
        uniqueName='videographer',
        valueType=Contributor,
        isContributor=True),

    # VOC/Vocalist: a person or organization who principally exhibits singing
    #   skills in a musical or dramatic presentation or entertainment.
    PropertyDescription(
        name='VOC',
        namespace='marcrel',
        uniqueName='vocalist',
        valueType=Contributor,
        isContributor=True),

    # WDE/Wood-engraver: a person or organization who makes prints by cutting
    #   the image in relief on the end-grain of a wood block.
    PropertyDescription(
        name='WDE',
        namespace='marcrel',
        uniqueName='woodEngraver',
        valueType=Contributor,
        isContributor=True),

    # WDC/Woodcutter: a person or organization who makes prints by cutting the
    #   image in relief on the plank side of a wood block.
    PropertyDescription(
        name='WDC',
        namespace='marcrel',
        uniqueName='woodCutter',
        valueType=Contributor,
        isContributor=True),

    # WAM/Writer of accompanying material: a person or organization who writes
    #   significant material which accompanies a sound recording or other
    #   audiovisual material.
    PropertyDescription(
        name='WAM',
        namespace='marcrel',
        uniqueName='accompanyingMaterialWriter',
        valueType=Contributor,
        isContributor=True),

    # The following marcrel property term refines dcterms:publisher

    # DST/Distributor: a person or organization that has exclusive or shared
    #   marketing rights for an item.
    PropertyDescription(
        name='DST',
        namespace='marcrel',
        uniqueName='distributor',
        valueType=Contributor,
        isContributor=True),

    # The following humdrum property terms have historically been supported
    # by music21, so we add them as standard property terms here.

    # TXO: original language of vocal/choral text
    PropertyDescription(
        name='TXO',
        namespace='humdrum',
        oldMusic21Abbrev='txo',
        oldMusic21WorkId='textOriginalLanguage',
        isContributor=False),

    # TXL: language of the encoded vocal/choral text
    PropertyDescription(
        name='TXL',
        namespace='humdrum',
        oldMusic21Abbrev='txl',
        oldMusic21WorkId='textLanguage',
        isContributor=False),

    # OTP: popular title
    PropertyDescription(
        name='OTP',
        namespace='humdrum',
        oldMusic21Abbrev='otp',
        oldMusic21WorkId='popularTitle',
        isContributor=False),

    # OPR: parent title
    PropertyDescription(
        name='OPR',
        namespace='humdrum',
        oldMusic21Abbrev='opr',
        oldMusic21WorkId='parentTitle',
        isContributor=False),

    # OAC: act number (e.g. '2' or 'Act 2')
    PropertyDescription(
        name='OAC',
        namespace='humdrum',
        oldMusic21Abbrev='oac',
        oldMusic21WorkId='actNumber',
        isContributor=False),

    # OSC: scene number (e.g. '3' or 'Scene 3')
    PropertyDescription(
        name='OSC',
        namespace='humdrum',
        oldMusic21Abbrev='osc',
        oldMusic21WorkId='sceneNumber',
        isContributor=False),

    # OMV: movement number (e.g. '4', or 'mov. 4', or...)
    PropertyDescription(
        name='OMV',
        namespace='humdrum',
        oldMusic21Abbrev='omv',
        oldMusic21WorkId='movementNumber',
        isContributor=False),

    # OMD: movement name (often a tempo description)
    PropertyDescription(
        name='OMD',
        namespace='humdrum',
        oldMusic21Abbrev='omd',
        oldMusic21WorkId='movementName',
        isContributor=False),

    # OPS: opus number (e.g. '23', or 'Opus 23')
    PropertyDescription(
        name='OPS',
        namespace='humdrum',
        oldMusic21Abbrev='ops',
        oldMusic21WorkId='opusNumber',
        isContributor=False),

    # ONM: number (e.g. number of song within ABC multi-song file)
    PropertyDescription(
        name='ONM',
        namespace='humdrum',
        oldMusic21Abbrev='onm',
        oldMusic21WorkId='number',
        isContributor=False),

    # OVM: volume number (e.g. '6' or 'Vol. 6')
    PropertyDescription(
        name='OVM',
        uniqueName='volumeNumber',
        namespace='humdrum',
        oldMusic21Abbrev='ovm',
        oldMusic21WorkId='volume',
        isContributor=False),

    # ODE: dedicated to
    PropertyDescription(
        name='ODE',
        uniqueName='dedicatedTo',
        namespace='humdrum',
        oldMusic21Abbrev='ode',
        oldMusic21WorkId='dedication',
        isContributor=False),

    # OCO: commissioned by
    PropertyDescription(
        name='OCO',
        uniqueName='commissionedBy',
        namespace='humdrum',
        oldMusic21Abbrev='oco',
        oldMusic21WorkId='commission',
        isContributor=False),

    # OCY: country of composition
    PropertyDescription(
        name='OCY',
        namespace='humdrum',
        oldMusic21Abbrev='ocy',
        oldMusic21WorkId='countryOfComposition',
        isContributor=False),

    # OPC: city, town, or village of composition
    PropertyDescription(
        name='OPC',
        namespace='humdrum',
        oldMusic21Abbrev='opc',
        oldMusic21WorkId='localeOfComposition',
        isContributor=False),

    # GTL: group title (e.g. 'The Seasons')
    PropertyDescription(
        name='GTL',
        namespace='humdrum',
        oldMusic21Abbrev='gtl',
        oldMusic21WorkId='groupTitle',
        isContributor=False),

    # GAW: associated work, such as a play or film
    PropertyDescription(
        name='GAW',
        namespace='humdrum',
        oldMusic21Abbrev='gaw',
        oldMusic21WorkId='associatedWork',
        isContributor=False),

    # GCO: collection designation. This is a free-form text record that can be
    #   used to identify a collection of pieces, such as works appearing in a
    #   compendium or anthology. E.g. Norton Scores, Smithsonian Collection,
    #   Burkhart Anthology.
    PropertyDescription(
        name='GCO',
        namespace='humdrum',
        oldMusic21Abbrev='gco',
        oldMusic21WorkId='collectionDesignation',
        isContributor=False),

    # COA: attributed composer
    PropertyDescription(
        name='COA',
        namespace='humdrum',
        oldMusic21WorkId='attributedComposer',
        valueType=Contributor,
        isContributor=True),

    # COS: suspected composer
    PropertyDescription(
        name='COS',
        namespace='humdrum',
        oldMusic21WorkId='suspectedComposer',
        valueType=Contributor,
        isContributor=True),

    # COL: composer's abbreviated, alias, or stage name
    PropertyDescription(
        name='COL',
        namespace='humdrum',
        oldMusic21WorkId='composerAlias',
        valueType=Contributor,
        isContributor=True),

    # COC: composer's corporate name
    PropertyDescription(
        name='COC',
        namespace='humdrum',
        oldMusic21WorkId='composerCorporate',
        valueType=Contributor,
        isContributor=True),

    # LOR: orchestrator
    PropertyDescription(
        name='LOR',
        namespace='humdrum',
        oldMusic21WorkId='orchestrator',
        valueType=Contributor,
        isContributor=True),

    # The following mei property terms are not found in dcterms, marcrel, or humdrum.

    PropertyDescription(
        name='subtitle',
        namespace='mei',
        isContributor=False)
)

# -----------------------------------------------------------------------------
# Dictionaries generated from STANDARD_PROPERTY_DESCRIPTIONS for looking up
# various things quickly.

NSKEY_TO_PROPERTYDESCRIPTION: dict = {
    f'{x.namespace}:{x.name}':
        x for x in STANDARD_PROPERTY_DESCRIPTIONS}

NSKEY_TO_VALUETYPE: dict = {
    f'{x.namespace}:{x.name}':
        x.valueType for x in STANDARD_PROPERTY_DESCRIPTIONS}

NSKEY_TO_CONTRIBUTORUNIQUENAME: dict = {
    f'{x.namespace}:{x.name}':
        x.uniqueName if x.uniqueName
        else x.oldMusic21WorkId if x.oldMusic21WorkId
        else x.name
        for x in STANDARD_PROPERTY_DESCRIPTIONS if x.isContributor}

NSKEY_TO_UNIQUENAME: dict = {
    f'{x.namespace}:{x.name}':
        x.uniqueName if x.uniqueName
        else x.oldMusic21WorkId if x.oldMusic21WorkId
        else x.name
        for x in STANDARD_PROPERTY_DESCRIPTIONS}

UNIQUENAME_TO_NSKEY: dict = {
    x.uniqueName if x.uniqueName
    else x.oldMusic21WorkId if x.oldMusic21WorkId
    else x.name:
        f'{x.namespace}:{x.name}'
        for x in STANDARD_PROPERTY_DESCRIPTIONS}

UNIQUENAME_TO_PROPERTYDESCRIPTION: dict = {
    x.uniqueName if x.uniqueName
    else x.oldMusic21WorkId if x.oldMusic21WorkId
    else x.name:
        x for x in STANDARD_PROPERTY_DESCRIPTIONS}

M21ABBREV_TO_NSKEY: dict = {
    x.oldMusic21Abbrev if x.oldMusic21Abbrev
    else None:
        f'{x.namespace}:{x.name}'
        for x in STANDARD_PROPERTY_DESCRIPTIONS
        if x.oldMusic21Abbrev}

M21WORKID_TO_NSKEY: dict = {
    x.oldMusic21WorkId if x.oldMusic21WorkId
    else None:
        f'{x.namespace}:{x.name}'
        for x in STANDARD_PROPERTY_DESCRIPTIONS
        if x.oldMusic21WorkId}

ALL_UNIQUENAMES: list = list(UNIQUENAME_TO_NSKEY.keys())
ALL_M21WORKIDS: list = list(M21WORKID_TO_NSKEY.keys())
ALL_M21ABBREVS: list = list(M21ABBREV_TO_NSKEY.keys())
ALL_NSKEYS: list = list(NSKEY_TO_PROPERTYDESCRIPTION.keys())
