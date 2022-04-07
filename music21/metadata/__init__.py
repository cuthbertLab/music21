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
'''

'''
    A guide to this initial new implementation:

    - class OldMetadata is where I'm keeping the old Metadata implementation.
        Metadata is the new implementation.

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
        addItem() and replaceItem().  addItem adds the new item to the (possibly empty)
        set of values, and replaceItem removes any current list of values before adding
        the item.

    - Primitives: Old code had DateXxxx and Text.  DateXxxx still works for Dublin Core
        et al (it's a superset of what is needed), but Text needs to add the ability to
        know whether or not the text has been translated, as well as a specified encoding
        scheme (a.k.a. what standard should I use to parse this string) so I have a new
        class TextLiteral (which is Dublin Core terminology) that replaces Text.

    - I have not yet tried to support client-specified namespaces, but I do have a couple
        APIs (getPersonalItem, addPersonalItem, replacePersonalItem) that have no namespace
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
        f'{namespace}:{name}', and the value is one of TextLiteral, DateXxxx, or a
        List of values of those types (for properties that have more than one value).


'''
from collections import OrderedDict, namedtuple
from dataclasses import dataclass
import os
import pathlib
import re
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
                                         Imprint, Copyright, TextLiteral)

from music21.metadata import testMetadata
# -----------------------------------------------------------------------------

__all__ = [
    'Metadata',     # the new implementation
    'OldMetadata',  # the old implementation
    'RichMetadata',
    'AmbitusShort',
    'Property'
]

from music21 import environment
environLocal = environment.Environment(os.path.basename(__file__))

AmbitusShort = namedtuple('AmbitusShort',
                          ['semitones', 'diatonic', 'pitchLowest', 'pitchHighest'])
Property = namedtuple('Property', 'code name label namespace')

@dataclass
class FileInfo:
    path: t.Optional[Text] = None
    number: t.Optional[int] = None
    format: t.Optional[Text] = None

# -----------------------------------------------------------------------------

class Metadata(base.Music21Object):
    # STDPROPERTIES: each Tuple['str', 'str', 'str', 'str'] is
    # code, name, label, namespace, oldAbbrev, oldWorkId
    # where:
    # code is an abbreviation for the name
    # name is the tail of the property term URI
    # label is the human-readable name of the property term
    # namespace is a shortened form of the URI for the set of terms
    #   e.g. 'dcterm' means the property term is from the Dublin Core property terms.
    #   'dcterm' is the shortened form of <http://purl.org/dc/terms/>
    #   e.g. 'marcrel' means the property term is from the MARC Relator terms (a.k.a. 'roles').
    #   'marcrel' is the shortened form of <http://www.loc.gov/loc.terms/relators/>
    # oldAbbrev is the old abbreviation (from Metadata.workIdAbbreviationDict)
    # oldWorkId is the old workID (from Metadata.workIdAbbreviationDict)

    STDPROPERTIES: Tuple[Property] = (
        # The following 'dcterm' properties are the standard Dublin Core property terms
        # found at http://purl.org/dc/terms/

        # abstract: A summary of the resource.
        Property('AB', 'abstract', 'Abstract', 'dcterm'),

        # accessRights: Information about who access the resource or an indication of
        #   its security status.
        Property('AR', 'accessRights', 'Access Rights', 'dcterm'),

        # accrualMethod: The method by which items are added to a collection.
        Property('AM', 'accrualMethod', 'Accrual Method', 'dcterm'),

        # accrualPeriodicity: The frequency with which items are added to a collection.
        Property('AP', 'accrualPeriodicity', 'Accrual Periodicity', 'dcterm'),

        # accrualPolicy: The policy governing the addition of items to a collection.
        Property('APL', 'accrualPolicy', 'Accrual Policy', 'dcterm'),

        # alternative: An alternative name for the resource.
        Property('ALT', 'alternative', 'Alternative Title', 'dcterm'),

        # audience: A class of agents for whom the resource is intended or useful.
        Property('AUD', 'audience', 'Audience', 'dcterm'),

        # available: Date that the resource became or will become available.
        Property('AVL', 'available', 'Date Available', 'dcterm'),

        # bibliographicCitation: A bibliographic reference for the resource.
        Property('BIB', 'bibliographicCitation', 'Bibliographic Citation', 'dcterm'),

        # conformsTo: An established standard to which the described resource conforms.
        Property('COT', 'conformsTo', 'Conforms To', 'dcterm'),

        # contributor: An entity responsible for making contributions to the resource.
        # NOTE: You should use one of the 'marcrel' properties below instead, since
        # this property is very vague. The 'marcrel' properties are considered to be
        # refinements of dcterm:contributor (this property), so if someone asks for
        # everything as Dublin Core metadata, those will all be translated into
        # dcterm:contributor properties.
        Property('CN', 'contributor', 'Contributor', 'dcterm'),

        # coverage: The spatial or temporal topic of the resource, spatial applicability
        #   of the resource, or jurisdiction under which the resource is relevant.
        Property('CVR', 'coverage', 'Coverage', 'dcterm'),

        # created: Date of creation of the resource.
        Property('CRD', 'created', 'Date Created', 'dcterm'),

        # creator: An entity responsible for making the resource.
        Property('CR', 'creator', 'Creator', 'dcterm'),

        # date: A point or period of time associated with an event in the lifecycle
        #   of the resource.
        Property('DT', 'date', 'Date', 'dcterm'),

        # dateAccepted: Date of acceptance of the resource.
        Property('DTA', 'dateAccepted', 'Date Accepted', 'dcterm'),

        # dateCopyrighted: Date of copyright of the resource.
        Property('DTC', 'dateCopyrighted', 'Date Copyrighted', 'dcterm'),

        # dateSubmitted: Date of submission of the resource.
        Property('DTS', 'dateSubmitted', 'Date Submitted', 'dcterm'),

        # description: An account of the resource.
        Property('DSC', 'description', 'Description', 'dcterm'),

        # educationLevel: A class of agents, defined in terms of progression
        #   through an educational or training context, for which the described
        #   resource is intended.
        Property('EL', 'educationLevel', 'Audience Education Level', 'dcterm'),

        # extent: The size or duration of the resource.
        Property('EXT', 'extent', 'Extent', 'dcterm'),

        # format: The file format, physical medium, or dimensions of the resource.
        Property('FMT', 'format', 'Format', 'dcterm'),

        # hasFormat: A related resource that is substantially the same as the
        #   pre-existing described resource, but in another format.
        Property('HFMT', 'hasFormat', 'Has Format', 'dcterm'),

        # hasPart: A related resource that is included either physically or
        #   logically in the described resource.
        Property('HPT', 'hasPart', 'Has Part', 'dcterm'),

        # hasVersion: A related resource that is a version, edition, or adaptation
        #   of the described resource.
        Property('HVS', 'hasVersion', 'Has Version', 'dcterm'),

        # identifier: An unambiguous reference to the resource within a given context.
        Property('ID', 'identifier', 'Identifier', 'dcterm'),

        # instructionalMethod: A process, used to engender knowledge, attitudes and
        #   skills, that the described resource is designed to support.
        Property('IM', 'instructionalMethod', 'Instructional Method', 'dcterm'),

        # isFormatOf: A pre-existing related resource that is substantially the same
        #   as the described resource, but in another format.
        Property('IFMT', 'isFormatOf', 'Is Format Of', 'dcterm'),

        # isPartOf: A related resource in which the described resource is physically
        #   or logically included.
        Property('IPT', 'isPartOf', 'Is Part Of', 'dcterm'),

        # isReferencedBy: A related resource that references, cites, or otherwise
        #   points to the described resource.
        Property('IREF', 'isReferencedBy', 'Is Referenced By', 'dcterm'),

        # isReplacedBy: A related resource that supplants, displaces, or supersedes
        #   the described resource.
        Property('IREP', 'isReplacedBy', 'Is Replaced By', 'dcterm'),

        # isRequiredBy: A related resource that requires the described resource
        #   to support its function, delivery, or coherence.
        Property('IREQ', 'isRequiredBy', 'Is Required By', 'dcterm'),

        # issued: Date of formal issuance of the resource.
        Property('IS', 'issued', 'Date Issued', 'dcterm'),

        # isVersionOf: A related resource of which the described resource is a
        #   version, edition, or adaptation.
        Property('IVSN', 'isVersionOf', 'Is Version Of', 'dcterm'),

        # language: A language of the resource.
        Property('LG', 'language', 'Language', 'dcterm'),

        # license: A legal document giving official permission to do something
        #   with the resource.
        Property('LI', 'license', 'License', 'dcterm'),

        # mediator: An entity that mediates access to the resource.
        Property('ME', 'mediator', 'Mediator', 'dcterm'),

        # medium: The material or physical carrier of the resource.
        Property('MED', 'medium', 'Medium', 'dcterm'),

        # modified: Date on which the resource was changed.
        Property('MOD', 'modified', 'Date Modified', 'dcterm'),

        # provenance: A statement of any changes in ownership and custody of
        #   the resource since its creation that are significant for its
        #   authenticity, integrity, and interpretation.
        Property('PRV', 'provenance', 'Provenance', 'dcterm'),

        # publisher: An entity responsible for making the resource available.
        Property('PBL', 'publisher', 'Publisher', 'dcterm'),

        # references: A related resource that is referenced, cited, or
        #   otherwise pointed to by the described resource.
        Property('REF', 'references', 'References', 'dcterm'),

        # relation: A related resource.
        Property('REL', 'relation', 'Relation', 'dcterm'),

        # replaces: A related resource that is supplanted, displaced, or
        #   superseded by the described resource.
        Property('REP', 'replaces', 'Replaces', 'dcterm'),

        # requires: A related resource that is required by the described
        #   resource to support its function, delivery, or coherence.
        Property('REQ', 'requires', 'Requires', 'dcterm'),

        # rights: Information about rights held in and over the resource.
        Property('RT', 'rights', 'Rights', 'dcterm'),

        # rightsHolder: A person or organization owning or managing rights
        #   over the resource.
        Property('RH', 'rightsHolder', 'Rights Holder', 'dcterm'),

        # source: A related resource from which the described resource
        #   is derived.
        Property('SRC', 'source', 'Source', 'dcterm'),

        # spatial: Spatial characteristics of the resource.
        Property('SP', 'spatial', 'Spatial Coverage', 'dcterm'),

        # subject: A topic of the resource.
        Property('SUB', 'subject', 'Subject', 'dcterm'),

        # tableOfContents: A list of subunits of the resource.
        Property('TOC', 'tableOfContents', 'Table Of Contents', 'dcterm'),

        # temporal: Temporal characteristics of the resource.
        Property('TE', 'temporal', 'Temporal Coverage', 'dcterm'),

        # title: A name given to the resource.
        Property('T', 'title', 'Title', 'dcterm'),

        # type : The nature or genre of the resource.
        Property('TYP', 'type', 'Type', 'dcterm'),

        # valid: Date (often a range) of validity of a resource.
        Property('VA', 'valid', 'Date Valid', 'dcterm'),

        # The following 'marcrel' property terms are the MARC Relator terms
        # that are refinements of dcterm:contributor, and can be used anywhere
        # dcterm:contributor can be used if you want to be more specific (and
        # you will want to). The MARC Relator terms are defined at:
        # http://www.loc.gov/loc.terms/relators/
        # and this particular sublist can be found at:
        # https://memory.loc.gov/diglib/loc.terms/relators/dc-contributor.html

        # ACT/Actor: a person or organization who principally exhibits acting
        #   skills in a musical or dramatic presentation or entertainment.
        Property('act', 'ACT', 'Actor', 'marcrel'),

        # ADP/Adapter: a person or organization who 1) reworks a musical composition,
        #   usually for a different medium, or 2) rewrites novels or stories
        #   for motion pictures or other audiovisual medium.
        Property('adp', 'ADP', 'Adapter', 'marcrel'),

        # ANM/Animator: a person or organization who draws the two-dimensional
        #   figures, manipulates the three dimensional objects and/or also
        #   programs the computer to move objects and images for the purpose
        #   of animated film processing.
        Property('anm', 'ANM', 'Animator', 'marcrel'),

        # ANN/Annotator: a person who writes manuscript annotations on a printed item.
        Property('ann', 'ANN', 'Annotator', 'marcrel'),

        # ARC/Architect: a person or organization who designs structures or oversees
        #   their construction.
        Property('arc', 'ARC', 'Architect', 'marcrel'),

        # ARR/Arranger: a person or organization who transcribes a musical
        #   composition, usually for a different medium from that of the original;
        #   in an arrangement the musical substance remains essentially unchanged.
        Property('arr', 'ARR', 'Arranger', 'marcrel'),

        # ART/Artist: a person (e.g., a painter) or organization who conceives, and
        #   perhaps also implements, an original graphic design or work of art, if
        #   specific codes (e.g., [egr], [etr]) are not desired. For book illustrators,
        #   prefer Illustrator [ill].
        Property('art', 'ART', 'Artist', 'marcrel'),

        # AUT/Author: a person or organization chiefly responsible for the
        #   intellectual or artistic content of a work, usually printed text.
        Property('aut', 'AUT', 'Author', 'marcrel'),

        # AQT/Author in quotations or text extracts: a person or organization
        #   whose work is largely quoted or extracted in works to which he or
        #   she did not contribute directly.
        Property('aqt', 'AQT', 'Author in quotations or text extracts', 'marcrel'),

        # AFT/Author of afterword, colophon, etc.: a person or organization
        #   responsible for an afterword, postface, colophon, etc. but who
        #   is not the chief author of a work.
        Property('aft', 'AFT', 'Author of afterword, colophon, etc.', 'marcrel'),

        # AUD/Author of dialog: a person or organization responsible for
        #   the dialog or spoken commentary for a screenplay or sound
        #   recording.
        Property('aud', 'AUD', 'Author of dialog', 'marcrel'),

        # AUI/Author of introduction, etc.:  a person or organization
        #   responsible for an introduction, preface, foreword, or other
        #   critical introductory matter, but who is not the chief author.
        Property('aui', 'AUI', 'Author of introduction, etc.', 'marcrel'),

        # AUS/Author of screenplay, etc.:  a person or organization responsible
        #   for a motion picture screenplay, dialog, spoken commentary, etc.
        Property('aus', 'AUS', 'Author of screenplay, etc.', 'marcrel'),

        # CLL/Calligrapher: a person or organization who writes in an artistic
        #   hand, usually as a copyist and or engrosser.
        Property('cll', 'CLL', 'Calligrapher', 'marcrel'),

        # CTG/Cartographer: a person or organization responsible for the
        #   creation of maps and other cartographic materials.
        Property('ctg', 'CTG', 'Cartographer', 'marcrel'),

        # CHR/Choreographer: a person or organization who composes or arranges
        #   dances or other movements (e.g., "master of swords") for a musical
        #   or dramatic presentation or entertainment.
        Property('chr', 'CHR', 'Choreographer', 'marcrel'),

        # CNG/Cinematographer: a person or organization who is in charge of
        #   the images captured for a motion picture film. The cinematographer
        #   works under the supervision of a director, and may also be referred
        #   to as director of photography. Do not confuse with videographer.
        Property('cng', 'CNG', 'Cinematographer', 'marcrel'),

        # CLB/Collaborator: a person or organization that takes a limited part
        #   in the elaboration of a work of another person or organization that
        #   brings complements (e.g., appendices, notes) to the work.
        Property('clb', 'CLB', 'Collaborator', 'marcrel'),

        # CLT/Collotyper: a person or organization responsible for the production
        #   of photographic prints from film or other colloid that has ink-receptive
        #   and ink-repellent surfaces.
        Property('clt', 'CLT', 'Collotyper', 'marcrel'),

        # CMM/Commentator: a person or organization who provides interpretation,
        #   analysis, or a discussion of the subject matter on a recording,
        #   motion picture, or other audiovisual medium.
        Property('cmm', 'CMM', 'Commentator', 'marcrel'),

        # CWT/Commentator for written text: a person or organization responsible
        #   for the commentary or explanatory notes about a text. For the writer
        #   of manuscript annotations in a printed book, use Annotator [ann].
        Property('cwt', 'CWT', 'Commentator for written text', 'marcrel'),

        # COM/Compiler: a person or organization who produces a work or
        #   publication by selecting and putting together material from the
        #   works of various persons or bodies.
        Property('com', 'COM', 'Compiler', 'marcrel'),

        # CMP/Composer: a person or organization who creates a musical work,
        #   usually a piece of music in manuscript or printed form.
        Property('cmp', 'CMP', 'Composer', 'marcrel'),

        # CCP/Conceptor: a person or organization responsible for the original
        #   idea on which a work is based, this includes the scientific author
        #   of an audio-visual item and the conceptor of an advertisement.
        Property('ccp', 'CCP', 'Conceptor', 'marcrel'),

        # CND/Conductor: a person who directs a performing group (orchestra,
        #   chorus, opera, etc.) in a musical or dramatic presentation or
        #   entertainment.
        Property('cnd', 'CND', 'Conductor', 'marcrel'),

        # CSL/Consultant: a person or organization relevant to a resource, who
        #   is called upon for professional advice or services in a specialized
        #   field of knowledge or training.
        Property('csl', 'CSL', 'Consultant', 'marcrel'),

        # CSP/Consultant to a project: a person or organization relevant to a
        #   resource, who is engaged specifically to provide an intellectual
        #   overview of a strategic or operational task and by analysis,
        #   specification, or instruction, to create or propose a cost-effective
        #   course of action or solution.
        Property('csp', 'CSP', 'Consultant to a project', 'marcrel'),

        # CTR/Contractor: a person or organization relevant to a resource, who
        #   enters into a contract with another person or organization to
        #   perform a specific task.
        Property('ctr', 'CTR', 'Contractor', 'marcrel'),

        # CTB/Contributor: a person or organization one whose work has been
        #   contributed to a larger work, such as an anthology, serial
        #   publication, or other compilation of individual works. Do not
        #   use if the sole function in relation to a work is as author,
        #   editor, compiler or translator.
        # Note: this is in fact a refinement of dcterm:contributor, since
        # it is more specific than that one.
        Property('ctb', 'CTB', 'Contributor', 'marcrel'),

        # CRP/Correspondent: a person or organization who was either
        #   the writer or recipient of a letter or other communication.
        Property('crp', 'CRP', 'Correspondent', 'marcrel'),

        # CST/Costume designer: a person or organization who designs
        #   or makes costumes, fixes hair, etc., for a musical or
        #   dramatic presentation or entertainment.
        Property('cst', 'CST', 'Costume designer', 'marcrel'),

        # CRE/Creator: a person or organization responsible for the
        #   intellectual or artistic content of a work.
        Property('cre', 'CRE', 'Creator', 'marcrel'),

        # CUR/Curator of an exhibition: a person or organization
        #   responsible for conceiving and organizing an exhibition.
        Property('cur', 'CUR', 'Curator of an exhibition', 'marcrel'),

        # DNC/Dancer: a person or organization who principally
        #   exhibits dancing skills in a musical or dramatic
        #   presentation or entertainment.
        Property('dnc', 'DNC', 'Dancer', 'marcrel'),

        # DLN/Delineator: a person or organization executing technical
        #   drawings from others' designs.
        Property('dln', 'DLN', 'Delineator', 'marcrel'),

        # DSR/Designer: a person or organization responsible for the design
        #   if more specific codes (e.g., [bkd], [tyd]) are not desired.
        Property('dsr', 'DSR', 'Designer', 'marcrel'),

        # DRT/Director: a person or organization who is responsible for the
        #   general management of a work or who supervises the production of
        #   a performance for stage, screen, or sound recording.
        Property('drt', 'DRT', 'Director', 'marcrel'),

        # DIS/Dissertant: a person who presents a thesis for a university or
        #   higher-level educational degree.
        Property('dis', 'DIS', 'Dissertant', 'marcrel'),

        # DRM/Draftsman: a person or organization who prepares artistic or
        #   technical drawings.
        Property('drm', 'DRM', 'Draftsman', 'marcrel'),

        # EDT/Editor: a person or organization who prepares for publication
        #   a work not primarily his/her own, such as by elucidating text,
        #   adding introductory or other critical matter, or technically
        #   directing an editorial staff.
        Property('edt', 'EDT', 'Editor', 'marcrel'),

        # ENG/Engineer: a person or organization that is responsible for
        #   technical planning and design, particularly with construction.
        Property('eng', 'ENG', 'Engineer', 'marcrel'),

        # EGR/Engraver: a person or organization who cuts letters, figures,
        #   etc. on a surface, such as a wooden or metal plate, for printing.
        Property('egr', 'EGR', 'Engraver', 'marcrel'),

        # ETR/Etcher: a person or organization who produces text or images
        #   for printing by subjecting metal, glass, or some other surface
        #   to acid or the corrosive action of some other substance.
        Property('etr', 'ETR', 'Etcher', 'marcrel'),

        # FAC/Facsimilist: a person or organization that executed the facsimile.
        Property('fac', 'FAC', 'Facsimilist', 'marcrel'),

        # FLM/Film editor: a person or organization who is an editor of a
        #   motion picture film. This term is used regardless of the medium
        #   upon which the motion picture is produced or manufactured (e.g.,
        #   acetate film, video tape).
        Property('flm', 'FLM', 'Film editor', 'marcrel'),

        # FRG/Forger: a person or organization who makes or imitates something
        #   of value or importance, especially with the intent to defraud.
        Property('frg', 'FRG', 'Forger', 'marcrel'),

        # HST/Host: a person who is invited or regularly leads a program
        #   (often broadcast) that includes other guests, performers, etc.
        #   (e.g., talk show host).
        Property('hst', 'HST', 'Host', 'marcrel'),

        # ILU/Illuminator: a person or organization responsible for the
        #   decoration of a work (especially manuscript material) with
        #   precious metals or color, usually with elaborate designs and
        #   motifs.
        Property('ilu', 'ILU', 'Illuminator', 'marcrel'),

        # ILL/Illustrator: a person or organization who conceives, and
        #   perhaps also implements, a design or illustration, usually
        #   to accompany a written text.
        Property('ill', 'ILL', 'Illustrator', 'marcrel'),

        # ITR/Instrumentalist: a person or organization who principally
        #   plays an instrument in a musical or dramatic presentation
        #   or entertainment.
        Property('itr', 'ITR', 'Instrumentalist', 'marcrel'),

        # IVE/Interviewee: a person or organization who is interviewed
        #   at a consultation or meeting, usually by a reporter, pollster,
        #   or some other information gathering agent.
        Property('ive', 'IVE', 'Interviewee', 'marcrel'),

        # IVR/Interviewer: a person or organization who acts as a reporter,
        #   pollster, or other information gathering agent in a consultation
        #   or meeting involving one or more individuals.
        Property('ivr', 'IVR', 'Interviewer', 'marcrel'),

        # INV/Inventor: a person or organization who first produces a
        #   particular useful item, or develops a new process for
        #   obtaining a known item or result.
        Property('inv', 'INV', 'Inventor', 'marcrel'),

        # LSA/Landscape architect: a person or organization whose work
        #   involves coordinating the arrangement of existing and
        #   proposed land features and structures.
        Property('lsa', 'LSA', 'Landscape architect', 'marcrel'),

        # LBT/Librettist: a person or organization who is a writer of
        #   the text of an opera, oratorio, etc.
        Property('lbt', 'LBT', 'Librettist', 'marcrel'),

        # LGD/Lighting designer: a person or organization who designs the
        #   lighting scheme for a theatrical presentation, entertainment,
        #   motion picture, etc.
        Property('lgd', 'LGD', 'Lighting designer', 'marcrel'),

        # LTG/Lithographer: a person or organization who prepares the stone
        #   or plate for lithographic printing, including a graphic artist
        #   creating a design directly on the surface from which printing
        #   will be done.
        Property('ltg', 'LTG', 'Lithographer', 'marcrel'),

        # LYR/Lyricist: a person or organization who is the a writer of the
        #   text of a song.
        Property('lyr', 'LYR', 'Lyricist', 'marcrel'),

        # MFR/Manufacturer: a person or organization that makes an
        #   artifactual work (an object made or modified by one or
        #   more persons). Examples of artifactual works include vases,
        #   cannons or pieces of furniture.
        Property('mfr', 'MFR', 'Manufacturer', 'marcrel'),

        # MTE/Metal-engraver: a person or organization responsible for
        #   decorations, illustrations, letters, etc. cut on a metal
        #   surface for printing or decoration.
        Property('mte', 'MTE', 'Metal-engraver', 'marcrel'),

        # MOD/Moderator: a person who leads a program (often broadcast)
        #   where topics are discussed, usually with participation of
        #   experts in fields related to the discussion.
        Property('mod', 'MOD', 'Moderator', 'marcrel'),

        # MUS/Musician: a person or organization who performs music or
        #   contributes to the musical content of a work when it is not
        #   possible or desirable to identify the function more precisely.
        Property('mus', 'MUS', 'Musician', 'marcrel'),

        # NRT/Narrator: a person who is a speaker relating the particulars
        #   of an act, occurrence, or course of events.
        Property('nrt', 'NRT', 'Narrator', 'marcrel'),

        # ORM/Organizer of meeting: a person or organization responsible
        #   for organizing a meeting for which an item is the report or
        #   proceedings.
        Property('orm', 'ORM', 'Organizer of meeting', 'marcrel'),

        # ORG/Originator: a person or organization performing the work,
        #   i.e., the name of a person or organization associated with
        #   the intellectual content of the work. This category does not
        #   include the publisher or personal affiliation, or sponsor
        #   except where it is also the corporate author.
        Property('org', 'ORG', 'Originator', 'marcrel'),

        # PRF/Performer: a person or organization who exhibits musical
        #   or acting skills in a musical or dramatic presentation or
        #   entertainment, if specific codes for those functions ([act],
        #   [dnc], [itr], [voc], etc.) are not used. If specific codes
        #   are used, [prf] is used for a person whose principal skill
        #   is not known or specified.
        Property('prf', 'PRF', 'Performer', 'marcrel'),

        # PHT/Photographer: a person or organization responsible for
        #   taking photographs, whether they are used in their original
        #   form or as reproductions.
        Property('pht', 'PHT', 'Photographer', 'marcrel'),

        # PLT/Platemaker: a person or organization responsible for the
        #   production of plates, usually for the production of printed
        #   images and/or text.
        Property('plt', 'PLT', 'Platemaker', 'marcrel'),

        # PRM/Printmaker: a person or organization who makes a relief,
        #   intaglio, or planographic printing surface.
        Property('prm', 'PRM', 'Printmaker', 'marcrel'),

        # PRO/Producer: a person or organization responsible for the
        #   making of a motion picture, including business aspects,
        #   management of the productions, and the commercial success
        #   of the work.
        Property('pro', 'PRO', 'Producer', 'marcrel'),

        # PRD/Production personnel: a person or organization associated
        #   with the production (props, lighting, special effects, etc.)
        #   of a musical or dramatic presentation or entertainment.
        Property('prd', 'PRD', 'Production personnel', 'marcrel'),

        # PRG/Programmer: a person or organization responsible for the
        #   creation and/or maintenance of computer program design
        #   documents, source code, and machine-executable digital files
        #   and supporting documentation.
        Property('prg', 'PRG', 'Programmer', 'marcrel'),

        # PPT/Puppeteer: a person or organization who manipulates, controls,
        #   or directs puppets or marionettes in a musical or dramatic
        #   presentation or entertainment.
        Property('ppt', 'PPT', 'Puppeteer', 'marcrel'),

        # RCE/Recording engineer: a person or organization who supervises
        #   the technical aspects of a sound or video recording session.
        Property('rce', 'RCE', 'Recording engineer', 'marcrel'),

        # REN/Renderer: a person or organization who prepares drawings
        #   of architectural designs (i.e., renderings) in accurate,
        #   representational perspective to show what the project will
        #   look like when completed.
        Property('ren', 'REN', 'Renderer', 'marcrel'),

        # RPT/Reporter: a person or organization who writes or presents
        #   reports of news or current events on air or in print.
        Property('rpt', 'RPT', 'Reporter', 'marcrel'),

        # RTH/Research team head: a person who directed or managed a
        #   research project.
        Property('rth', 'RTH', 'Research team head', 'marcrel'),

        # RTM/Research team member:  a person who participated in a
        #   research project but whose role did not involve direction
        #   or management of it.
        Property('rtm', 'RTM', 'Research team member', 'marcrel'),

        # RES/Researcher: a person or organization responsible for
        #   performing research.
        Property('res', 'RES', 'Researcher', 'marcrel'),

        # RPY/Responsible party: a person or organization legally
        #   responsible for the content of the published material.
        Property('rpy', 'RPY', 'Responsible party', 'marcrel'),

        # RSG/Restager: a person or organization, other than the
        #   original choreographer or director, responsible for
        #   restaging a choreographic or dramatic work and who
        #   contributes minimal new content.
        Property('rsg', 'RSG', 'Restager', 'marcrel'),

        # REV/Reviewer:  a person or organization responsible for
        #   the review of a book, motion picture, performance, etc.
        Property('rev', 'REV', 'Reviewer', 'marcrel'),

        # SCE/Scenarist: a person or organization who is the author
        #   of a motion picture screenplay.
        Property('sce', 'SCE', 'Scenarist', 'marcrel'),

        # SAD/Scientific advisor: a person or organization who brings
        #   scientific, pedagogical, or historical competence to the
        #   conception and realization on a work, particularly in the
        #   case of audio-visual items.
        Property('sad', 'SAD', 'Scientific advisor', 'marcrel'),

        # SCR/Scribe: a person who is an amanuensis and for a writer of
        #   manuscripts proper. For a person who makes pen-facsimiles,
        #   use Facsimilist [fac].
        Property('scr', 'SCR', 'Scribe', 'marcrel'),

        # SCL/Sculptor: a person or organization who models or carves
        #   figures that are three-dimensional representations.
        Property('scl', 'SCL', 'Sculptor', 'marcrel'),

        # SEC/Secretary: a person or organization who is a recorder,
        #   redactor, or other person responsible for expressing the
        #   views of a organization.
        Property('sec', 'SEC', 'Secretary', 'marcrel'),

        # STD/Set designer:  a person or organization who translates the
        #   rough sketches of the art director into actual architectural
        #   structures for a theatrical presentation, entertainment, motion
        #   picture, etc. Set designers draw the detailed guides and
        #   specifications for building the set.
        Property('std', 'STD', 'Set designer', 'marcrel'),

        # SNG/Singer: a person or organization who uses his/her/their voice
        #   with or without instrumental accompaniment to produce music.
        #   A performance may or may not include actual words.
        Property('sng', 'SNG', 'Singer', 'marcrel'),

        # SPK/Speaker: a person who participates in a program (often broadcast)
        #   and makes a formalized contribution or presentation generally
        #   prepared in advance.
        Property('spk', 'SPK', 'Speaker', 'marcrel'),

        # STN/Standards body: an organization responsible for the development
        #   or enforcement of a standard.
        Property('stn', 'STN', 'Standards body', 'marcrel'),

        # STL/Storyteller: a person relaying a story with creative and/or
        #   theatrical interpretation.
        Property('stl', 'STL', 'Storyteller', 'marcrel'),

        # SRV/Surveyor: a person or organization who does measurements of
        #   tracts of land, etc. to determine location, forms, and boundaries.
        Property('srv', 'SRV', 'Surveyor', 'marcrel'),

        # TCH/Teacher: a person who, in the context of a resource, gives
        #   instruction in an intellectual subject or demonstrates while
        #   teaching physical skills.
        Property('tch', 'TCH', 'Teacher', 'marcrel'),

        # TRC/Transcriber: a person who prepares a handwritten or typewritten copy
        #   from original material, including from dictated or orally recorded
        #   material. For makers of pen-facsimiles, use Facsimilist [fac].
        Property('trc', 'TRC', 'Transcriber', 'marcrel'),

        # TRL/Translator: a person or organization who renders a text from one
        #   language into another, or from an older form of a language into the
        #   modern form.
        Property('trl', 'TRL', 'Translator', 'marcrel'),

        # VDG/Videographer: a person or organization in charge of a video production,
        #   e.g. the video recording of a stage production as opposed to a commercial
        #   motion picture. The videographer may be the camera operator or may
        #   supervise one or more camera operators. Do not confuse with cinematographer.
        Property('vdg', 'VDG', 'Videographer', 'marcrel'),

        # VOC/Vocalist: a person or organization who principally exhibits singing
        #   skills in a musical or dramatic presentation or entertainment.
        Property('voc', 'VOC', 'Vocalist', 'marcrel'),

        # WDE/Wood-engraver: a person or organization who makes prints by cutting
        #   the image in relief on the end-grain of a wood block.
        Property('wde', 'WDE', 'Wood-engraver', 'marcrel'),

        # WDC/Woodcutter: a person or organization who makes prints by cutting the
        #   image in relief on the plank side of a wood block.
        Property('wdc', 'WDC', 'Woodcutter', 'marcrel'),

        # WAM/Writer of accompanying material: a person or organization who writes
        #   significant material which accompanies a sound recording or other
        #   audiovisual material.
        Property('wam', 'WAM', 'Writer of accompanying material', 'marcrel'),

        # The following marcrel property term refines dcterm:publisher

        # DST/Distributor: a person or organization that has exclusive or shared
        #   marketing rights for an item.
        Property('dst', 'DST', 'Distributor', 'marcrel'),

        # The following 17 music21 property terms have historically been supported
        # by music21, so we must add them as standard property terms here:

        # textOriginalLanguage: original language of vocal/choral text
        Property('TXO', 'textOriginalLanguage', 'Original Text Language', 'music21'),

        # textLanguage: language of the encoded vocal/choral text
        Property('TXL', 'textLanguage', 'Text Language', 'music21'),

        # popularTitle: popular title
        Property('OTP', 'popularTitle', 'Popular Title', 'music21'),

        # parentTitle: parent title
        Property('OPR', 'parentTitle', 'Parent Title', 'music21'),

        # actNumber: act number (e.g. '2' or 'Act 2')
        Property('OAC', 'actNumber', 'Act Number', 'music21'),

        # sceneNumber: scene number (e.g. '3' or 'Scene 3')
        Property('OSC', 'sceneNumber', 'Scene Number', 'music21'),

        # movementNumber: movement number (e.g. '4', or 'mov. 4', or...)
        Property('OMV', 'movementNumber', 'Movement Number', 'music21'),

        # movementName: movement name (often a tempo description)
        Property('OMD', 'movementName', 'Movement Name', 'music21'),

        # opusNumber: opus number (e.g. '23', or 'Opus 23')
        Property('OPS', 'opusNumber', 'Opus Number', 'music21'),

        # number: number (e.g. '5', or 'No. 5')
        Property('ONM', 'number', 'Number', 'music21'),

        # volume: volume number (e.g. '6' or 'Vol. 6')
        Property('OVM', 'volume', 'Volume Number', 'music21'),

        # dedication: dedicated to
        Property('ODE', 'dedication', 'Dedicated To', 'music21'),

        # commission: commissioned by
        Property('OCO', 'commission', 'Commissioned By', 'music21'),

        # countryOfComposition: country of composition
        Property('OCY', 'countryOfComposition', 'Country of Composition', 'music21'),

        # localeOfComposition: city, town, or village of composition
        Property('OPC', 'localeOfComposition', 'Locale of Composition', 'music21'),

        # groupTitle: group title (e.g. 'The Seasons')
        Property('GTL', 'groupTitle', 'Group Title', 'music21'),

        # associatedWork: associated work, such as a play or film
        Property('GAW', 'associatedWork', 'Associated Work', 'music21'),
    )

    NSKEY2STDPROPERTY: dict = {f'{x.namespace}:{x.name}':x for x in STDPROPERTIES}

    CODE2NSKEY:      dict = {x[0]:f'{x.namespace}:{x.name}' for x in STDPROPERTIES}
    NAME2NSKEY:      dict = {x[1]:f'{x.namespace}:{x.name}' for x in STDPROPERTIES}
#     OLDABBREV2NSKEY: dict = {x[4]:f'{x.namespace}:{x.name}' for x in STDPROPERTIES if len(x) > 4}
#     OLDWORKID2NSKEY: dict = {x[5]:f'{x.namespace}:{x.name}' for x in STDPROPERTIES if len(x) > 5}

    STDPROPERTY_CODES:   Tuple[str, ...] = tuple(x.code for x in STDPROPERTIES)
    STDPROPERTY_NAMES:   Tuple[str, ...] = tuple(x.name for x in STDPROPERTIES)

    # Do we need to extend Dublin Core with some of the old "humdrum" property codes?  I hope not.

    # We should allow any random "personal" key/value pairs (these will also have the ability to
    # replace a key's value, or add a value to a key's list of values).

    # And then someday allow any new property code vocab to be specified, both property codes/names
    # and implied (or specified) encoding types.  Take a look at MEI to see what might be needed.
    # Hopefully this is where "humdrum:XXX" codes will go.

    # The parsers themselves are the ones responsible for putting together the
    # Dublin Core metadata plus their own ("this better stuff that lost info in
    # info in translation to Dublin Core").

    def __init__(self):
        # for now (experimental) use name for key, and either a single value
        # or a list (for more than one value)
        # So, where original metadata contained a contributors list, this new
        # metadata will have the potential of a list for any DublinCore property.
        # Values (whether in a list or not) can also be dictionaries, where the keys
        # are either DublinCore property keys, or our own ('music21') keys, (for
        # example, for contributor roles).
        super().__init__()
        self._metadata: Dict = {}

        # TODO: for backward compatibility, allow **keywords to specify keys that are
        # the old abbreviations and/or workIds.

    @staticmethod
    def nsKey(key: str, namespace: Optional[str] = None) -> str:
        if namespace:
            return f'{namespace}:{key}'

        if key in Metadata.STDPROPERTY_NAMES:
            return Metadata.NAME2NSKEY[key]

        if key in Metadata.STDPROPERTY_CODES:
            return Metadata.CODE2NSKEY[key]

        return key

    @staticmethod
    def propertyToNSKey(prop: Property) -> str:
        return Metadata.nsKey(prop.name, prop.namespace)

    @staticmethod
    def getPropertyDefinitionByNSKey(nsKey: str) -> Property:
        if not nsKey:
            return None
        return Metadata.NSKEY2STDPROPERTY.get(nsKey, None)

#     # Here are some examples of old APIs, implemented in terms of the new data structures
#     # for backward compatibility
#     @ property
#     def alternativeTitle(self):
#         r'''
#         Get or set the alternative title.
#
#         >>> md = metadata.Metadata(popularTitle='Eroica')
#         >>> md.alternativeTitle = 'Heroic Symphony'
#         >>> md.alternativeTitle
#         'Heroic Symphony'
#         '''
#         result = self._metadata.get(OLDWORKID2NSKEY['alternativeTitle'], None)
#         if result is not None:
#             return str(result)
#         return None
#
#     @alternativeTitle.setter
#     def alternativeTitle(self, value):
#         self._metadata[OLDWORKID2NSKEY['alternativeTitle']] = Text(value)

    # New APIs
    def getItem(self,
                key: str, # can be name, code, or namespace:name (if namespace is None)
                namespace: Optional[str] = None) -> Optional[Union[TextLiteral, Date, dict]]:
        nsKey: str = self.nsKey(key, namespace)
        return self._metadata.get(nsKey, None)

    # Values can be of type TextLiteral or Date (pass in a str, and we'll do a crappy
    # job of turning it into a TextLiteral)
    def addItem(self,
                key: str, # can be name, code, or namespace:name (if namespace is None)
                value: Union[TextLiteral, Date, str, dict],
                namespace: Optional[str] = None):
        if isinstance(value, str):
            value = TextLiteral(value)

        nsKey: str = self.nsKey(key, namespace)

        prevValue: Union[List, TextLiteral, Date, str, dict]
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

    def replaceItem(self,
                    key: str,
                    value: Union[TextLiteral, Date, str, dict],
                    namespace: Optional[str] = None):
        nsKey: str = self.nsKey(key, namespace)
        self._metadata.pop(nsKey)
        self.addItem(key, value, namespace)

    def getPersonalItem(self, key: str) -> Union[TextLiteral, Date, dict]:
        return self.getItem(key, namespace=None)

    def addPersonalItem(self, key: str, value: Union[TextLiteral, Date, str, dict]):
        self.addItem(key, value, namespace=None)

    def replacePersonalItem(self, key: str, value: Union[TextLiteral, Date, str, dict]):
        self.replaceItem(key, value, namespace=None)


class OldMetadata(base.Music21Object):
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
     'fileFormat', 'fileNumber', 'filePath',
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
        'fileFormat',
        'fileNumber',
        'filePath',
    ] + list(workIdAbbreviationDict.values())))

    workIdLookupDict = {}
    for key, value in workIdAbbreviationDict.items():
        workIdLookupDict[value.lower()] = key

    # INITIALIZER #

    def __init__(self, *args, **keywords):
        super().__init__()

        # a list of Contributor objects
        # there can be more than one composer, or any other combination
        self.contributors = []  # use addContributor to add.
        self._date = None

        # store one or more URLs from which this work came; this could
        # be local file paths or otherwise
        self._urls = []

        # TODO: need a specific object for imprint
        self._imprint = None

        self.software = [defaults.software]

        # Copyright can be None or a copyright object
        # TODO: Change to property to prevent setting as a plain string
        #     (but need to regenerate CoreCorpus() after doing so.)
        self.copyright = None

        # TODO: check pickling, etc.
        self.fileInfo = FileInfo()

        # a dictionary of Text elements, where keys are work id strings
        # all are loaded with None by default
        self._workIds = OrderedDict()
        for abbreviation, workId in self.workIdAbbreviationDict.items():
            # abbreviation = workIdToAbbreviation(id)
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

    # SPECIAL METHODS #
    def all(self, skipContributors=False):
        # noinspection SpellCheckingInspection, PyShadowingNames
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
         ('date', '1689/--/-- or earlier'),
         ('fileFormat', 'musicxml'),
         ('filePath', '...corpus/corelli/opus3no1/1grave.xml'),
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
                del allOut['title']

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
        result = self._workIds[match]
        # always return string representation for now
        return str(result)

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
        self.contributors.append(c)

    def getContributorsByRole(self, value):
        # noinspection PyShadowingNames
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
                self._workIds[workId] = Text(value)
                match = True
                break
            elif abbreviation == idStr:
                self._workIds[workId] = Text(value)
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
        result = self._workIds['alternativeTitle']
        if result is not None:
            return str(result)

    @alternativeTitle.setter
    def alternativeTitle(self, value):
        self._workIds['alternativeTitle'] = Text(value)

    def _contributor_role_getter(self, role: str) -> t.Optional[str]:
        '''
        get the name of the first contributor with this role, or None

        see composer property for an example
        '''
        result = self.getContributorsByRole(role)
        if result is not None:
            # get just the name of the first contributor
            return str(result[0].name)
        return None

    def _contributor_role_setter(self, role: str, name: str) -> None:
        '''
        set the name for a particular role, adding a new contributor
        in the process if none exists for that role.

        see composer.setter property for an example
        '''
        c = None

        result = self.getContributorsByRole(role)
        if result is not None:
            c = result[0]
        else:
            c = Contributor()
            c.role = role
            self.contributors.append(c)

        c.name = name

    def _contributor_multiple_role_getter(self, role: str) -> t.List[str]:
        '''
        get a list of the names of contributors with a certain role.

        see composers (plural) property for an example.
        '''
        result = self.getContributorsByRole(role)
        if result is not None:
            # get just the name of each composer/role
            return [x.name for x in result]
        else:
            return []

    def _contributor_multiple_role_setter(self, role: str, value: t.List[str]) -> None:
        '''
        set multiple names for a particular role, replacing the people
        already in those roles.

        see composers.setter (plural) property for an example.
        '''
        existing_contributors = self.getContributorsByRole(role)
        if existing_contributors:
            for existing in existing_contributors:
                self.contributors.remove(existing)

        for v in value:
            contrib = Contributor(role=role, name=v)
            self.addContributor(contrib)

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
        return self._contributor_role_getter('composer')

    @composer.setter
    def composer(self, value):
        self._contributor_role_setter('composer', value)

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
        return self._contributor_multiple_role_getter('composer')

    @composers.setter
    def composers(self, value: t.List[str]) -> None:
        self._contributor_multiple_role_setter('composer', value)


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
        return str(self._date)

    @date.setter
    def date(self, value):
        # all inherit date single
        if isinstance(value, DateSingle):
            self._date = value
        else:
            # assume date single; could be other subclass
            ds = DateSingle(value)
            self._date = ds

    @property
    def fileFormat(self) -> t.Optional[str]:
        '''
        Get or set the file format that was parsed.
        '''
        if self.fileInfo.format:
            return str(self.fileInfo.format)

    @fileFormat.setter
    def fileFormat(self, value: t.Union[str, Text]) -> None:
        self.fileInfo.format = Text(value)

    @property
    def filePath(self) -> t.Optional[str]:
        '''
        Get or set the file path that was parsed.
        '''
        if self.fileInfo.path:
            return str(self.fileInfo.path)

    @filePath.setter
    def filePath(self, value: t.Union[str, Text]) -> None:
        self.fileInfo.path = Text(value)

    @property
    def fileNumber(self) -> t.Optional[int]:
        '''
        Get or set the file path that was parsed.
        '''
        if self.fileInfo.number:
            return self.fileInfo.number

    @fileNumber.setter
    def fileNumber(self, value: t.Union[int, None]) -> None:
        self.fileInfo.number = value

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
        self._contributor_role_setter('librettist', value)

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
        return self._contributor_multiple_role_getter('librettist')

    @librettists.setter
    def librettists(self, value: t.List[str]) -> None:
        self._contributor_multiple_role_setter('librettist', value)



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
        return self._contributor_role_getter('lyricist')

    @lyricist.setter
    def lyricist(self, value):
        self._contributor_role_setter('lyricist', value)

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
        return self._contributor_multiple_role_getter('lyricist')

    @lyricists.setter
    def lyricists(self, value: t.List[str]) -> None:
        self._contributor_multiple_role_setter('lyricist', value)


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
        result = self._workIds['movementNumber']
        if result is not None:
            return str(result)
        return None

    @movementNumber.setter
    def movementNumber(self, value):
        self._workIds['movementNumber'] = Text(value)

    @property
    def number(self):
        r'''
        Get or set the number of the work within a collection of pieces.
        (for instance, the number within a collection of ABC files)

        Note that numbers are always returned as strings!  This may
        change in the future.
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

        Note that opusNumbers are always returned as strings!  This may
        change in the future.
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
    searchAttributes = tuple(sorted(OldMetadata.searchAttributes + (
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
