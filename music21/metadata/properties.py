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
            'dcterms' means the property term is from the Dublin Core terms,
                defined at <http://purl.org/dc/terms/>
            'marcrel' means the property term is from the MARC Relator terms,
                defined at <http://www.loc.gov/loc.terms/relators/>
            'humdrum' means the property term is from the Humdrum reference record terms,
                defined at <https://www.humdrum.org/reference-records/#>
        isContributor: bool is whether or not the property describes a contributor.
        needsArticleNormalization: bool is whether or not the property values might
            benefit from article normalization when getting as a string (this is
            generally True for various kinds of titles).
        oldMusic21Abbrev: str is the backward compatible music21 abbreviation for this
            property.
        oldMusic21WorkId: str is the backward compatible music21 name for this property.
        uniqueName: str is the official music21 name for this property, that is unique
            within the list of properties. There is always a unique name, but the
            uniqueName field is only set if name is not unique enough.
            To get the unique name from a particular PropertyDescription, we do:
                (desc.uniqueName if desc.uniqueName
                    else desc.name)
        valueType: Type is the actual type of the value that will be stored in the metadata.
            This allows auto-conversion to take place when clients store items in the
            metadata, and is the tuple element type clients will always receive from
            md['uniqueName'] or md['namespace:name'].
    '''
    uniqueName: t.Optional[str] = None
    name: str = ''
    namespace: str = ''
    oldMusic21Abbrev: t.Optional[str] = None
    oldMusic21WorkId: t.Optional[str] = None
    valueType: t.Type = Text
    needsArticleNormalization: bool = False
    isContributor: bool = False


STANDARD_PROPERTY_DESCRIPTIONS: t.Tuple[PropertyDescription, ...] = (
    # The following 'dcterms' properties are standard Dublin Core property
    # terms, found at http://purl.org/dc/terms/

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

    # alternativeTitle: An alternative name for the resource.
    PropertyDescription(
        uniqueName='alternativeTitle',
        name='alternative',
        namespace='dcterms',
        oldMusic21Abbrev='ota',
        needsArticleNormalization=True,
        isContributor=False),

    # audience: A class of agents for whom the resource is intended or useful.
    PropertyDescription(
        name='audience',
        namespace='dcterms',
        isContributor=False),

    # dateAvailable: Date that the resource became or will become available.
    PropertyDescription(
        uniqueName='dateAvailable',
        name='available',
        namespace='dcterms',
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

    # dateCreated: Date of creation of the resource.
    PropertyDescription(
        uniqueName='dateCreated',
        name='created',
        namespace='dcterms',
        oldMusic21WorkId='date',
        valueType=DateSingle,   # including DateRelative, DateBetween, DateSelection
        isContributor=False),

    # otherDate: A point or period of time associated with an event in the lifecycle
    #   of the resource.
    PropertyDescription(
        uniqueName='otherDate',
        name='date',
        namespace='dcterms',
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

    # dateIssued: Date of formal issuance of the resource.
    PropertyDescription(
        uniqueName='dateIssued',
        name='issued',
        namespace='dcterms',
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

    # medium: The material or physical carrier of the resource.
    PropertyDescription(
        name='medium',
        namespace='dcterms',
        isContributor=False),

    # dateModified: Date on which the resource was changed.
    PropertyDescription(
        uniqueName='dateModified',
        name='modified',
        namespace='dcterms',
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

    # copyright: Information about rights held in and over the resource.
    PropertyDescription(
        uniqueName='copyright',
        name='rights',
        namespace='dcterms',
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

    # title: A name given to the resource.
    PropertyDescription(
        name='title',
        namespace='dcterms',
        oldMusic21Abbrev='otl',
        needsArticleNormalization=True,
        isContributor=False),

    # type : The nature or genre of the resource.
    PropertyDescription(
        name='type',
        namespace='dcterms',
        isContributor=False),

    # dateValid: Date (often a range) of validity of a resource.
    PropertyDescription(
        uniqueName='dateValid',
        name='valid',
        namespace='dcterms',
        valueType=DateSingle,   # including DateRelative, DateBetween, DateSelection
        isContributor=False),

    # The following 'marcrel' property terms are MARC Relator terms,
    # found at:  http://www.loc.gov/loc.terms/relators/

    # adapter: a person or organization who 1) reworks a musical composition,
    #   usually for a different medium, or 2) rewrites novels or stories
    #   for motion pictures or other audiovisual medium.
    PropertyDescription(
        uniqueName='adapter',
        name='ADP',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # annotator: a person who writes manuscript annotations on a printed item.
    PropertyDescription(
        uniqueName='annotator',
        name='ANN',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # arranger: a person or organization who transcribes a musical
    #   composition, usually for a different medium from that of the original;
    #   in an arrangement the musical substance remains essentially unchanged.
    PropertyDescription(
        uniqueName='arranger',
        name='ARR',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # quotationsAuthor: a person or organization whose work is largely quoted
    #   or extracted in works to which he or she did not contribute directly.
    PropertyDescription(
        uniqueName='quotationsAuthor',
        name='AQT',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # afterwordAuthor: a person or organization responsible for an afterword,
    #   postface, colophon, etc. but who is not the chief author of a work.
    PropertyDescription(
        uniqueName='afterwordAuthor',
        name='AFT',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # dialogAuthor: a person or organization responsible for
    #   the dialog or spoken commentary for a screenplay or sound
    #   recording.
    PropertyDescription(
        uniqueName='dialogAuthor',
        name='AUD',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # introductionAuthor:  a person or organization responsible for an
    #   introduction, preface, foreword, or other critical introductory
    #   matter, but who is not the chief author.
    PropertyDescription(
        uniqueName='introductionAuthor',
        name='AUI',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # calligrapher: a person or organization who writes in an artistic
    #   hand, usually as a copyist and or engrosser.
    PropertyDescription(
        uniqueName='calligrapher',
        name='CLL',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # collaborator: a person or organization that takes a limited part
    #   in the elaboration of a work of another person or organization that
    #   brings complements (e.g., appendices, notes) to the work.
    PropertyDescription(
        uniqueName='collaborator',
        name='CLB',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # collotyper: a person or organization responsible for the production
    #   of photographic prints from film or other colloid that has ink-receptive
    #   and ink-repellent surfaces.
    PropertyDescription(
        uniqueName='collotyper',
        name='CLT',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # commentaryAuthor: a person or organization responsible for the
    #   commentary or explanatory notes about a text. For the writer of
    #   manuscript annotations in a printed book, use annotator.
    PropertyDescription(
        uniqueName='commentaryAuthor',
        name='CWT',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # compiler: a person or organization who produces a work or
    #   publication by selecting and putting together material from the
    #   works of various persons or bodies.
    PropertyDescription(
        uniqueName='compiler',
        name='COM',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # composer: a person or organization who creates a musical work,
    #   usually a piece of music in manuscript or printed form.
    PropertyDescription(
        uniqueName='composer',
        name='CMP',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # conceptor: a person or organization responsible for the original
    #   idea on which a work is based, this includes the scientific author
    #   of an audio-visual item and the conceptor of an advertisement.
    PropertyDescription(
        uniqueName='conceptor',
        name='CCP',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # conductor: a person who directs a performing group (orchestra,
    #   chorus, opera, etc.) in a musical or dramatic presentation or
    #   entertainment.
    PropertyDescription(
        uniqueName='conductor',
        name='CND',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # otherContributor: a person or organization one whose work has been
    #   contributed to a larger work, such as an anthology, serial
    #   publication, or other compilation of individual works. Only
    #   use if there is no other more specific term that is accurate.
    #   If otherContributor is used, set contributorValue.role to a
    #   custom term that accurately describes the actual role of this
    #   contributor.
    PropertyDescription(
        uniqueName='otherContributor',
        name='CTB',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # editor: a person or organization who prepares for publication
    #   a work not primarily his/her own, such as by elucidating text,
    #   adding introductory or other critical matter, or technically
    #   directing an editorial staff.
    PropertyDescription(
        uniqueName='editor',
        name='EDT',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # engraver: a person or organization who cuts letters, figures,
    #   etc. on a surface, such as a wooden or metal plate, for printing.
    PropertyDescription(
        uniqueName='engraver',
        name='EGR',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # etcher: a person or organization who produces text or images
    #   for printing by subjecting metal, glass, or some other surface
    #   to acid or the corrosive action of some other substance.
    PropertyDescription(
        uniqueName='etcher',
        name='ETR',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # illuminator: a person or organization responsible for the
    #   decoration of a work (especially manuscript material) with
    #   precious metals or color, usually with elaborate designs and
    #   motifs.
    PropertyDescription(
        uniqueName='illuminator',
        name='ILU',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # illustrator: a person or organization who conceives, and
    #   perhaps also implements, a design or illustration, usually
    #   to accompany a written text.
    PropertyDescription(
        uniqueName='illustrator',
        name='ILL',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # instrumentalist: a person or organization who principally
    #   plays an instrument in a musical or dramatic presentation
    #   or entertainment.
    PropertyDescription(
        uniqueName='instrumentalist',
        name='ITR',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # librettist: a person or organization who is a writer of
    #   the text of an opera, oratorio, etc.
    PropertyDescription(
        uniqueName='librettist',
        name='LBT',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # lithographer: a person or organization who prepares the stone
    #   or plate for lithographic printing, including a graphic artist
    #   creating a design directly on the surface from which printing
    #   will be done.
    PropertyDescription(
        uniqueName='lithographer',
        name='LTG',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # lyricist: a person or organization who is the a writer of the
    #   text of a song.
    PropertyDescription(
        uniqueName='lyricist',
        name='LYR',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # metalEngraver: a person or organization responsible for
    #   decorations, illustrations, letters, etc. cut on a metal
    #   surface for printing or decoration.
    PropertyDescription(
        uniqueName='metalEngraver',
        name='MTE',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # musician: a person or organization who performs music or
    #   contributes to the musical content of a work when it is not
    #   possible or desirable to identify the function more precisely.
    PropertyDescription(
        uniqueName='musician',
        name='MUS',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # platemaker: a person or organization responsible for the
    #   production of plates, usually for the production of printed
    #   images and/or text.
    PropertyDescription(
        uniqueName='platemaker',
        name='PLT',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # printmaker: a person or organization who makes a relief,
    #   intaglio, or planographic printing surface.
    PropertyDescription(
        uniqueName='printmaker',
        name='PRM',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # producer: a person or organization responsible for the
    #   making of an artistic work, including business aspects,
    #   management of the productions, and the commercial success
    #   of the work.
    PropertyDescription(
        uniqueName='producer',
        name='PRO',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # responsibleParty: a person or organization legally
    #   responsible for the content of the published material.
    PropertyDescription(
        uniqueName='responsibleParty',
        name='RPY',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # scribe: a person who is an amanuensis and for a writer of
    #   manuscripts proper. For a person who makes pen-facsimiles,
    #   use Facsimilist [fac].
    PropertyDescription(
        uniqueName='scribe',
        name='SCR',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # singer: a person or organization who uses his/her/their voice
    #   with or without instrumental accompaniment to produce music.
    #   A performance may or may not include actual words.
    PropertyDescription(
        uniqueName='singer',
        name='SNG',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # transcriber: a person who prepares a handwritten or typewritten copy
    #   from original material, including from dictated or orally recorded
    #   material. For makers of pen-facsimiles, use Facsimilist [fac].
    PropertyDescription(
        uniqueName='transcriber',
        name='TRC',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # translator: a person or organization who renders a text from one
    #   language into another, or from an older form of a language into the
    #   modern form.
    PropertyDescription(
        uniqueName='translator',
        name='TRL',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # woodEngraver: a person or organization who makes prints by cutting
    #   the image in relief on the end-grain of a wood block.
    PropertyDescription(
        uniqueName='woodEngraver',
        name='WDE',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # woodCutter: a person or organization who makes prints by cutting the
    #   image in relief on the plank side of a wood block.
    PropertyDescription(
        uniqueName='woodCutter',
        name='WDC',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # accompanyingMaterialWriter: a person or organization who writes
    #   significant material which accompanies a sound recording or other
    #   audiovisual material.
    PropertyDescription(
        uniqueName='accompanyingMaterialWriter',
        name='WAM',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # distributor: a person or organization that has exclusive or shared
    #   marketing rights for an item. (This is a refinement of 'publisher'.)
    PropertyDescription(
        uniqueName='distributor',
        name='DST',
        namespace='marcrel',
        valueType=Contributor,
        isContributor=True),

    # The following 'humdrum' property terms are Humdrum reference record
    # terms, found at https://www.humdrum.org/reference-records/#

    # textOriginalLanguage: original language of vocal/choral text
    PropertyDescription(
        uniqueName='textOriginalLanguage',
        name='TXO',
        namespace='humdrum',
        oldMusic21Abbrev='txo',
        isContributor=False),

    # textLanguage: language of the encoded vocal/choral text
    PropertyDescription(
        uniqueName='textLanguage',
        name='TXL',
        namespace='humdrum',
        oldMusic21Abbrev='txl',
        isContributor=False),

    # popularTitle: popular title
    PropertyDescription(
        uniqueName='popularTitle',
        name='OTP',
        namespace='humdrum',
        oldMusic21Abbrev='otp',
        needsArticleNormalization=True,
        isContributor=False),

    # parentTitle: parent title
    PropertyDescription(
        uniqueName='parentTitle',
        name='OPR',
        namespace='humdrum',
        oldMusic21Abbrev='opr',
        needsArticleNormalization=True,
        isContributor=False),

    # actNumber: act number (e.g. '2' or 'Act 2')
    PropertyDescription(
        uniqueName='actNumber',
        name='OAC',
        namespace='humdrum',
        oldMusic21Abbrev='oac',
        isContributor=False),

    # sceneNumber: scene number (e.g. '3' or 'Scene 3')
    PropertyDescription(
        uniqueName='sceneNumber',
        name='OSC',
        namespace='humdrum',
        oldMusic21Abbrev='osc',
        isContributor=False),

    # movementNumber: movement number (e.g. '4', or 'mov. 4', or...)
    PropertyDescription(
        uniqueName='movementNumber',
        name='OMV',
        namespace='humdrum',
        oldMusic21Abbrev='omv',
        isContributor=False),

    # movementName: movement name (often a tempo description)
    PropertyDescription(
        uniqueName='movementName',
        name='OMD',
        namespace='humdrum',
        oldMusic21Abbrev='omd',
        needsArticleNormalization=True,
        isContributor=False),

    # opusNumber: opus number (e.g. '23', or 'Opus 23')
    PropertyDescription(
        uniqueName='opusNumber',
        name='OPS',
        namespace='humdrum',
        oldMusic21Abbrev='ops',
        isContributor=False),

    # number: generic number (e.g. number of song within ABC multi-song file)
    PropertyDescription(
        uniqueName='number',
        name='ONM',
        namespace='humdrum',
        oldMusic21Abbrev='onm',
        isContributor=False),

    # volumeNumber: volume number (e.g. '6' or 'Vol. 6')
    PropertyDescription(
        uniqueName='volumeNumber',
        name='OVM',
        namespace='humdrum',
        oldMusic21Abbrev='ovm',
        oldMusic21WorkId='volume',
        isContributor=False),

    # dedicatedTo: dedicated to
    PropertyDescription(
        uniqueName='dedicatedTo',
        name='ODE',
        namespace='humdrum',
        oldMusic21Abbrev='ode',
        oldMusic21WorkId='dedication',
        isContributor=False),

    # commissionedBy: commissioned by
    PropertyDescription(
        uniqueName='commissionedBy',
        name='OCO',
        namespace='humdrum',
        oldMusic21Abbrev='oco',
        oldMusic21WorkId='commission',
        isContributor=False),

    # countryOfComposition: country of composition
    PropertyDescription(
        uniqueName='countryOfComposition',
        name='OCY',
        namespace='humdrum',
        oldMusic21Abbrev='ocy',
        isContributor=False),

    # localeOfComposition: city, town, or village of composition
    PropertyDescription(
        uniqueName='localeOfComposition',
        name='OPC',
        namespace='humdrum',
        oldMusic21Abbrev='opc',
        isContributor=False),

    # groupTitle: group title (e.g. 'The Seasons')
    PropertyDescription(
        uniqueName='groupTitle',
        name='GTL',
        namespace='humdrum',
        oldMusic21Abbrev='gtl',
        needsArticleNormalization=True,
        isContributor=False),

    # associatedWork: associated work, such as a play or film
    PropertyDescription(
        uniqueName='associatedWork',
        name='GAW',
        namespace='humdrum',
        oldMusic21Abbrev='gaw',
        isContributor=False),

    # collectionDesignation: collection designation. E.g. Norton Scores,
    #   Smithsonian Collection, Burkhart Anthology.
    PropertyDescription(
        uniqueName='collectionDesignation',
        name='GCO',
        namespace='humdrum',
        oldMusic21Abbrev='gco',
        isContributor=False),

    # attributedComposer: attributed composer
    PropertyDescription(
        uniqueName='attributedComposer',
        name='COA',
        namespace='humdrum',
        valueType=Contributor,
        isContributor=True),

    # suspectedComposer: suspected composer
    PropertyDescription(
        uniqueName='suspectedComposer',
        name='COS',
        namespace='humdrum',
        valueType=Contributor,
        isContributor=True),

    # composerAlias: composer's abbreviated, alias, or stage name
    PropertyDescription(
        uniqueName='composerAlias',
        name='COL',
        namespace='humdrum',
        valueType=Contributor,
        isContributor=True),

    # composerCorporate: composer's corporate name
    PropertyDescription(
        uniqueName='composerCorporate',
        name='COC',
        namespace='humdrum',
        valueType=Contributor,
        isContributor=True),

    # orchestrator: orchestrator
    PropertyDescription(
        uniqueName='orchestrator',
        name='LOR',
        namespace='humdrum',
        valueType=Contributor,
        isContributor=True),

    # originalDocumentOwner: original document owner
    PropertyDescription(
        uniqueName='originalDocumentOwner',
        name='YOO',
        namespace='humdrum',
        valueType=Contributor,
        isContributor=True),

    # originalEditor: original editor
    PropertyDescription(
        uniqueName='originalEditor',
        name='YOE',
        namespace='humdrum',
        valueType=Contributor,
        isContributor=True),

    # electronicEditor: electronic editor
    PropertyDescription(
        uniqueName='electronicEditor',
        name='EED',
        namespace='humdrum',
        valueType=Contributor,
        isContributor=True),

    # electronicEncoder: electronic encoder
    PropertyDescription(
        uniqueName='electronicEncoder',
        name='ENC',
        namespace='humdrum',
        valueType=Contributor,
        isContributor=True),
)

# -----------------------------------------------------------------------------
# Dictionaries generated from STANDARD_PROPERTY_DESCRIPTIONS for looking up
# various things quickly.

NSKEY_TO_PROPERTY_DESCRIPTION: t.Dict[str, PropertyDescription] = {
    f'{x.namespace}:{x.name}':
        x for x in STANDARD_PROPERTY_DESCRIPTIONS}

NSKEY_TO_VALUE_TYPE: t.Dict[str, t.Type] = {
    f'{x.namespace}:{x.name}':
        x.valueType for x in STANDARD_PROPERTY_DESCRIPTIONS}

NSKEY_TO_CONTRIBUTOR_UNIQUE_NAME: t.Dict[str, str] = {
    f'{x.namespace}:{x.name}':
        x.uniqueName if x.uniqueName
        else x.name
        for x in STANDARD_PROPERTY_DESCRIPTIONS if x.isContributor}

NSKEY_TO_UNIQUE_NAME: t.Dict[str, str] = {
    f'{x.namespace}:{x.name}':
        x.uniqueName if x.uniqueName
        else x.name
        for x in STANDARD_PROPERTY_DESCRIPTIONS}

UNIQUE_NAME_TO_NSKEY: t.Dict[str, str] = {
    x.uniqueName if x.uniqueName
    else x.name:
        f'{x.namespace}:{x.name}'
        for x in STANDARD_PROPERTY_DESCRIPTIONS}

UNIQUE_NAME_TO_PROPERTY_DESCRIPTION: t.Dict[str, PropertyDescription] = {
    x.uniqueName if x.uniqueName
    else x.name:
        x for x in STANDARD_PROPERTY_DESCRIPTIONS}

MUSIC21_ABBREVIATION_TO_NSKEY: t.Dict[str, str] = {
    x.oldMusic21Abbrev if x.oldMusic21Abbrev
    else '':
        f'{x.namespace}:{x.name}'
        for x in STANDARD_PROPERTY_DESCRIPTIONS
        if x.oldMusic21Abbrev}

MUSIC21_WORK_ID_TO_NSKEY: t.Dict[str, str] = {
    x.oldMusic21WorkId if x.oldMusic21WorkId
    else '':
        f'{x.namespace}:{x.name}'
        for x in STANDARD_PROPERTY_DESCRIPTIONS
        if x.oldMusic21WorkId}

ALL_UNIQUE_NAMES: t.List[str] = list(UNIQUE_NAME_TO_NSKEY.keys())
ALL_MUSIC21_WORK_IDS: t.List[str] = list(MUSIC21_WORK_ID_TO_NSKEY.keys())
ALL_MUSIC21_ABBREVIATIONS: t.List[str] = list(MUSIC21_ABBREVIATION_TO_NSKEY.keys())
ALL_NSKEYS: t.List[str] = list(NSKEY_TO_PROPERTY_DESCRIPTION.keys())

ALL_SINGLE_ATTRIBUTE_NAMES: t.List[str] = list(
    ALL_UNIQUE_NAMES
    + ALL_MUSIC21_WORK_IDS
    + ALL_MUSIC21_ABBREVIATIONS
    + ['fileFormat' + 'filePath' + 'fileNumber']
)

ALL_PLURAL_ATTRIBUTE_NAMES: t.List[str] = [
    'composers', 'librettists', 'lyricists'
]

ALL_LEGAL_ATTRIBUTES: t.List[str] = list(
    ALL_SINGLE_ATTRIBUTE_NAMES
    + ALL_PLURAL_ATTRIBUTE_NAMES
)
