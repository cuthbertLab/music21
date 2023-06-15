# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         musicxml/m21ToXml.py
# Purpose:      Translate from music21 objects to musicxml representation
#
# Authors:      Michael Scott Asato Cuthbert
#               Christopher Ariza
#               Jacob Tyler Walls
#
# Copyright:    Copyright © 2010-22 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Converters for music21 objects to musicxml using ElementTree
'''
from __future__ import annotations

from collections import OrderedDict
import copy
import datetime
import fractions
import io
import math
import typing as t
import warnings
from xml.etree.ElementTree import (
    Element, SubElement, Comment
)

# external dependencies
import webcolors  # type: ignore  # no typing in module

# Imported in music21.converter. Thus, cannot import it here
from music21 import articulations
from music21 import base
from music21 import bar
from music21 import clef
from music21 import chord
from music21 import common
from music21.common.enums import AppendSpanners
from music21 import defaults
from music21 import duration
from music21 import dynamics
from music21 import environment
from music21 import exceptions21
from music21 import expressions
from music21 import harmony
from music21 import instrument
from music21 import key
from music21 import layout
from music21 import metadata
from music21 import note
from music21 import meter
from music21 import pitch
from music21 import prebase
from music21 import repeat
from music21 import spanner
from music21 import stream
from music21.stream.iterator import OffsetIterator
from music21 import style
from music21 import tempo
from music21 import text
from music21 import tie

from music21.musicxml import helpers
from music21.musicxml.partStaffExporter import PartStaffExporterMixin
from music21.musicxml import xmlObjects
from music21.musicxml.xmlObjects import MusicXMLExportException
from music21.musicxml.xmlObjects import MusicXMLWarning

environLocal = environment.Environment('musicxml.m21ToXml')


if t.TYPE_CHECKING:
    from music21.common.types import OffsetQL
    from music21 import roman
    from music21 import tablature

# ------------------------------------------------------------------------------

def typeToMusicXMLType(value: str) -> str:
    '''
    Convert a music21 type to a MusicXML type or raise a MusicXMLExportException

    >>> musicxml.m21ToXml.typeToMusicXMLType('longa')
    'long'
    >>> musicxml.m21ToXml.typeToMusicXMLType('quarter')
    'quarter'
    >>> musicxml.m21ToXml.typeToMusicXMLType('duplex-maxima')
    Traceback (most recent call last):
    music21.musicxml.xmlObjects.MusicXMLExportException:
    Cannot convert "duplex-maxima" duration to MusicXML (too long).
    >>> musicxml.m21ToXml.typeToMusicXMLType('inexpressible')
    Traceback (most recent call last):
    music21.musicxml.xmlObjects.MusicXMLExportException:
    Cannot convert inexpressible durations to MusicXML.
    >>> musicxml.m21ToXml.typeToMusicXMLType('zero')
    Traceback (most recent call last):
    music21.musicxml.xmlObjects.MusicXMLExportException:
    Cannot convert durations without types to MusicXML.
    '''
    # MusicXML uses long instead of longa
    if value == 'longa':
        return 'long'
    elif value == '2048th':
        raise MusicXMLExportException('Cannot convert "2048th" duration to MusicXML (too short).')
    elif value == 'duplex-maxima':
        raise MusicXMLExportException(
            'Cannot convert "duplex-maxima" duration to MusicXML (too long).')
    elif value == 'inexpressible':
        raise MusicXMLExportException('Cannot convert inexpressible durations to MusicXML.')
    elif value == 'complex':
        raise MusicXMLExportException(
            'Cannot convert complex durations to MusicXML. '
            + 'Try exporting with makeNotation=True or manually running splitAtDurations()')
    elif value == 'zero':
        raise MusicXMLExportException('Cannot convert durations without types to MusicXML.')
    else:
        return value


def normalizeColor(color: str) -> str:
    '''
    Normalize a css3 name to hex or leave it alone...

    >>> musicxml.m21ToXml.normalizeColor('')
    ''
    >>> musicxml.m21ToXml.normalizeColor('red')
    '#FF0000'
    >>> musicxml.m21ToXml.normalizeColor('#00ff00')
    '#00FF00'
    '''
    if not color:
        return ''
    if '#' not in color:
        return webcolors.name_to_hex(color).upper()
    else:
        return color.upper()


def getMetadataFromContext(s: stream.Stream) -> metadata.Metadata | None:
    # noinspection PyShadowingNames
    '''
    Get metadata from site or context, so that a Part
    can be shown and have the rich metadata of its Score

    >>> s = stream.Score()
    >>> s2 = s.transpose(4)
    >>> md = metadata.Metadata()
    >>> md.title = 'emptiness'
    >>> s.metadata = md
    >>> s2.metadata is None
    True
    >>> musicxml.m21ToXml.getMetadataFromContext(s2).title
    'emptiness'
    >>> musicxml.m21ToXml.getMetadataFromContext(s).title
    'emptiness'
    >>> p = stream.Part()
    >>> s2.insert(0, p)
    >>> musicxml.m21ToXml.getMetadataFromContext(p).title
    'emptiness'
    '''
    # get metadata from context.
    md = s.metadata
    if md is not None:
        return md

    for contextSite in s.contextSites():
        if contextSite.site.metadata is not None:
            return contextSite.site.metadata
    return None


def _setTagTextFromAttribute(
    m21El: t.Any,
    xmlEl: Element,
    tag: str,
    attributeName: str | None = None,
    *,
    transform: t.Callable[[t.Any], t.Any] | None = None,
    forceEmpty: bool = False
) -> Element | None:
    '''
    If m21El has an attribute called attributeName, create a new SubElement
    for xmlEl and set its text to the value of the m21El attribute.

    Pass a function or lambda function as transform to transform the
    value before setting it.  String transformation is assumed.

    Returns the SubElement

    Will not create an empty element unless forceEmpty is True

    >>> from xml.etree.ElementTree import Element
    >>> e = Element('accidental')

    >>> seta = musicxml.m21ToXml._setTagTextFromAttribute
    >>> acc = pitch.Accidental()
    >>> acc.alter = -2.0

    >>> subEl = seta(acc, e, 'alter')
    >>> subEl.text
    '-2.0'
    >>> subEl in e
    True

    >>> XB = musicxml.m21ToXml.XMLExporterBase()
    >>> XB.dump(e)
    <accidental>
      <alter>-2.0</alter>
    </accidental>

    add a transform

    >>> subEl = seta(acc, e, 'alter', transform=int)
    >>> subEl.text
    '-2'

    '''
    if attributeName is None:
        attributeName = common.hyphenToCamelCase(tag)

    try:
        value = getattr(m21El, attributeName)
    except AttributeError:
        return None

    if transform is not None:
        value = transform(value)

    if value in (None, '') and forceEmpty is not True:
        return None

    subElement = SubElement(xmlEl, tag)

    if value is not None:
        subElement.text = str(value)

    return subElement


def _setAttributeFromAttribute(
    m21El: t.Any,
    xmlEl: Element,
    xmlAttributeName: str,
    attributeName: str | None = None,
    transform: t.Callable[[t.Any], t.Any] | None = None
):
    '''
    If m21El has at least one element of tag==tag with some text. If
    it does, set the attribute either with the same name (with "foo-bar" changed to
    "fooBar") or with attributeName to the text contents.

    Pass a function or lambda function as transform to transform the value before setting it

    >>> from xml.etree.ElementTree import fromstring as El
    >>> e = El('<page-layout/>')

    >>> setb = musicxml.m21ToXml._setAttributeFromAttribute
    >>> pl = layout.PageLayout()
    >>> pl.pageNumber = 4
    >>> pl.isNew = True

    >>> setb(pl, e, 'page-number')
    >>> e.get('page-number')
    '4'

    >>> XB = musicxml.m21ToXml.XMLExporterBase()
    >>> XB.dump(e)
    <page-layout page-number="4" />

    >>> setb(pl, e, 'new-page', 'isNew')
    >>> e.get('new-page')
    'True'


    Transform the isNew value to 'yes'.

    >>> convBool = musicxml.xmlObjects.booleanToYesNo
    >>> setb(pl, e, 'new-page', 'isNew', transform=convBool)
    >>> e.get('new-page')
    'yes'
    '''
    if attributeName is None:
        attributeName = common.hyphenToCamelCase(xmlAttributeName)

    value = getattr(m21El, attributeName, None)
    if value is None:
        return

    if transform is not None:
        value = transform(value)

    xmlEl.set(xmlAttributeName, str(value))


def _synchronizeIds(element: Element,
                    m21Object: prebase.ProtoM21Object | None) -> None:
    # noinspection PyTypeChecker
    '''
    MusicXML 3.1 defines the id attribute (entity: %optional-unique-id)
    on many elements which is perfect for getting from .id on
    a music21 element.

    >>> from xml.etree.ElementTree import fromstring as El
    >>> e = El('<fermata />')
    >>> f = expressions.Fermata()
    >>> f.id = 'fermata1'
    >>> musicxml.m21ToXml._synchronizeIds(e, f)
    >>> e.get('id')
    'fermata1'

    Does not set attr: id if el.id is not valid or default:

    >>> e = El('<fermata />')
    >>> f = expressions.Fermata()
    >>> musicxml.m21ToXml._synchronizeIds(e, f)
    >>> e.get('id', None) is None
    True
    >>> f.id = '123456'  # invalid for MusicXML id
    >>> musicxml.m21ToXml._synchronizeIds(e, f)
    >>> e.get('id', None) is None
    True

    None can be passed in instead of a m21object.

    >>> e = El('<fermata />')
    >>> musicxml.m21ToXml._synchronizeIds(e, None)
    >>> e.get('id', 'no idea')
    'no idea'
    '''
    # had to suppress type-checking because of spurious error on
    #    e.get('id', 'no idea')
    if not isinstance(m21Object, prebase.ProtoM21Object):
        return
    if not hasattr(m21Object, 'id'):
        return

    m21Id = m21Object.id  # type: ignore

    if m21Id is None:
        return

    if not xmlObjects.isValidXSDID(m21Id):
        return
    element.set('id', m21Id)


class GeneralObjectExporter:
    '''
    Packs any `Music21Object` into a well-formed score and exports
    a bytes object MusicXML representation.
    '''
    classMapping = OrderedDict([
        ('Score', 'fromScore'),
        ('Part', 'fromPart'),
        ('Measure', 'fromMeasure'),
        ('Voice', 'fromVoice'),
        ('Stream', 'fromStream'),
        # ## individual parts
        ('GeneralNote', 'fromGeneralNote'),
        ('Pitch', 'fromPitch'),
        ('Duration', 'fromDuration'),  # not an m21 object
        ('Dynamic', 'fromDynamic'),
        ('DiatonicScale', 'fromDiatonicScale'),
        ('Scale', 'fromScale'),
        ('Music21Object', 'fromMusic21Object'),
    ])

    def __init__(self, obj: prebase.ProtoM21Object | None = None):
        self.generalObj = obj
        self.makeNotation: bool = True

    def parse(self, obj: prebase.ProtoM21Object | None = None) -> bytes:
        r'''
        Return a bytes object representation of anything from a
        Score to a single pitch.

        When :attr:`makeNotation` is True (default), wraps `obj` in a well-formed
        `Score`, makes a copy, and runs :meth:`~music21.stream.base.Stream.makeNotation`
        on each of the parts. To skip copying and making notation, set `.makeNotation`
        on this instance to False.

        >>> p = pitch.Pitch('D#4')
        >>> GEX = musicxml.m21ToXml.GeneralObjectExporter(p)
        >>> out = GEX.parse()  # out is bytes
        >>> outStr = out.decode('utf-8')  # now is string
        >>> print(outStr.strip())
        <?xml version="1.0" encoding="utf-8"?>
        <!DOCTYPE score-partwise
          PUBLIC "-//Recordare//DTD MusicXML ... Partwise//EN"
          "http://www.musicxml.org/dtds/partwise.dtd">
        <score-partwise version="...">
          <movement-title>Music21 Fragment</movement-title>
          <identification>
            <creator type="composer">Music21</creator>
            <encoding>
              <encoding-date>...</encoding-date>
              <software>music21 v...</software>
            </encoding>
          </identification>
          <defaults>
            <scaling>
              <millimeters>7</millimeters>
              <tenths>40</tenths>
            </scaling>
          </defaults>
          <part-list>
            <score-part id="...">
              <part-name />
            </score-part>
          </part-list>
          <!--=========================== Part 1 ===========================-->
          <part id="...">
            <!--========================= Measure 1 ==========================-->
            <measure implicit="no" number="1">
              <attributes>
                <divisions>10080</divisions>
                <time>
                  <beats>1</beats>
                  <beat-type>4</beat-type>
                </time>
                <clef>
                  <sign>G</sign>
                  <line>2</line>
                </clef>
              </attributes>
              <note>
                <pitch>
                  <step>D</step>
                  <alter>1</alter>
                  <octave>4</octave>
                </pitch>
                <duration>10080</duration>
                <type>quarter</type>
                <accidental>sharp</accidental>
              </note>
            </measure>
          </part>
        </score-partwise>
        '''
        if obj is None:
            obj = self.generalObj
        if obj is None:
            raise MusicXMLExportException('Must have an object to export')

        if self.makeNotation:
            outObj = self.fromGeneralObject(obj)
            return self.parseWellformedObject(outObj)
        else:
            if not isinstance(obj, stream.Score):
                raise MusicXMLExportException('Can only export Scores with makeNotation=False')
            return self.parseWellformedObject(obj)

    def parseWellformedObject(self, sc: stream.Score) -> bytes:
        '''
        Parse an object that has already gone through the
        `.fromGeneralObject` conversion, which has produced a copy with
        :meth:`~music21.stream.Score.makeNotation` run on it
        (unless :attr:`makeNotation` is False).

        Returns bytes.
        '''
        scoreExporter = ScoreExporter(sc, makeNotation=self.makeNotation)
        scoreExporter.parse()
        return scoreExporter.asBytes()

    def fromGeneralObject(self, obj: prebase.ProtoM21Object):
        '''
        Converts any Music21Object (or a duration or a pitch) to something that
        can be passed to :class:`ScoreExporter`.

        >>> GEX = musicxml.m21ToXml.GeneralObjectExporter()
        >>> s = GEX.fromGeneralObject(duration.Duration(3.0))
        >>> s
        <music21.stream.Score 0x...>
        >>> s.show('t')
        {0.0} <music21.stream.Part 0x...>
            {0.0} <music21.stream.Measure 1 offset=0.0>
                {0.0} <music21.clef.TrebleClef>
                {0.0} <music21.meter.TimeSignature 6/8>
                {0.0} <music21.note.Note C>
                {3.0} <music21.bar.Barline type=final>
        >>> s[note.NotRest].first().duration
        <music21.duration.Duration 3.0>

        * Changed in v8: fills gaps with rests before calling makeNotation
          to avoid duplicating effort with :meth:`PartExporter.fixupNotationMeasured`.

        >>> v = stream.Voice(note.Note())
        >>> m = stream.Measure([meter.TimeSignature(), v])
        >>> GEX = musicxml.m21ToXml.GeneralObjectExporter(m)
        >>> out = GEX.parse()  # out is bytes
        >>> outStr = out.decode('utf-8')  # now is string
        >>> '<note print-object="no" print-spacing="yes">' in outStr
        True
        >>> len(v[note.Rest])  # original stream unchanged
        0
        '''
        classes = obj.classes
        outObj = None

        if isinstance(obj, stream.Stream) and self.makeNotation:
            # This is where the first (and hopefully only) copy is made.
            obj = obj.makeRests(refStreamOrTimeRange=[0.0, obj.highestTime],
                                fillGaps=True,
                                inPlace=False,
                                hideRests=True,  # just to fill up MusicXML display
                                timeRangeFromBarDuration=True,
                                )

        for cM, methName in self.classMapping.items():
            if cM in classes:
                meth = getattr(self, methName)
                outObj = meth(obj)
                break
        if outObj is None:
            raise MusicXMLExportException(
                'Cannot translate the object '
                + f'{self.generalObj} to a complete musicXML document; put it in a Stream first!'
            )
        return outObj

    def fromScore(self, sc):
        '''
        Runs :meth:`~music21.stream.Score.makeNotation` on the copy.
        '''
        if self.makeNotation:
            sc.makeNotation(inPlace=True)
        if not sc.isWellFormedNotation():
            warnings.warn(f'{sc} is not well-formed; see isWellFormedNotation()',
                category=MusicXMLWarning)
        # sc.makeImmutable()
        return sc

    def fromPart(self, p):
        '''
        From a part, put it in a new score.
        '''
        if p.isFlat:
            p.makeMeasures(inPlace=True)
        # p.makeImmutable()  # impossible, we haven't made notation yet.
        s = stream.Score()
        s.insert(0, p)
        s.metadata = copy.deepcopy(getMetadataFromContext(p))
        return self.fromScore(s)

    def fromMeasure(self, m):
        '''
        Translate a music21 Measure into a
        complete MusicXML string representation.

        Note: this method is called for complete MusicXML
        representation of a Measure, not for partial
        solutions in Part or Stream production.
        '''
        m.coreGatherMissingSpanners()
        m.makeNotation(inPlace=True)
        if m.style.measureNumbering is None:
            # Provide a default
            m.style.measureNumbering = 'measure'
        clef_from_measure_start_or_context = m.getContextByClass(
            clef.Clef,
            getElementMethod=common.enums.ElementSearch.AT_OR_BEFORE_OFFSET
        )
        if clef_from_measure_start_or_context is None:
            m.clef = clef.bestClef(m, recurse=True)
        else:
            m.clef = clef_from_measure_start_or_context
        p = stream.Part()
        p.append(m)
        p.metadata = copy.deepcopy(getMetadataFromContext(m))
        context_part = m.getContextByClass(stream.Part)
        if context_part is not None:
            p.partName = context_part.partName
            p.partAbbreviation = context_part.partAbbreviation
        return self.fromPart(p)

    def fromVoice(self, v):
        m = stream.Measure(number=1)
        m.insert(0, v)
        return self.fromMeasure(m)

    def fromStream(self, st):
        if st.isFlat:
            st2 = stream.Part()
            st2.mergeAttributes(st)
            st2.elements = copy.deepcopy(st)
            if not st.getElementsByClass(clef.Clef).getElementsByOffset(0.0):
                st2.clef = clef.bestClef(st2)
            st2.makeNotation(inPlace=True)
            st2.metadata = copy.deepcopy(getMetadataFromContext(st))
            return self.fromPart(st2)

        elif st.hasPartLikeStreams():
            st2 = stream.Score()
            st2.mergeAttributes(st)
            st2.elements = copy.deepcopy(st)
            st2.makeNotation(inPlace=True)
            st2.metadata = copy.deepcopy(getMetadataFromContext(st))
            return self.fromScore(st2)

        elif st.getElementsByClass(stream.Stream).first().isFlat:  # like a part w/ measures...
            st2 = stream.Part()
            st2.mergeAttributes(st)
            st2.elements = copy.deepcopy(st)
            if not st.getElementsByClass(clef.Clef).getElementsByOffset(0.0):
                bestClef = True
            else:
                bestClef = False
            st2.makeNotation(inPlace=True, bestClef=bestClef)
            st2.metadata = copy.deepcopy(getMetadataFromContext(st))
            return self.fromPart(st2)

        else:
            # probably a problem? or a voice...
            if not st.getElementsByClass(clef.Clef).getElementsByOffset(0.0):
                bestClef = True
            else:
                bestClef = False
            st2 = st.makeNotation(inPlace=False, bestClef=bestClef)
            return self.fromScore(st)

    def fromDuration(self, d):
        '''
        Translate a music21 :class:`~music21.duration.Duration` into
        a complete MusicXML representation.

        Rarely, rarely used.  Only if you call .show() on a duration object
        '''
        # make a copy, as we this process will change tuple types
        # not needed, since fromGeneralNote does it too.  but so
        # rarely used, it doesn't matter, and the extra safety is nice.
        dCopy = copy.deepcopy(d)
        n = note.Note()
        n.duration = dCopy
        # call the musicxml property on Stream
        return self.fromGeneralNote(n)

    def fromDynamic(self, dynamicObject):
        '''
        Provide a complete MusicXML string from a single dynamic by
        putting it into a Stream first.

        '''
        dCopy = copy.deepcopy(dynamicObject)
        out = stream.Stream()
        out.append(dCopy)
        # call the musicxml property on Stream
        return self.fromStream(out)

    def fromScale(self, scaleObject):
        # noinspection PyShadowingNames
        '''
        Generate the pitches from this scale
        and put it into a stream.Measure, then call
        fromMeasure on it.

        >>> cMaj = scale.MajorScale('C')
        >>> GEX = musicxml.m21ToXml.GeneralObjectExporter()
        >>> m = GEX.fromScale(cMaj)
        >>> m
        <music21.stream.Score 0x11d4f17b8>

        >>> m.show('text')
        {0.0} <music21.stream.Part 0x116a04b38>
            {0.0} <music21.stream.Measure 1 offset=0.0>
                {0.0} <music21.clef.TrebleClef>
                {0.0} <music21.meter.TimeSignature 10/4>
                {0.0} <music21.note.Note C>
                {4.0} <music21.note.Note D>
                {5.0} <music21.note.Note E>
                {6.0} <music21.note.Note F>
                {7.0} <music21.note.Note G>
                {8.0} <music21.note.Note A>
                {9.0} <music21.note.Note B>
        '''
        m = stream.Measure(number=1)
        for i in range(1, scaleObject.abstract.getDegreeMaxUnique() + 1):
            p = scaleObject.pitchFromDegree(i)
            n = note.Note()
            n.pitch = p
            if i == 1:
                n.addLyric(scaleObject.name)

            if p.name == scaleObject.getTonic().name:
                n.quarterLength = 4  # set longer
            else:
                n.quarterLength = 1
            m.append(n)
        m.timeSignature = m.bestTimeSignature()
        return self.fromMeasure(m)

    def fromDiatonicScale(self, diatonicScaleObject):
        # noinspection PyShadowingNames
        '''
        Return a complete musicxml of the DiatonicScale

        Overrides the general scale behavior to highlight
        the tonic and dominant.

        >>> cMaj = scale.MajorScale('C')
        >>> GEX = musicxml.m21ToXml.GeneralObjectExporter()
        >>> m = GEX.fromDiatonicScale(cMaj)
        >>> m
        <music21.stream.Score 0x11d4f17b8>

        >>> m.show('text')
        {0.0} <music21.stream.Part 0x116a04b38>
            {0.0} <music21.stream.Measure 1 offset=0.0>
                {0.0} <music21.clef.TrebleClef>
                {0.0} <music21.meter.TimeSignature 11/4>
                {0.0} <music21.note.Note C>
                {4.0} <music21.note.Note D>
                {5.0} <music21.note.Note E>
                {6.0} <music21.note.Note F>
                {7.0} <music21.note.Note G>
                {9.0} <music21.note.Note A>
                {10.0} <music21.note.Note B>
        '''
        m = stream.Measure(number=1)
        for i in range(1, diatonicScaleObject.abstract.getDegreeMaxUnique() + 1):
            p = diatonicScaleObject.pitchFromDegree(i)
            n = note.Note()
            n.pitch = p
            if i == 1:
                n.addLyric(diatonicScaleObject.name)

            if p.name == diatonicScaleObject.getTonic().name:
                n.quarterLength = 4  # set longer
            elif p.name == diatonicScaleObject.getDominant().name:
                n.quarterLength = 2  # set longer
            else:
                n.quarterLength = 1
            m.append(n)
        m.timeSignature = m.bestTimeSignature()
        return self.fromMeasure(m)

    def fromMusic21Object(self, obj):
        '''
        return a single TimeSignature as a musicxml document
        '''
        # return a complete musicxml representation
        objCopy = copy.deepcopy(obj)
        # m = stream.Measure()
        # m.timeSignature = tsCopy
        # m.append(note.Rest())
        out = stream.Measure(number=1)
        out.append(objCopy)
        return self.fromMeasure(out)

    def fromGeneralNote(self, n):
        # noinspection PyShadowingNames
        '''
        Translate a music21 :class:`~music21.note.Note` into an object
        ready to be parsed.

        An attempt is made to find the best TimeSignature for quarterLengths
        <= 6:

        >>> n = note.Note('c3')
        >>> n.quarterLength = 3
        >>> GEX = musicxml.m21ToXml.GeneralObjectExporter()
        >>> sc = GEX.fromGeneralNote(n)
        >>> sc.show('t')
        {0.0} <music21.stream.Part 0x1046afa90>
            {0.0} <music21.stream.Measure 1 offset=0.0>
                {0.0} <music21.clef.BassClef>
                {0.0} <music21.meter.TimeSignature 6/8>
                {0.0} <music21.note.Note C>
                {3.0} <music21.bar.Barline type=final>

        But longer notes will be broken into tied components placed in
        4/4 measures:

        >>> long_note = note.Note('e5', quarterLength=40)
        >>> GEX = musicxml.m21ToXml.GeneralObjectExporter()
        >>> sc = GEX.fromGeneralNote(long_note)
        >>> sc[meter.TimeSignature].first()
        <music21.meter.TimeSignature 4/4>
        >>> len(sc[stream.Measure])
        10
        '''
        # make a copy, as this process will change tuple types
        # this method is called infrequently (only displaying a single note)
        nCopy = copy.deepcopy(n)
        new_part = stream.Part(nCopy)
        if 0 < n.quarterLength <= 6.0:
            new_part.insert(0, meter.bestTimeSignature(new_part))
        stream.makeNotation.makeMeasures(
            new_part,
            inPlace=True,
            refStreamOrTimeRange=[0, nCopy.quarterLength]
        )
        stream.makeNotation.makeTupletBrackets(new_part, inPlace=True)
        return self.fromPart(new_part)

    def fromPitch(self, p: pitch.Pitch):
        # noinspection PyShadowingNames
        '''
        Translate a music21 :class:`~music21.pitch.Pitch` into an object
        ready to be parsed.

        >>> p = pitch.Pitch('c#3')
        >>> GEX = musicxml.m21ToXml.GeneralObjectExporter()
        >>> sc = GEX.fromPitch(p)
        >>> sc.show('t')
        {0.0} <music21.stream.Part 0x1046afa90>
            {0.0} <music21.stream.Measure 1 offset=0.0>
                {0.0} <music21.clef.BassClef>
                {0.0} <music21.meter.TimeSignature 1/4>
                {0.0} <music21.note.Note C#>
        '''
        n = note.Note()
        n.pitch = copy.deepcopy(p)
        out = stream.Measure(number=1)
        out.append(n)
        # call the musicxml property on Stream
        return self.fromMeasure(out)


class XMLExporterBase:
    '''
    contains functions that could be called
    at multiple levels of exporting (Score, Part, Measure).
    '''
    def __init__(self) -> None:
        self.xmlRoot = Element('override-me-in-subclasses')
        self.stream: stream.Stream = stream.Stream()

    def asBytes(self, noCopy=True) -> bytes:
        '''
        returns the xmlRoot as a bytes object. If noCopy is True
        (default), modifies the file for pretty-printing in place.  Otherwise,
        make a copy.
        '''
        sio = io.BytesIO()
        sio.write(self.xmlHeader())
        rootObj = self.xmlRoot
        rootObj_string = helpers.dumpString(rootObj, noCopy=noCopy)
        sio.write(rootObj_string.encode('utf-8'))
        v = sio.getvalue()
        sio.close()
        return v

    def addDividerComment(self, comment: str = '') -> None:
        '''
        Add a divider to xmlRoot.

        >>> from xml.etree.ElementTree import Element
        >>> e1 = Element('accidental')
        >>> e2 = Element('accidental')

        >>> XB = musicxml.m21ToXml.ScoreExporter()
        >>> XB.xmlRoot.append(e1)
        >>> XB.addDividerComment('second accidental below')
        >>> XB.xmlRoot.append(e2)
        >>> XB.dump(XB.xmlRoot)
        <score-partwise version="...">
          <accidental />
          <!--================== second accidental below ===================-->
          <accidental />
          </score-partwise>
        '''
        commentLength = min(len(comment), 60)
        spacerLengthLow = math.floor((60 - commentLength) / 2)
        spacerLengthHigh = math.ceil((60 - commentLength) / 2)

        commentText = ('=' * spacerLengthLow) + ' ' + comment + ' ' + ('=' * spacerLengthHigh)

        divider = Comment(commentText)
        self.xmlRoot.append(divider)

    # ------------------------------------------------------------------------------
    @staticmethod
    def dump(obj):
        return helpers.dump(obj)

    def xmlHeader(self) -> bytes:
        return (b'''<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE score-partwise  '''
                + b'''PUBLIC "-//Recordare//DTD MusicXML '''
                + defaults.musicxmlVersion.encode('utf-8')
                + b''' Partwise//EN" '''
                + b'''"http://www.musicxml.org/dtds/partwise.dtd">\n''')

    # style attributes

    def setStyleAttributes(self, mxObject, m21Object, musicXMLNames, m21Names=None):
        '''
        Sets any attribute from .style, doing some conversions.

        m21Object can also be a style.Style object itself.
        '''
        if isinstance(m21Object, style.Style):
            stObj = m21Object
        elif m21Object.hasStyleInformation is False:
            return
        else:
            stObj = m21Object.style

        if not common.isIterable(musicXMLNames):
            musicXMLNames = (musicXMLNames,)

        if m21Names is None:
            m21Names = (common.hyphenToCamelCase(x) for x in musicXMLNames)
        elif not common.isIterable(m21Names):
            m21Names = (m21Names,)

        for xmlName, m21Name in zip(musicXMLNames, m21Names):
            try:
                m21Value = getattr(stObj, m21Name)
            except AttributeError:
                continue

            if m21Name in xmlObjects.STYLE_ATTRIBUTES_STR_NONE_TO_NONE and m21Value is None:
                m21Value = 'none'
            if m21Name in xmlObjects.STYLE_ATTRIBUTES_YES_NO_TO_BOOL:
                m21Value = xmlObjects.booleanToYesNo(m21Value)

            if m21Value is None:
                continue

            try:
                m21Value = str(m21Value)
            except ValueError:
                continue

            mxObject.set(xmlName, m21Value)

    def setTextFormatting(self, mxObject, m21Object):
        '''
        sets the justification, print-style-align group, and
        text-decoration, text-rotation,
        letter-spacing, line-height, lang, text-direction, and
        enclosure, on an
        m21Object, which must have style.TextStyle as its Style class,
        and then calls setPrintStyleAlign

        conforms to attr-group %text-formatting in the MusicXML DTD
        '''
        musicXMLNames = ('justify', 'text-decoration', 'text-rotation', 'letter-spacing',
                         'line-height', 'lang', 'text-direction', 'enclosure')
        m21Names = ('justify', 'textDecoration', 'textRotation', 'letterSpacing',
                    'lineHeight', 'language', 'textDirection', 'enclosure')
        self.setStyleAttributes(mxObject, m21Object, musicXMLNames, m21Names)
        self.setPrintStyleAlign(mxObject, m21Object)

    def setPrintStyleAlign(self, mxObject, m21Object):
        '''
        runs setPrintStyle and then sets horizontalAlign and verticalAlign, on an
        m21Object, which must have style.TextStyle as its Style class.

        conforms to attr-group %print-style-align in the MusicXML DTD
        '''
        self.setPrintStyle(mxObject, m21Object)
        self.setStyleAttributes(mxObject,
                                m21Object,
                                ('valign', 'halign'),
                                ('alignVertical', 'alignHorizontal'))

    def setPrintStyle(self, mxObject, m21Object):
        '''
        get position, font, and color information from the mxObject
        into the m21Object, which must have style.TextStyle as its Style class.

        conforms to attr-group %print-style in the MusicXML DTD
        '''
        self.setPosition(mxObject, m21Object)
        self.setFont(mxObject, m21Object)
        self.setColor(mxObject, m21Object)

    def setPrintObject(self, mxObject, m21Object):
        '''
        sets print-object to 'no' if m21Object.style.hideObjectOnPrint is True
        or if m21Object is a StyleObject and has .hideObjectOnPrint set to True.
        '''
        if isinstance(m21Object, style.Style):
            st = m21Object
        elif m21Object.hasStyleInformation:
            st = m21Object.style
        else:
            return

        if st.hideObjectOnPrint:
            mxObject.set('print-object', 'no')

    def setColor(self, mxObject, m21Object):
        '''
        Sets mxObject['color'] to a normalized version of m21Object.style.color
        '''
        # we repeat 'color' rather than just letting setStyleAttributes
        # handle it, because otherwise it will run the expensive
        # hyphenToCamelCase routine on something called on each note.
        self.setStyleAttributes(mxObject, m21Object, 'color', 'color')
        if 'color' in mxObject.attrib:  # set
            mxObject.attrib['color'] = normalizeColor(mxObject.attrib['color'])

    def setFont(self, mxObject, m21Object):
        '''
        sets font-family, font-style, font-size, and font-weight as
        fontFamily (list), fontStyle, fontSize and fontWeight from
        an object into a TextStyle object

        conforms to attr-group %font in the MusicXML DTD

        >>> from xml.etree.ElementTree import fromstring as El
        >>> XB = musicxml.m21ToXml.XMLExporterBase()
        >>> mxObj = El('<text>hi</text>')
        >>> te = expressions.TextExpression('hi!')
        >>> te.style.fontFamily = ['Courier', 'monospaced']
        >>> te.style.fontStyle = 'italic'
        >>> te.style.fontSize = 24.0
        >>> XB.setFont(mxObj, te)
        >>> XB.dump(mxObj)
        <text font-family="Courier,monospaced" font-size="24" font-style="italic">hi</text>

        >>> XB = musicxml.m21ToXml.XMLExporterBase()
        >>> mxObj = El('<text>hi</text>')
        >>> te = expressions.TextExpression('hi!')
        >>> te.style.fontStyle = 'bold'
        >>> XB.setFont(mxObj, te)
        >>> XB.dump(mxObj)
        <text font-weight="bold">hi</text>

        >>> te.style.fontStyle = 'bolditalic'
        >>> XB.setFont(mxObj, te)
        >>> XB.dump(mxObj)
        <text font-style="italic" font-weight="bold">hi</text>
        '''
        musicXMLNames = ('font-style', 'font-size', 'font-weight')
        m21Names = ('fontStyle', 'fontSize', 'fontWeight')
        self.setStyleAttributes(mxObject, m21Object, musicXMLNames, m21Names)
        if isinstance(m21Object, style.Style):
            st = m21Object
        elif m21Object.hasStyleInformation:
            st = m21Object.style
        else:
            return

        if hasattr(st, 'fontStyle'):
            # mxml does not support bold or bolditalic as font-style value
            if st.fontStyle == 'bold':
                mxObject.set('font-weight', 'bold')
                mxObject.attrib.pop('font-style', None)
            elif st.fontStyle == 'bolditalic':
                mxObject.set('font-weight', 'bold')
                mxObject.set('font-style', 'italic')

        if hasattr(st, 'fontFamily') and st.fontFamily:
            if common.isIterable(st.fontFamily):
                mxObject.set('font-family', ','.join(st.fontFamily))
            else:
                mxObject.set('font-family', st.fontFamily)

    def setPosition(self, mxObject, m21Object):
        '''
        set positioning information for an mxObject from
        default-x, default-y, relative-x, relative-y from
        the .style attribute's absoluteX, relativeX, etc. attributes.
        '''
        musicXMLNames = ('default-x', 'default-y', 'relative-x', 'relative-y')
        m21Names = ('absoluteX', 'absoluteY', 'relativeX', 'relativeY')
        self.setStyleAttributes(mxObject, m21Object, musicXMLNames, m21Names)

    def setEditorial(self, mxObject, m21Object):
        '''
        >>> from xml.etree.ElementTree import fromstring as El
        >>> XB = musicxml.m21ToXml.XMLExporterBase()
        >>> mxObj = El('<note />')
        >>> n = note.Note('C-5')

        Most common case: does nothing

        >>> XB.setEditorial(mxObj, n)
        >>> XB.dump(mxObj)
        <note />

        >>> fn = editorial.Comment('flat is obvious error for sharp')
        >>> fn.levelInformation = 2
        >>> fn.isFootnote = True
        >>> n.editorial.footnotes.append(fn)
        >>> XB.setEditorial(mxObj, n)
        >>> XB.dump(mxObj)
        <note>
          <footnote>flat is obvious error for sharp</footnote>
          <level reference="no">2</level>
        </note>

        Placing information in `.editorial.comments` only puts out the level:

        >>> mxObj = El('<note />')
        >>> n = note.Note('C-5')
        >>> com = editorial.Comment('flat is obvious error for sharp')
        >>> com.levelInformation = 'hello'
        >>> com.isReference = True
        >>> n.editorial.comments.append(com)
        >>> XB.setEditorial(mxObj, n)
        >>> XB.dump(mxObj)
        <note>
          <level reference="yes">hello</level>
        </note>
        '''
        if m21Object.hasEditorialInformation is False:
            return
        # MusicXML allows only one footnote or level, so we take the first...

        e = m21Object.editorial
        if 'footnotes' not in e and 'comments' not in e:
            return

        makeFootnote = False
        if e.footnotes:
            c = e.footnotes[0]
            makeFootnote = True
        elif e.comments:
            c = e.comments[0]
        else:
            return

        if makeFootnote:
            mxFn = SubElement(mxObject, 'footnote')
            self.setTextFormatting(mxFn, c)
            if c.text is not None:
                mxFn.text = c.text
        if c.levelInformation is not None:
            mxLevel = SubElement(mxObject, 'level')
            mxLevel.text = str(c.levelInformation)
            mxLevel.set('reference', xmlObjects.booleanToYesNo(c.isReference))
            # TODO: attr: parentheses
            # TODO: attr: bracket
            # TODO: attr: size

    ###################

    def pageLayoutToXmlPrint(self, pageLayout, mxPrintIn=None):
        # noinspection PyShadowingNames
        '''
        Given a PageLayout object, set object data for <print>

        >>> pl = layout.PageLayout()
        >>> pl.pageHeight = 4000
        >>> pl.isNew = True
        >>> pl.rightMargin = 30.25
        >>> pl.leftMargin = 20
        >>> pl.pageNumber = 5

        >>> XPBase = musicxml.m21ToXml.XMLExporterBase()
        >>> mxPrint = XPBase.pageLayoutToXmlPrint(pl)
        >>> XPBase.dump(mxPrint)
        <print new-page="yes" page-number="5">
          <page-layout>
            <page-height>4000</page-height>
            <page-margins>
              <left-margin>20</left-margin>
              <right-margin>30.25</right-margin>
            </page-margins>
          </page-layout>
        </print>


        >>> MP = musicxml.xmlToM21.MeasureParser()
        >>> pl2 = MP.xmlPrintToPageLayout(mxPrint)
        >>> pl2.isNew
        True
        >>> pl2.rightMargin
        30.25
        >>> pl2.leftMargin
        20
        >>> pl2.pageNumber
        5
        >>> pl2.pageHeight
        4000
        '''
        if mxPrintIn is None:
            mxPrint = Element('print')
        else:
            mxPrint = mxPrintIn

        setb = _setAttributeFromAttribute
        setb(pageLayout, mxPrint, 'new-page', 'isNew', transform=xmlObjects.booleanToYesNo)
        setb(pageLayout, mxPrint, 'page-number')

        mxPageLayout = self.pageLayoutToXmlPageLayout(pageLayout)
        if mxPageLayout:
            mxPrint.append(mxPageLayout)

        if mxPrintIn is None:
            return mxPrint

    def pageLayoutToXmlPageLayout(self, pageLayout, mxPageLayoutIn=None):
        '''
        get a <page-layout> element from a PageLayout

        Called out from pageLayoutToXmlPrint because it
        is also used in the <defaults> tag
        '''
        if mxPageLayoutIn is None:
            mxPageLayout = Element('page-layout')
        else:
            mxPageLayout = mxPageLayoutIn

        seta = _setTagTextFromAttribute

        seta(pageLayout, mxPageLayout, 'page-height')
        seta(pageLayout, mxPageLayout, 'page-width')

        # TODO -- record even, odd, both margins
        mxPageMargins = Element('page-margins')
        for direction in ('left', 'right', 'top', 'bottom'):
            seta(pageLayout, mxPageMargins, direction + '-margin')
        if mxPageMargins:
            mxPageLayout.append(mxPageMargins)

        if mxPageLayoutIn is None:
            return mxPageLayout

    def systemLayoutToXmlPrint(self, systemLayout, mxPrintIn=None):
        # noinspection PyShadowingNames
        '''
        Given a SystemLayout tag, set a <print> tag

        >>> sl = layout.SystemLayout()
        >>> sl.distance = 55
        >>> sl.isNew = True
        >>> sl.rightMargin = 30.25
        >>> sl.leftMargin = 20

        >>> XPBase = musicxml.m21ToXml.XMLExporterBase()
        >>> mxPrint = XPBase.systemLayoutToXmlPrint(sl)
        >>> XPBase.dump(mxPrint)
        <print new-system="yes">
          <system-layout>
            <system-margins>
              <left-margin>20</left-margin>
              <right-margin>30.25</right-margin>
            </system-margins>
            <system-distance>55</system-distance>
          </system-layout>
        </print>


        Test return conversion

        >>> MP = musicxml.xmlToM21.MeasureParser()
        >>> sl2 = MP.xmlPrintToSystemLayout(mxPrint)
        >>> sl2.isNew
        True
        >>> sl2.rightMargin
        30.25
        >>> sl2.leftMargin
        20
        >>> sl2.distance
        55
        '''
        if mxPrintIn is None:
            mxPrint = Element('print')
        else:
            mxPrint = mxPrintIn

        setb = _setAttributeFromAttribute
        setb(systemLayout, mxPrint, 'new-system', 'isNew', transform=xmlObjects.booleanToYesNo)

        mxSystemLayout = Element('system-layout')
        self.systemLayoutToXmlSystemLayout(systemLayout, mxSystemLayout)
        if mxSystemLayout:
            mxPrint.append(mxSystemLayout)

        if mxPrintIn is None:
            return mxPrint

    def systemLayoutToXmlSystemLayout(self, systemLayout, mxSystemLayoutIn=None):
        '''
        get given a SystemLayout object configure <system-layout> or <print>

        Called out from xmlPrintToSystemLayout because it
        is also used in the <defaults> tag

        >>> sl = layout.SystemLayout()
        >>> sl.distance = 40.0
        >>> sl.topDistance = 70.0
        >>> XPBase = musicxml.m21ToXml.XMLExporterBase()
        >>> mxSl = XPBase.systemLayoutToXmlSystemLayout(sl)
        >>> XPBase.dump(mxSl)
        <system-layout>
          <system-distance>40.0</system-distance>
          <top-system-distance>70.0</top-system-distance>
        </system-layout>

        >>> sl = layout.SystemLayout()
        >>> sl.leftMargin = 30.0
        >>> mxSl = XPBase.systemLayoutToXmlSystemLayout(sl)
        >>> XPBase.dump(mxSl)
        <system-layout>
          <system-margins>
            <left-margin>30.0</left-margin>
          </system-margins>
        </system-layout>
        '''
        if mxSystemLayoutIn is None:
            mxSystemLayout = Element('system-layout')
        else:
            mxSystemLayout = mxSystemLayoutIn

        seta = _setTagTextFromAttribute

        # TODO -- record even, odd, both margins
        mxSystemMargins = Element('system-margins')
        for direction in ('top', 'bottom', 'left', 'right'):
            seta(systemLayout, mxSystemMargins, direction + '-margin')

        if mxSystemMargins:
            mxSystemLayout.append(mxSystemMargins)

        seta(systemLayout, mxSystemLayout, 'system-distance', 'distance')
        seta(systemLayout, mxSystemLayout, 'top-system-distance', 'topDistance')

        # TODO: system-dividers

        if mxSystemLayoutIn is None:
            return mxSystemLayout

    def staffLayoutToXmlStaffLayout(self, staffLayout, mxStaffLayoutIn=None):
        '''
        get a <staff-layout> tag from a StaffLayout object

        In music21, the <staff-layout> and <staff-details> are
        intertwined in a StaffLayout object.

        >>> sl = layout.StaffLayout()
        >>> sl.distance = 40.0
        >>> sl.staffNumber = 1
        >>> XPBase = musicxml.m21ToXml.XMLExporterBase()
        >>> mxSl = XPBase.staffLayoutToXmlStaffLayout(sl)
        >>> XPBase.dump(mxSl)
        <staff-layout number="1">
          <staff-distance>40.0</staff-distance>
        </staff-layout>

        '''
        if mxStaffLayoutIn is None:
            mxStaffLayout = Element('staff-layout')
        else:
            mxStaffLayout = mxStaffLayoutIn
        seta = _setTagTextFromAttribute
        setb = _setAttributeFromAttribute

        seta(staffLayout, mxStaffLayout, 'staff-distance', 'distance')
        # ET.dump(mxStaffLayout)
        setb(staffLayout, mxStaffLayout, 'number', 'staffNumber')

        if mxStaffLayoutIn is None:
            return mxStaffLayout

    def accidentalToMx(self, a: pitch.Accidental, *, elName: str = 'accidental') -> Element:
        '''
        Convert a pitch.Accidental object to a Element of tag 'accidental' (or other name)

        >>> acc = pitch.Accidental()
        >>> acc.set('half-sharp')
        >>> acc.alter == 0.5
        True

        >>> XB = musicxml.m21ToXml.XMLExporterBase()
        >>> a2m = XB.accidentalToMx
        >>> XB.dump(a2m(acc))
        <accidental>quarter-sharp</accidental>

        >>> acc.set('double-flat')
        >>> XB.dump(a2m(acc))
        <accidental>flat-flat</accidental>


        >>> acc.set('one-and-a-half-sharp')
        >>> XB.dump(a2m(acc, elName='accidental-mark'))
        <accidental-mark>three-quarters-sharp</accidental-mark>

        >>> acc.set('half-flat')
        >>> XB.dump(a2m(acc))
        <accidental>quarter-flat</accidental>

        >>> acc.set('one-and-a-half-flat')
        >>> XB.dump(a2m(acc))
        <accidental>three-quarters-flat</accidental>

        >>> acc.set('sharp')
        >>> acc.displayStyle = 'parentheses'
        >>> XB.dump(a2m(acc))
        <accidental parentheses="yes">sharp</accidental>

        >>> acc.displayStyle = 'bracket'
        >>> XB.dump(a2m(acc))
        <accidental bracket="yes">sharp</accidental>

        >>> acc.displayStyle = 'both'
        >>> XB.dump(a2m(acc))
        <accidental bracket="yes" parentheses="yes">sharp</accidental>

        >>> acc = pitch.Accidental('flat')
        >>> acc.style.relativeX = -2
        >>> XB.dump(a2m(acc))
        <accidental relative-x="-2">flat</accidental>

        >>> acc = pitch.Accidental()
        >>> acc.name = 'double-sharp-down'  # musicxml 3.1
        >>> XB.dump(a2m(acc))
        <accidental>double-sharp-down</accidental>

        >>> acc.name = 'funnyAccidental'  # unknown
        >>> XB.dump(a2m(acc))
        <accidental>other</accidental>
        '''
        # noinspection PyShadowingNames
        otherMusicXMLAccidentals = (
            # v. 3.1
            'double-sharp-down', 'double-sharp-up',
            'flat-flat-down', 'flat-flat-up',
            'arrow-down', 'arrow-up',
            'other',

            # v. 3.0
            'sharp-down', 'sharp-up',
            'natural-down', 'natural-up',
            'flat-down', 'flat-up',
            'slash-quarter-sharp', 'slash-sharp',
            'slash-flat', 'double-slash-flat',
            'sharp-1', 'sharp-2',
            'sharp-3', 'sharp-5',
            'flat-1', 'flat-2',
            'flat-3', 'flat-4',
            'sori', 'koron',
        )

        if a.name == 'half-sharp':
            mxName = 'quarter-sharp'
        elif a.name == 'one-and-a-half-sharp':
            mxName = 'three-quarters-sharp'
        elif a.name == 'half-flat':
            mxName = 'quarter-flat'
        elif a.name == 'one-and-a-half-flat':
            mxName = 'three-quarters-flat'
        elif a.name == 'double-flat':
            mxName = 'flat-flat'
        else:  # all others are the same
            mxName = a.name
            if (mxName not in pitch.accidentalNameToModifier
                    and mxName not in otherMusicXMLAccidentals):
                mxName = 'other'

        mxAccidental = Element(elName)
        # need to remove display in this case and return None
        #         if self.displayStatus == False:
        #             pass
        mxAccidental.text = mxName
        if a.displayStyle in ('parentheses', 'both'):
            mxAccidental.set('parentheses', 'yes')
        if a.displayStyle in ('bracket', 'both'):
            mxAccidental.set('bracket', 'yes')

        self.setPrintStyle(mxAccidental, a)
        return mxAccidental


    def accidentalToMxAccidentalMark(self, a: pitch.Accidental) -> Element:
        return self.accidentalToMx(a, elName='accidental-mark')


# ---------

class ScoreExporter(XMLExporterBase, PartStaffExporterMixin):
    '''
    Convert a Score (or outer stream with .parts) into
    a musicxml Element.
    '''

    def __init__(self, score: stream.Score | None = None, makeNotation: bool = True):
        super().__init__()
        if score is None:
            # should not be done this way.
            self.stream = stream.Score()
        else:
            self.stream = score

        self.xmlRoot = Element('score-partwise', version=defaults.musicxmlVersion)
        self.mxIdentification: Element | None = None

        self.scoreMetadata: metadata.Metadata | None = None

        self.spannerBundle: spanner.SpannerBundle | None = None
        self.meterStream: stream.Stream[meter.TimeSignatureBase] | None = None
        self.scoreLayouts: list[layout.ScoreLayout] = []
        self.firstScoreLayout: layout.ScoreLayout | None = None
        self.textBoxes: list[text.TextBox] = []
        self.highestTime = 0.0

        self.refStreamOrTimeRange = [0.0, self.highestTime]

        self.partExporterList: list[PartExporter] = []

        self.groupsToJoin: list[layout.StaffGroup] = []
        # key = id(stream) (NB: not stream.id); value = .instrumentStream
        self.instrumentsByStream: dict[int, stream.Stream] = {}

        self.instrumentList: list[instrument.Instrument] = []
        self.instrumentIdList: list[str | None] = []
        self.midiChannelList: list[int | None] = []

        self.parts: list[stream.Part] = []

        self.makeNotation: bool = makeNotation

    def parse(self) -> Element:
        '''
        the main function to call.

        If self.stream is empty, call self.emptyObject().  Otherwise,
        convert sounding to written pitch,
        set scorePreliminaries(), call parsePartlikeScore or parseFlatScore, then postPartProcess(),
        clean up circular references for garbage collection, and returns the <score-partwise>
        object.

        >>> b = corpus.parse('bwv66.6')
        >>> SX = musicxml.m21ToXml.ScoreExporter(b)
        >>> mxScore = SX.parse()
        >>> SX.dump(mxScore)
        <score-partwise version="...">...</score-partwise>
        '''
        s = self.stream
        if not s:
            return self.emptyObject()

        # A copy was already made or elected NOT to be made.
        s.toWrittenPitch(inPlace=True, ottavasToSounding=True)

        self.scorePreliminaries()

        if s.hasPartLikeStreams():
            # Pre-populate partExporterList so that joinable groups can be identified
            # before attempting to identify and count instruments
            self._populatePartExporterList()
            self.groupsToJoin = self.joinableGroups()
            self.setPartExporterStaffGroups()
            self.renumberVoicesWithinStaffGroups()
            self.parsePartlikeScore()
        else:
            self.parseFlatScore()

        self.postPartProcess()

        # clean up for circular references.
        self.partExporterList.clear()

        return self.xmlRoot

    def emptyObject(self) -> Element:
        '''
        Creates a cheeky "This Page Intentionally Left Blank" for a blank score

        >>> emptySX = musicxml.m21ToXml.ScoreExporter()
        >>> mxScore = emptySX.parse()  # will call emptyObject
        >>> emptySX.dump(mxScore)
        <score-partwise version="...">
          <work>
            <work-title>This Page Intentionally Left Blank</work-title>
          </work>
          ...
              <note>
                <rest />
                <duration>40320</duration>
                <type>whole</type>
              </note>
            </measure>
          </part>
        </score-partwise>
        '''
        out = stream.Score()
        p = stream.Part()
        m = stream.Measure()
        r = note.Rest(quarterLength=4)
        m.append(r)
        p.append(m)
        out.append(p)
        # return the processing of this Stream
        md = metadata.Metadata(title='This Page Intentionally Left Blank')
        out.insert(0, md)
        # recursive call to this non-empty stream
        self.stream = out
        return self.parse()

    def scorePreliminaries(self) -> None:
        '''
        Populate the exporter object with
        `meterStream`, `scoreLayouts`, `spannerBundle`, and `textBoxes`

        >>> emptySX = musicxml.m21ToXml.ScoreExporter()
        >>> emptySX.scorePreliminaries()  # will call emptyObject
        >>> len(emptySX.textBoxes)
        0
        >>> emptySX.spannerBundle
        <music21.spanner.SpannerBundle of size 0>

        '''
        self.setScoreLayouts()
        self.setMeterStream()
        self.setPartsAndRefStream()
        # get all text boxes
        self.textBoxes = list(self.stream[text.TextBox])

        # we need independent sub-stream elements to shift in presentation
        self.highestTime = 0.0  # redundant, but set here.

        if self.spannerBundle is None:
            self.spannerBundle = self.stream.spannerBundle

    def setPartsAndRefStream(self) -> None:
        '''
        Transfers the offset of the inner stream to elements and sets self.highestTime

        >>> b = corpus.parse('bwv66.6')
        >>> SX = musicxml.m21ToXml.ScoreExporter(b)
        >>> SX.highestTime
        0.0
        >>> SX.setPartsAndRefStream()
        >>> SX.highestTime
        36.0
        >>> SX.refStreamOrTimeRange
        [0.0, 36.0]
        >>> len(SX.parts)
        4
        >>> isinstance(SX.parts[0], stream.Part)
        True

        >>> b.insert(stream.Score())
        >>> SX = musicxml.m21ToXml.ScoreExporter(b)
        >>> SX.setPartsAndRefStream()
        Traceback (most recent call last):
        music21.musicxml.xmlObjects.MusicXMLExportException:
        Exporting scores nested inside scores is not supported
        '''
        s = self.stream
        if t.TYPE_CHECKING:
            assert isinstance(s, stream.Score)

        # environLocal.printDebug('streamToMx(): interpreting multipart')
        streamOfStreams = s.getElementsByClass(stream.Stream)
        for innerStream in streamOfStreams:
            # may need to copy element here
            # apply this stream's offset to elements
            # but retain offsets if inner stream is a Measure
            # https://github.com/cuthbertLab/music21/issues/580
            if isinstance(innerStream, stream.Measure):
                ht = innerStream.offset + innerStream.highestTime
            elif isinstance(innerStream, (stream.Score, stream.Opus)):
                raise MusicXMLExportException(
                    'Exporting scores nested inside scores is not supported')
            else:
                innerStream.transferOffsetToElements()
                ht = innerStream.highestTime
            if ht > self.highestTime:
                self.highestTime = ht
        self.refStreamOrTimeRange = [0.0, self.highestTime]
        self.parts = list(s.parts)

    def setMeterStream(self) -> None:
        '''
        sets `self.meterStream` or uses a default.

        Used in makeNotation in Part later.

        >>> b = corpus.parse('bwv66.6')
        >>> SX = musicxml.m21ToXml.ScoreExporter(b)
        >>> SX.setMeterStream()
        >>> SX.meterStream
        <music21.stream.Score bach/bwv66.6.mxl>
        >>> len(SX.meterStream)
        4
        >>> SX.meterStream[0]
        <music21.meter.TimeSignature 4/4>
        '''
        s = self.stream
        meterStream = s.getTimeSignatures(searchContext=False,
                                          sortByCreationTime=False,
                                          returnDefault=True)
        self.meterStream = meterStream

    def setScoreLayouts(self) -> None:
        '''
        sets `self.scoreLayouts` and `self.firstScoreLayout`

        >>> b = corpus.parse('schoenberg/opus19', 2)
        >>> SX = musicxml.m21ToXml.ScoreExporter(b)
        >>> SX.setScoreLayouts()
        >>> SX.scoreLayouts
        [<music21.layout.ScoreLayout>]
        >>> len(SX.scoreLayouts)
        1
        >>> SX.firstScoreLayout
        <music21.layout.ScoreLayout>
        '''
        s = self.stream
        scoreLayouts = s.getElementsByClass(layout.ScoreLayout)
        self.firstScoreLayout = scoreLayouts.first()
        self.scoreLayouts = list(scoreLayouts)

    def _populatePartExporterList(self) -> None:
        count = 0
        sp = list(self.parts)
        for innerStream in sp:
            count += 1
            # This guards against making an error in a future refactor
            # Raises if editing while iterating instead of casting to list above
            if count > len(sp):  # pragma: no cover
                raise MusicXMLExportException('infinite stream encountered')

            pp = PartExporter(innerStream, parent=self)
            pp.spannerBundle = self.spannerBundle
            self.partExporterList.append(pp)

    def parsePartlikeScore(self) -> None:
        '''
        Called by .parse() if the score has individual parts.
        Creates a `PartExporter` for each part, and runs .parse() on that part.
        Appends the PartExporter to `self.partExporterList`
        and runs .parse() on that part. Appends the PartExporter to self.
        '''
        if not self.partExporterList:
            self._populatePartExporterList()
        for part_ex in self.partExporterList:
            part_ex.parse()

    def parseFlatScore(self) -> None:
        '''
        creates a single PartExporter for this Stream and parses it.

        Note that the Score does not need to be totally flat, it just cannot have Parts inside it;
        measures are fine.

        >>> c = converter.parse('tinyNotation: 3/4 c2. d e')
        >>> SX = musicxml.m21ToXml.ScoreExporter(c)
        >>> SX.parseFlatScore()
        >>> len(SX.partExporterList)
        1
        >>> SX.partExporterList[0]
        <music21.musicxml.m21ToXml.PartExporter object at 0x...>
        >>> SX.dump(SX.partExporterList[0].xmlRoot)
        <part id="...">
          <!--========================= Measure 1 ==========================-->
          <measure implicit="no" number="1">...</measure>
        </part>
        >>> del SX.partExporterList[:]  # for garbage collection
        '''
        s = self.stream
        p = stream.Part()
        for el in s:
            p.coreInsert(el.offset, el)
        p.coreElementsChanged()
        pp = PartExporter(p, parent=self)
        pp.parse()
        self.partExporterList.append(pp)

    def setPartExporterStaffGroups(self) -> None:
        '''
        Figures out the containing StaffGroup for every PartExporter that has one.

        Called automatically by .parse()
        '''
        for partExp in self.partExporterList:
            joinableGroup = None
            for sg in self.groupsToJoin:
                if partExp.stream in sg:
                    joinableGroup = sg
                    break

            partExp.staffGroup = joinableGroup

    def renumberVoicesWithinStaffGroups(self) -> None:
        '''
        Renumbers voices (as appropriate) in each StaffGroup, so that
        voices have unique numbers across the entire group.

        Called automatically by .parse()
        '''
        staffGroupsProcessed: list = []
        for partExp in self.partExporterList:
            if partExp.staffGroup is None:
                # no staffGroup to process
                continue

            if partExp.staffGroup in staffGroupsProcessed:
                # we already processed this one
                continue

            # renumber the voices in this StaffGroup
            staffGroupScore = stream.Score(partExp.staffGroup.getSpannedElements())
            measuresStream: stream.Stream[stream.Measure] = (
                staffGroupScore.recurse().getElementsByClass(stream.Measure).stream()
            )
            offsetIterator: OffsetIterator[stream.Measure] = OffsetIterator(measuresStream)
            measureStack: t.Sequence[stream.Stream[stream.Measure]]
            for measureStack in offsetIterator:
                nextVoiceId: int = 1
                for m in measureStack:
                    for v in m[stream.Voice]:
                        if not isinstance(v.id, int):
                            # it's not an integer, leave it as is, and don't move nextVoiceId
                            continue
                        elif v.id < defaults.minIdNumberToConsiderMemoryLocation:
                            # it's a low integer, leave it as is, and jump nextVoiceId to v.id + 1
                            nextVoiceId = v.id + 1
                        else:
                            # it's a memory location, set v.id to nextVoiceId and increment
                            v.id = nextVoiceId
                            nextVoiceId += 1

            # remember we did this one, so we don't do it again
            staffGroupsProcessed.append(partExp.staffGroup)


    def postPartProcess(self) -> None:
        '''
        calls .joinPartStaffs() from the
        :class:`~music21.musicxml.partStaffExporter.PartStaffExporterMixin`,
        then calls .setScoreHeader(),
        then appends each PartExporter's xmlRoot from
        self.partExporterList to self.xmlRoot.

        Called automatically by .parse().
        '''
        self.joinPartStaffs()
        self.setScoreHeader()
        for i, pex in enumerate(self.partExporterList):
            self.addDividerComment('Part ' + str(i + 1))
            self.xmlRoot.append(pex.xmlRoot)

    def setScoreHeader(self) -> None:
        '''
        Sets the group score-header in <score-partwise>.  Note that score-header is not
        a separate tag, but just a way of grouping things from the tag.

        runs `setTitles()`, `setIdentification()`, `setDefaults()`, changes textBoxes
        to `<credit>` and does the major task of setting up the part-list with `setPartList()`.
        '''
        s = self.stream
        # create score and part list
        # set some score header information from metadata
        self.scoreMetadata = getMetadataFromContext(s)

        self.setTitles()
        self.setIdentification()
        self.setDefaults()
        # add text boxes as Credits
        for tb in self.textBoxes:  # a stream of text boxes
            self.xmlRoot.append(self.textBoxToXmlCredit(tb))

        # the hard one...
        self.setPartList()

    def textBoxToXmlCredit(self, textBox: text.TextBox) -> Element:
        # noinspection PyShadowingNames
        r'''
        Convert a music21 TextBox to a MusicXML Credit.

        >>> tb = text.TextBox('testing')
        >>> tb.style.absoluteY = 400
        >>> tb.style.absoluteX = 300
        >>> tb.page = 3
        >>> SX = musicxml.m21ToXml.ScoreExporter()
        >>> mxCredit = SX.textBoxToXmlCredit(tb)
        >>> SX.dump(mxCredit)
        <credit page="3">
          <credit-words default-x="300" default-y="400"
               halign="center" valign="top">testing</credit-words>
        </credit>

        Default of page 1:

        >>> tb = text.TextBox('testing')
        >>> tb.page
        1
        >>> mxCredit = SX.textBoxToXmlCredit(tb)
        >>> SX.dump(mxCredit)
        <credit page="1">...</credit>

        * Changed in v8: Multi-line text now exports as one `<credit-words>`
          element (preserving newlines).

        >>> tb = text.TextBox('Snare\nCymbals')
        >>> mxCredit = SX.textBoxToXmlCredit(tb)
        >>> SX.dump(mxCredit)
        <credit page="1">
            <credit-words default-x="500" default-y="500" halign="center" valign="top"
            xml:space="preserve">Snare
            Cymbals</credit-words>
        </credit>
        '''
        mxCredit = Element('credit')
        # TODO: credit-type
        # TODO: link
        # TODO: bookmark
        # TODO: credit-image

        if textBox.page is not None:
            mxCredit.set('page', str(textBox.page))
        else:
            mxCredit.set('page', '1')

        mxCreditWords = Element('credit-words')
        if '\n' in textBox.content:
            mxCreditWords.set('xml:space', 'preserve')
        mxCreditWords.text = textBox.content
        # TODO: link/bookmark in credit-words
        self.setPrintStyleAlign(mxCreditWords, textBox)
        if textBox.hasStyleInformation:
            sty = textBox.style
            if t.TYPE_CHECKING:
                assert isinstance(sty, style.TextStyle)
            if sty.justify is not None:
                mxCreditWords.set('justify', sty.justify)
        mxCredit.append(mxCreditWords)
        return mxCredit

    def setDefaults(self):
        # noinspection PyShadowingNames
        '''
        Returns a default object from self.firstScoreLayout or a very simple one if none exists.

        Simple:

        >>> SX = musicxml.m21ToXml.ScoreExporter()
        >>> mxDefaults = SX.setDefaults()
        >>> SX.dump(mxDefaults)
        <defaults>
          <scaling>
            <millimeters>7</millimeters>
            <tenths>40</tenths>
          </scaling>
        </defaults>

        These numbers come from the `defaults` module:

        >>> defaults.scalingMillimeters
        7
        >>> defaults.scalingTenths
        40

        More complex:

        >>> s = corpus.parse('schoenberg/opus19', 2)
        >>> SX = musicxml.m21ToXml.ScoreExporter(s)
        >>> SX.setScoreLayouts()  # necessary to call before .setDefaults()
        >>> mxDefaults = SX.setDefaults()
        >>> mxDefaults.tag
        'defaults'
        >>> mxScaling = mxDefaults.find('scaling')
        >>> SX.dump(mxScaling)
        <scaling>
          <millimeters>6.1472</millimeters>
          <tenths>40</tenths>
        </scaling>

        >>> mxPageLayout = mxDefaults.find('page-layout')
        >>> SX.dump(mxPageLayout)
        <page-layout>
          <page-height>1818</page-height>
          <page-width>1405</page-width>
          <page-margins>
            <left-margin>83</left-margin>
            <right-margin>83</right-margin>
            <top-margin>103</top-margin>
            <bottom-margin>103</bottom-margin>
          </page-margins>
        </page-layout>

        >>> mxSystemLayout = mxDefaults.find('system-layout')
        >>> SX.dump(mxSystemLayout)
        <system-layout>
          <system-margins>
            <left-margin>0</left-margin>
            <right-margin>0</right-margin>
          </system-margins>
          <system-distance>121</system-distance>
          <top-system-distance>70</top-system-distance>
        </system-layout>

        >>> mxStaffLayoutList = mxDefaults.findall('staff-layout')
        >>> len(mxStaffLayoutList)
        1
        >>> SX.dump(mxStaffLayoutList[0])
        <staff-layout>
          <staff-distance>98</staff-distance>
        </staff-layout>
        '''

        # get score defaults if any:
        if self.firstScoreLayout is None:
            scoreLayout = layout.ScoreLayout()
            scoreLayout.scalingMillimeters = defaults.scalingMillimeters
            scoreLayout.scalingTenths = defaults.scalingTenths
        else:
            scoreLayout = self.firstScoreLayout

        mxDefaults = SubElement(self.xmlRoot, 'defaults')
        if scoreLayout.scalingMillimeters is not None or scoreLayout.scalingTenths is not None:
            mxScaling = SubElement(mxDefaults, 'scaling')
            mxMillimeters = SubElement(mxScaling, 'millimeters')
            mxMillimeters.text = str(scoreLayout.scalingMillimeters)
            mxTenths = SubElement(mxScaling, 'tenths')
            mxTenths.text = str(scoreLayout.scalingTenths)

        if scoreLayout.pageLayout is not None:
            mxPageLayout = self.pageLayoutToXmlPageLayout(scoreLayout.pageLayout)
            mxDefaults.append(mxPageLayout)

        if scoreLayout.systemLayout is not None:
            mxSystemLayout = self.systemLayoutToXmlSystemLayout(scoreLayout.systemLayout)
            mxDefaults.append(mxSystemLayout)

        for staffLayout in scoreLayout.staffLayoutList:
            mxStaffLayout = self.staffLayoutToXmlStaffLayout(staffLayout)
            mxDefaults.append(mxStaffLayout)

        self.addStyleToXmlDefaults(mxDefaults)
        return mxDefaults  # mostly for testing...

    def addStyleToXmlDefaults(self, mxDefaults):
        # noinspection PyShadowingNames
        '''
        Optionally add an <appearance> tag (using `styleToXmlAppearance`)
        and <music-font>, <word-font>, zero or more <lyric-font> tags,
        and zero or more <lyric-language> tags to mxDefaults

        Demonstrating round tripping:

        >>> import xml.etree.ElementTree as ET
        >>> defaults = ET.fromstring('<defaults>'
        ...          + '<music-font font-family="Maestro, Opus" font-weight="bold" />'
        ...          + '<word-font font-family="Garamond" font-style="italic" />'
        ...          + '<lyric-font name="verse" font-size="12" />'
        ...          + '<lyric-font name="chorus" font-size="14" />'
        ...          + '<lyric-language name="verse" xml:lang="fr" />'
        ...          + '<lyric-language name="chorus" xml:lang="en" />'
        ...          + '</defaults>')

        >>> MI = musicxml.xmlToM21.MusicXMLImporter()
        >>> MI.styleFromXmlDefaults(defaults)
        >>> SX = musicxml.m21ToXml.ScoreExporter(MI.stream)
        >>> mxDefaults = ET.Element('defaults')
        >>> SX.addStyleToXmlDefaults(mxDefaults)
        >>> SX.dump(mxDefaults)
        <defaults>
            <music-font font-family="Maestro,Opus" font-weight="bold" />
            <word-font font-family="Garamond" font-style="italic" />
            <lyric-font font-size="12" name="verse" />
            <lyric-font font-size="14" name="chorus" />
            <lyric-language name="verse" xml:lang="fr" />
            <lyric-language name="chorus" xml:lang="en" />
        </defaults>
        '''
        if not self.stream.hasStyleInformation:
            return

        mxAppearance = self.styleToXmlAppearance()
        if mxAppearance is not None:
            mxDefaults.append(mxAppearance)

        st = self.stream.style
        if st.musicFont is not None:
            mxMusicFont = SubElement(mxDefaults, 'music-font')
            self.setFont(mxMusicFont, st.musicFont)

        if st.wordFont is not None:
            mxWordFont = SubElement(mxDefaults, 'word-font')
            self.setFont(mxWordFont, st.wordFont)

        for lyricName, lyricFont in st.lyricFonts:
            mxLyricFont = SubElement(mxDefaults, 'lyric-font')
            if lyricFont is not None:
                self.setFont(mxLyricFont, lyricFont)
            if lyricName is not None:
                mxLyricFont.set('name', lyricName)

        for lyricType, lyricLang in st.lyricLanguages:
            mxLyricLanguage = SubElement(mxDefaults, 'lyric-language')
            if lyricType is not None:
                mxLyricLanguage.set('name', lyricType)
            if lyricLang is not None:
                mxLyricLanguage.set('xml:lang', lyricLang)

    def styleToXmlAppearance(self):
        # noinspection PyShadowingNames
        '''
        Populates the <appearance> tag of the <defaults> with
        information from the stream's .style information.

        >>> s = stream.Score()
        >>> s.style.lineWidths.append(('beam', 5.0))
        >>> s.style.noteSizes.append(('cue', 75))
        >>> s.style.distances.append(('hyphen', 0.1))
        >>> s.style.otherAppearances.append(('flags', 'wavy'))
        >>> SX = musicxml.m21ToXml.ScoreExporter(s)
        >>> mxAppearance = SX.styleToXmlAppearance()
        >>> SX.dump(mxAppearance)
        <appearance>
          <line-width type="beam">5.0</line-width>
          <note-size type="cue">75</note-size>
          <distance type="hyphen">0.1</distance>
          <other-appearance type="flags">wavy</other-appearance>
        </appearance>
        '''
        st = self.stream.style

        if (not st.lineWidths
                and not st.noteSizes
                and not st.distances
                and not st.otherAppearances):
            return None  # appearance tag cannot be empty

        mxAppearance = Element('appearance')
        for thisProperty, tag in [('lineWidths', 'line-width'),
                                  ('noteSizes', 'note-size'),
                                  ('distances', 'distance'),
                                  ('otherAppearances', 'other-appearance')]:
            propertyList = getattr(st, thisProperty)
            for propertyType, propertyValue in propertyList:
                mxProperty = SubElement(mxAppearance, tag)
                mxProperty.set('type', propertyType)
                mxProperty.text = str(propertyValue)

        return mxAppearance

    def setPartList(self):
        # noinspection PyShadowingNames
        '''
        Returns a <part-list> and appends it to self.xmlRoot.

        This is harder than it looks because MusicXML and music21's idea of where to store
        staff-groups are quite different.

        We find each stream in self.partExporterList, then look at the StaffGroup spanners in
        self.spannerBundle.  If the part is the first element in a StaffGroup then we add a
        <staff-group> object with 'start' as the starting point (and same for multiple StaffGroups)
        this is in `staffGroupToXmlPartGroup(sg)`.
        then we add the <score-part> descriptor of the part and its instruments, etc. (currently
        just one!), then we iterate again through all StaffGroups and if this part is the last
        element in a StaffGroup we add a <staff-group> descriptor with type="stop".

        This Bach example has four parts and one staff-group bracket linking them:

        >>> b = corpus.parse('bwv66.6')
        >>> SX = musicxml.m21ToXml.ScoreExporter(b)

        Needs some strange setup to make this work in a demo.  `.parse()` takes care of all this.

        >>> SX.scorePreliminaries()
        >>> SX.parsePartlikeScore()

        >>> mxPartList = SX.setPartList()
        >>> SX.dump(mxPartList)
        <part-list>
          <part-group number="1" type="start">...
          <score-part id="P1">...
          <score-part id="P2">...
          <score-part id="P3">...
          <score-part id="P4">...
          <part-group number="1" type="stop" />
        </part-list>

        Multi-staff parts (such as piano staves), should NOT receive `<part-group>` tags,
        since they are joined by `<staff>` tags:

        >>> cpe = corpus.parse('cpebach')
        >>> SX = musicxml.m21ToXml.ScoreExporter(cpe)
        >>> SX.scorePreliminaries()
        >>> SX.parsePartlikeScore()
        >>> SX.joinPartStaffs()

        >>> mxPartList = SX.setPartList()
        >>> SX.dump(mxPartList)
        <part-list>
          <score-part id="P1">...
          </score-part>
        </part-list>
        '''

        spannerBundle = self.spannerBundle

        mxPartList = SubElement(self.xmlRoot, 'part-list')
        # mxComponents is just a list
        # returns a spanner bundle
        staffGroups = spannerBundle.getByClass(layout.StaffGroup)
        # environLocal.printDebug(['got staff groups', staffGroups])

        # first, find which parts are start/end of partGroups
        partGroupIndexRef = {}  # have id be key
        partGroupIndex = 1  # start by 1 by convention
        for pex in self.partExporterList:
            p = pex.stream
            # check for first
            for sg in staffGroups:
                if sg in self.groupsToJoin:
                    continue
                if sg.isFirst(p):
                    mxPartGroup = self.staffGroupToXmlPartGroup(sg)
                    mxPartGroup.set('number', str(partGroupIndex))
                    # assign the spanner in the dictionary
                    partGroupIndexRef[partGroupIndex] = sg
                    partGroupIndex += 1  # increment for next usage
                    mxPartList.append(mxPartGroup)
            # add score part
            mxScorePart = pex.getXmlScorePart()
            mxPartList.append(mxScorePart)
            # check for last
            activeIndex = None
            for sg in staffGroups:
                if sg in self.groupsToJoin:
                    continue
                # Handle last part in the StaffGroup
                if sg.isLast(p):
                    # find the spanner in the dictionary already-assigned
                    for k, value in partGroupIndexRef.items():
                        if value is sg:
                            activeIndex = k
                            break
                    mxPartGroup = Element('part-group')
                    mxPartGroup.set('type', 'stop')
                    if activeIndex is not None:
                        mxPartGroup.set('number', str(activeIndex))
                    mxPartList.append(mxPartGroup)

        return mxPartList

    def staffGroupToXmlPartGroup(self, staffGroup):
        # noinspection PyShadowingNames
        '''
        Create and configure an mxPartGroup object for the 'start' tag
        from a staff group spanner. Note that this object
        is not completely formed by this procedure. (number isn't done...)

        >>> b = corpus.parse('bwv66.6')
        >>> SX = musicxml.m21ToXml.ScoreExporter(b)
        >>> firstStaffGroup = b.spannerBundle.getByClass(layout.StaffGroup)[0]
        >>> mxPartGroup = SX.staffGroupToXmlPartGroup(firstStaffGroup)
        >>> SX.dump(mxPartGroup)
        <part-group type="start">
          <group-symbol>bracket</group-symbol>
          <group-barline>yes</group-barline>
        </part-group>

        At this point, you should set the number of the mxPartGroup, since it is required:

        >>> mxPartGroup.set('number', str(1))


        What can we do with it?

        >>> firstStaffGroup.name = 'Voices'
        >>> firstStaffGroup.abbreviation = 'Ch.'
        >>> firstStaffGroup.symbol = 'brace' # 'none', 'brace', 'line', 'bracket', 'square'
        >>> firstStaffGroup.barTogether = False  # True, False, or 'Mensurstrich'
        >>> mxPartGroup = SX.staffGroupToXmlPartGroup(firstStaffGroup)
        >>> SX.dump(mxPartGroup)
        <part-group type="start">
          <group-name>Voices</group-name>
          <group-abbreviation>Ch.</group-abbreviation>
          <group-symbol>brace</group-symbol>
          <group-barline>no</group-barline>
        </part-group>

        Now we avoid printing the name of the group:

        >>> firstStaffGroup.style.hideObjectOnPrint = True
        >>> mxPartGroup = SX.staffGroupToXmlPartGroup(firstStaffGroup)
        >>> SX.dump(mxPartGroup)
        <part-group type="start">
          <group-name>Voices</group-name>
          <group-name-display print-object="no" />
          <group-abbreviation>Ch.</group-abbreviation>
          <group-symbol>brace</group-symbol>
          <group-barline>no</group-barline>
        </part-group>
        '''
        mxPartGroup = Element('part-group')
        mxPartGroup.set('type', 'start')
        seta = _setTagTextFromAttribute
        seta(staffGroup, mxPartGroup, 'group-name', 'name')
        if staffGroup.style.hideObjectOnPrint:
            mxGroupNameDisplay = SubElement(mxPartGroup, 'group-name-display')
            mxGroupNameDisplay.set('print-object', 'no')
        seta(staffGroup, mxPartGroup, 'group-abbreviation', 'abbreviation')
        mxGroupSymbol = seta(staffGroup, mxPartGroup, 'group-symbol', 'symbol')
        if mxGroupSymbol is not None:
            self.setColor(mxGroupSymbol, staffGroup)
            self.setPosition(mxGroupSymbol, staffGroup)

        mxGroupBarline = SubElement(mxPartGroup, 'group-barline')
        if staffGroup.barTogether is True:
            mxGroupBarline.text = 'yes'
        elif staffGroup.barTogether is False:
            mxGroupBarline.text = 'no'
        elif staffGroup.barTogether == 'Mensurstrich':
            mxGroupBarline.text = 'Mensurstrich'
        # TODO: group-time
        self.setEditorial(mxPartGroup, staffGroup)

        # environLocal.printDebug(['configureMxPartGroupFromStaffGroup: mxPartGroup', mxPartGroup])
        return mxPartGroup

    def setIdentification(self) -> Element:
        # noinspection SpellCheckingInspection, PyShadowingNames
        '''
        Returns an identification object from self.scoreMetadata.  And appends to the score...

        For defaults:

        >>> SX = musicxml.m21ToXml.ScoreExporter()
        >>> mxIdentification = SX.setIdentification()
        >>> SX.dump(mxIdentification)
        <identification>
          <creator type="composer">Music21</creator>
          <encoding>
            <encoding-date>20...-...-...</encoding-date>
            <software>music21 v...</software>
          </encoding>
        </identification>

        More realistic:

        >>> md = metadata.Metadata()
        >>> md.composer = 'Francesca Caccini'
        >>> c = metadata.Contributor(role='arranger', name='Aliyah Shanti')
        >>> md.addContributor(c)

        need a fresh ScoreExporter ...otherwise appends to existing mxIdentification


        >>> SX = musicxml.m21ToXml.ScoreExporter()
        >>> SX.scoreMetadata = md
        >>> mxIdentification = SX.setIdentification()
        >>> SX.dump(mxIdentification)
        <identification>
          <creator type="composer">Francesca Caccini</creator>
          <creator type="arranger">Aliyah Shanti</creator>
          <encoding>
            <encoding-date>...</encoding-date>
            <software>music21 v...</software>
          </encoding>
        </identification>


        Overriding the default:

        >>> defaults.author = "Batch Conversion March 2022"
        >>> SX = musicxml.m21ToXml.ScoreExporter()
        >>> mxIdentification = SX.setIdentification()
        >>> SX.dump(mxIdentification)
        <identification>
          <creator type="composer">Batch Conversion March 2022</creator>
          <encoding>
            <encoding-date>20...-...-...</encoding-date>
            <software>music21 v...</software>
          </encoding>
        </identification>

        '''
        if self.mxIdentification is not None:
            mxId = self.mxIdentification
        else:
            mxId = SubElement(self.xmlRoot, 'identification')
            self.mxIdentification = mxId

        # creators
        foundOne = False
        if self.scoreMetadata is not None:
            # We ignore the name ('namespace:name') here, and use
            # c.role instead so we can represent non-standard roles.
            # If c.role is non-standard, the name will be very boring:
            # 'marcrel:CTB', which means 'otherContributor'.
            for _, c in self.scoreMetadata.all(
                    skipNonContributors=True,  # we only want contributors
                    returnPrimitives=True,     # we want Contributor values
                    returnSorted=False):
                mxCreator = self.contributorToXmlCreator(c)
                mxId.append(mxCreator)
                foundOne = True

        if foundOne is False and defaults.author:
            mxCreator = SubElement(mxId, 'creator')
            mxCreator.set('type', 'composer')
            mxCreator.text = defaults.author

        if self.scoreMetadata is not None:
            copyrights: tuple[metadata.Copyright, ...] = self.scoreMetadata['copyright']
            for c in copyrights:
                mxRights = SubElement(mxId, 'rights')
                if c.role is not None:
                    mxRights.set('type', c.role)
                mxRights.text = str(c)

        # Encoding does its own append...
        self.setEncoding()
        # TODO: source
        # TODO: relation
        self.metadataToMiscellaneous()

        return mxId

    def metadataToMiscellaneous(
        self,
        md: metadata.Metadata | None = None
    ) -> Element | None:
        # noinspection PyShadowingNames
        '''
        Returns an mxMiscellaneous of information from metadata object md or
        from self.scoreMetadata if md is None.  If the mxMiscellaneous object
        has any miscellaneous-fields, then it is appended to self.mxIdentification
        if it exists.

        >>> SX = musicxml.m21ToXml.ScoreExporter()
        >>> md = metadata.Metadata()
        >>> md.date = metadata.primitives.DateRelative('1689', 'onOrBefore')
        >>> md.localeOfComposition = 'Rome'

        >>> mxMisc = SX.metadataToMiscellaneous(md)
        >>> SX.dump(mxMisc)
        <miscellaneous>
          <miscellaneous-field name="dcterms:created">1689/--/-- or earlier</miscellaneous-field>
          <miscellaneous-field name="humdrum:OPC">Rome</miscellaneous-field>
        </miscellaneous>
        '''
        if md is None and self.scoreMetadata is None:
            return None
        elif md is None:
            md = self.scoreMetadata

        if t.TYPE_CHECKING:
            assert md is not None

        mxMiscellaneous = Element('miscellaneous')

        foundOne = False
        allItems: tuple[tuple[str, t.Any], ...]
        allItems = md.all(
            skipContributors=True,  # we don't want the contributors (already handled them)
            returnPrimitives=True,  # we want ValueType values
            returnSorted=False
        )

        skippedOneMovementName: bool = False
        skippedOneMovementNumber: bool = False
        skippedOneTitle: bool = False
        for uniqueName, value in allItems:
            if uniqueName == 'software':
                # we have already emitted the software versions in <software>.
                continue

            if uniqueName == 'movementName':
                # We have already emitted the first movementName in <movement-title>,
                # but we need to emit the rest of them here in miscellaneous.
                if not skippedOneMovementName:
                    skippedOneMovementName = True
                    continue

            if uniqueName == 'movementNumber':
                # We have already emitted the first movementNumber in <movement-number>,
                # but we need to emit the rest of them here in miscellaneous.
                if not skippedOneMovementNumber:
                    skippedOneMovementNumber = True
                    continue

            if uniqueName == 'title':
                # We have already emitted the first title in <work-title>,
                # but we need to emit the rest of them here in miscellaneous.
                if not skippedOneTitle:
                    skippedOneTitle = True
                    continue

            if uniqueName == 'copyright':
                # We have already emitted all the copyrights.
                continue

            namespaceName: str | None = md.uniqueNameToNamespaceName(uniqueName)
            if namespaceName is None:
                namespaceName = uniqueName

            if namespaceName.startswith('m21FileInfo:'):
                # We don't emit fileInfo (fileFormat, filePath, fileNumber)
                # into MusicXML files.  It is added during parsing, and
                # isn't accurate for the file we are writing here.
                continue

            mxMiscField = SubElement(mxMiscellaneous, 'miscellaneous-field')
            mxMiscField.set('name', namespaceName)
            mxMiscField.text = str(value)
            foundOne = True

        if self.mxIdentification is not None and foundOne:
            self.mxIdentification.append(mxMiscellaneous)

        # for testing:
        return mxMiscellaneous

    def setEncoding(self):
        # noinspection PyShadowingNames
        '''
        Returns an encoding object that might have information about <supports> also.
        and appends to mxIdentification (if any)

        Will use the date of generation as encoding-date.

        >>> SX = musicxml.m21ToXml.ScoreExporter()
        >>> mxEncoding = SX.setEncoding()
        >>> SX.dump(mxEncoding)
        <encoding>
          <encoding-date>20...-...-...</encoding-date>
          <software>music21 v...</software>
        </encoding>

        Encoding-date is in YYYY-MM-DD format.
        '''
        if self.mxIdentification is not None:
            mxEncoding = SubElement(self.mxIdentification, 'encoding')
        else:
            mxEncoding = Element('encoding')

        mxEncodingDate = SubElement(mxEncoding, 'encoding-date')
        mxEncodingDate.text = str(datetime.date.today())  # right format...
        # TODO: encoder

        if self.scoreMetadata is not None:
            found_m21_already = False
            for software in self.scoreMetadata.software:
                if 'music21 v.' in software:
                    if found_m21_already:
                        # only write out one copy of the music21 software
                        # tag.  First one should be current version.
                        continue
                    else:
                        found_m21_already = True
                mxSoftware = SubElement(mxEncoding, 'software')
                mxSoftware.text = software
        else:
            # there will not be a music21 software tag if there was no scoreMetadata
            # if not for these lines.
            mxSoftware = SubElement(mxEncoding, 'software')
            mxSoftware.text = defaults.software

        # TODO: encoding-description
        mxSupportsList = self.getSupports()
        for mxSupports in mxSupportsList:
            mxEncoding.append(mxSupports)

        return mxEncoding  # for testing...

    def getSupports(self):
        '''
        return a list of <supports> tags  for what this supports.  Does not append

        Currently just supports new-system and new-page if s.definesExplicitSystemBreaks
        and s.definesExplicitPageBreaks is True.

        >>> SX = musicxml.m21ToXml.ScoreExporter()
        >>> SX.getSupports()
        []
        >>> SX.stream.definesExplicitSystemBreaks = True
        >>> SX.getSupports()
        [<Element 'supports' at 0x...>]
        >>> SX.dump(SX.getSupports()[0])
        <supports attribute="new-system" element="print" type="yes" value="yes" />

        >>> SX.stream.definesExplicitPageBreaks = True
        >>> SX.dump(SX.getSupports()[1])
        <supports attribute="new-page" element="print" type="yes" value="yes" />

        '''
        def getSupport(attribute, supports_type, value, element):
            su = Element('supports')
            su.set('attribute', attribute)
            su.set('type', supports_type)
            su.set('value', value)
            su.set('element', element)
            return su

        supportsList = []
        s = self.stream
        if s.definesExplicitSystemBreaks is True:
            supportsList.append(getSupport('new-system', 'yes', 'yes', 'print'))

        if s.definesExplicitPageBreaks is True:
            supportsList.append(getSupport('new-page', 'yes', 'yes', 'print'))

        return supportsList

    def setTitles(self) -> None:
        '''
        puts work (with work-title), movement-number, movement-title into the self.xmlRoot
        '''
        mdObj = self.scoreMetadata
        if self.scoreMetadata is None:
            mdObj = metadata.Metadata()
        if t.TYPE_CHECKING:
            assert mdObj is not None

        mxScoreHeader = self.xmlRoot
        mxWork = Element('work')
        # TODO: work-number
        firstTitleFound: metadata.Text | None = None
        titles: tuple[metadata.Text, ...] = mdObj['title']
        if titles:
            if firstTitleFound is None:
                firstTitleFound = titles[0]
            mxWorkTitle = SubElement(mxWork, 'work-title')
            mxWorkTitle.text = str(titles[0])
        if mxWork:
            mxScoreHeader.append(mxWork)

        movementNumbers: tuple[metadata.Text, ...] = mdObj['movementNumber']
        if movementNumbers:
            mxMovementNumber = SubElement(mxScoreHeader, 'movement-number')
            mxMovementNumber.text = str(movementNumbers[0])

        # musicxml often defaults to show only movement title
        # if no movementName is found in mdObj, set movement title to
        # first title of the mdObj instead. Fall back to defaults.title if
        # necessary (and if possible).

        movement_title: str = ''

        movementNames: tuple[metadata.Text, ...] = mdObj['movementName']
        if movementNames:
            movement_title = str(movementNames[0])
        else:  # there are no movementNames
            if firstTitleFound is not None:
                movement_title = str(firstTitleFound)
            elif defaults.title:
                movement_title = defaults.title
            else:
                return
        mxMovementTitle = SubElement(mxScoreHeader, 'movement-title')
        mxMovementTitle.text = movement_title

    def contributorToXmlCreator(self, c):
        # noinspection SpellCheckingInspection, PyShadowingNames
        '''
        Return a <creator> tag from a :class:`~music21.metadata.Contributor` object.

        >>> md = metadata.Metadata()
        >>> md.composer = 'Oliveros, Pauline'
        >>> contrib = md.contributors[0]
        >>> contrib
        <music21.metadata.primitives.Contributor composer:Oliveros, Pauline>

        >>> SX = musicxml.m21ToXml.ScoreExporter()
        >>> mxCreator = SX.contributorToXmlCreator(contrib)
        >>> SX.dump(mxCreator)
        <creator type="composer">Oliveros, Pauline</creator>
        '''
        mxCreator = Element('creator')
        if c.role is not None:
            mxCreator.set('type', str(c.role))
        if c.name is not None:
            mxCreator.text = c.name
        return mxCreator

# ------------------------------------------------------------------------------


class PartExporter(XMLExporterBase):
    '''
    Object to convert one Part stream to a <part> tag on .parse()
    '''
    _DOC_ATTR: dict[str, str] = {
        'previousPartStaffInGroup': '''
            If the part being exported is a :class:`~music21.stream.base.PartStaff`,
            this attribute will be used to store the immediately previous `PartStaff`
            in the :class:`~music21.layout.StaffGroup`, if any. (E.g. if this is
            the left hand, store a reference to the right hand.)''',
    }

    def __init__(self,
                 partObj: stream.Part | stream.Score | None = None,
                 parent: ScoreExporter | None = None):
        super().__init__()
        # partObj can be a Score IF it has no parts within it.  But better to
        # always have it be a Part

        if partObj is None:
            partObj = stream.Part()
        self.stream: stream.Part | stream.Score = partObj
        self.parent = parent  # ScoreExporter
        self.xmlRoot = Element('part')

        if parent is None:
            self.meterStream: stream.Stream[meter.TimeSignatureBase] = stream.Stream()
            self.refStreamOrTimeRange = [0.0, 0.0]
            self.midiChannelList = []
            self.makeNotation = True
        else:
            self.meterStream = (parent.meterStream
                                if parent.meterStream is not None
                                else stream.Stream())  # else should not be executed.
            self.refStreamOrTimeRange = parent.refStreamOrTimeRange
            self.midiChannelList = parent.midiChannelList  # shared list
            self.makeNotation = parent.makeNotation

        self.previousPartStaffInGroup: stream.PartStaff | None = None

        self.instrumentStream: stream.Stream[instrument.Instrument] | None = None
        self.firstInstrumentObject = None

        # keep track of this so that we only put out new attributes when something
        # has changed
        self.lastDivisions = None

        # The staffGroup to which this part belongs (if it belongs to one)
        self.staffGroup: layout.StaffGroup | None = None
        self.spannerBundle = partObj.spannerBundle

    def parse(self):
        '''
        Set up instruments, convert sounding pitch to written pitch,
        create a partId (if no good one exists) and set it on
        <part>, fixes up the notation
        (:meth:`fixupNotationFlat` or :meth:`fixupNotationMeasured`),
        setIdLocals() on spanner bundle. Run parse() on each measure's MeasureExporter and
        append the output to the <part> object.

        In other words, one-stop shopping.

        :attr:`makeNotation` when False, will avoid running
        :meth:`~music21.stream.base.Stream.makeNotation`
        on the Part. Generally this attribute is set on `GeneralObjectExporter`
        or `ScoreExporter` and read from there. Running with `makeNotation`
        as False will raise `MusicXMLExportException` if no measures are present.
        If `makeNotation` is False, the transposition to written pitch is still
        performed and thus will be done in place.

        >>> from music21.musicxml.m21ToXml import PartExporter
        >>> noMeasures = stream.Part(note.Note())
        >>> pex = PartExporter(noMeasures)
        >>> pex.makeNotation = False
        >>> pex.parse()
        Traceback (most recent call last):
        music21.musicxml.xmlObjects.MusicXMLExportException:
        Cannot export with makeNotation=False if there are no measures
        '''
        # A copy has already been made
        # unless makeNotation=False, but the user
        # should have called toWrittenPitch() first
        # and is explicitly asking for no further copies to be made
        self.stream.toWrittenPitch(inPlace=True, ottavasToSounding=True)

        # Suppose that everything below this is a measure
        if self.makeNotation:
            self.stream = self.stream.splitAtDurations(recurse=True)[0]

            if self.stream.getElementsByClass(stream.Measure):
                self.fixupNotationMeasured()
            else:
                self.fixupNotationFlat()
        elif not self.stream.getElementsByClass(stream.Measure):
            raise MusicXMLExportException(
                'Cannot export with makeNotation=False if there are no measures')

        # make sure that all instances of the same class have unique ids
        self.spannerBundle.setIdLocals()

        # must do after fixupNotation, since instrument instances may be created anew!
        self.instrumentSetup()

        self.xmlRoot.set('id', str(self.firstInstrumentObject.partId))

        for m in self.stream.getElementsByClass(stream.Measure):
            self.addDividerComment('Measure ' + str(m.number))
            measureExporter = MeasureExporter(m, parent=self)
            measureExporter.spannerBundle = self.spannerBundle
            try:
                mxMeasure = measureExporter.parse()
            except MusicXMLExportException as e:
                e.measureNumber = str(m.number)
                if isinstance(self.stream, stream.Part):
                    e.partName = self.stream.partName
                # else: could be a Score without parts (flat)
                raise e
            self.xmlRoot.append(mxMeasure)

        return self.xmlRoot

    def instrumentSetup(self):
        '''
        Sets self.instrumentStream and self.firstInstrumentObject for the stream,
        checks for a unique midiChannel and then blocks it off from future use.

        >>> p = converter.parse('tinyNotation: 4/4 c1 d1 e1')
        >>> p.getElementsByClass(stream.Measure)[0].insert(0, instrument.Clarinet())
        >>> p.getElementsByClass(stream.Measure)[1].insert(0, instrument.BassClarinet())
        >>> PEX = musicxml.m21ToXml.PartExporter(p)
        >>> PEX.instrumentStream is None
        True
        >>> PEX.firstInstrumentObject is None
        True
        >>> PEX.instrumentSetup()
        >>> PEX.instrumentStream
        <music21.stream.Part 0x10ae02780>

        The "P" signifies that it is the main instrument associated with a Part.

        >>> PEX.instrumentStream.show('text')
        {0.0} <music21.instrument.Clarinet 'P...: Clarinet'>
        {4.0} <music21.instrument.BassClarinet 'Bass clarinet'>
        '''
        # Collect instruments
        if self.parent is not None and id(self.stream) in self.parent.instrumentsByStream:
            # this condition will be satisfied if this is the second or subsequent
            # PartStaff in a StaffGroup
            self.instrumentStream = self.parent.instrumentsByStream[id(self.stream)]
        else:
            # get a default instrument if not assigned
            self.instrumentStream = self.stream.getInstruments(returnDefault=True, recurse=True)
        self.firstInstrumentObject = self.instrumentStream[0]  # store first, as handled differently

        if self.parent is not None:
            instIdList = [x.partId for x in self.parent.instrumentList]
        else:
            instIdList = [self.stream.id]

        firstInstId = self.firstInstrumentObject.partId
        if firstInstId in instIdList or firstInstId is None:  # must have unique ids
            self.firstInstrumentObject.partIdRandomize()  # set new random id

        should_short_circuit = self.mergeInstrumentStreamPartStaffAware()
        if should_short_circuit:
            return

        seen_instrument_classes = set()
        for thisInstrument in self.instrumentStream:
            # fragile against two or more instruments with the same
            # Instrument subclass but different MIDI numbers or channels.
            if type(thisInstrument) in seen_instrument_classes:
                continue

            seen_instrument_classes.add(type(thisInstrument))
            if (thisInstrument.midiChannel is None
                    or thisInstrument.midiChannel in self.midiChannelList):
                try:
                    thisInstrument.autoAssignMidiChannel(usedChannels=self.midiChannelList)
                except exceptions21.InstrumentException as e:
                    environLocal.warn(str(e))

            # this is shared among all PartExporters, so long as they are created by a
            # ScoreExporter
            self.midiChannelList.append(thisInstrument.midiChannel)
            # environLocal.printDebug(['midiChannel list', self.midiChannelList])

            # Enforce uniqueness
            if (thisInstrument.instrumentId is None
                or (self.parent
                    and thisInstrument.instrumentId in self.parent.instrumentIdList)):
                thisInstrument.instrumentIdRandomize()

            # add to the lists for checking on next part
            if self.parent is not None:
                self.parent.instrumentIdList.append(thisInstrument.instrumentId)
                if thisInstrument is self.firstInstrumentObject:
                    self.parent.instrumentList.append(thisInstrument)

    def mergeInstrumentStreamPartStaffAware(self) -> bool:
        '''
        Merges instrument streams from subsequent parts in a PartStaff group.

        Does nothing in the normal case of single staves.

        Returns whether instrument processing should short circuit,
        which is False for the general case and True for subsequent
        PartStaff objects after the first in a group.
        '''
        if self.parent is None:
            return False

        # This is a list of StaffGroups, not PartStaffs, so check if any
        if not self.parent.groupsToJoin:
            return False

        for joined_group in self.parent.groupsToJoin:
            if joined_group.isFirst(self.stream):
                # need to insert instruments from subsequent staffs
                for subsequent_staff in joined_group[1:]:
                    other_instruments = subsequent_staff.getInstruments(
                        returnDefault=True, recurse=True)
                    self.instrumentStream += other_instruments
                    if self.instrumentStream is not None:
                        instrument.deduplicate(self.instrumentStream, inPlace=True)
                    # Place a reference to this instrument stream in a place
                    # where subsequent staffs entering this method will find and use it
                    if self.parent and self.instrumentStream is not None:
                        next_id = id(subsequent_staff)
                        self.parent.instrumentsByStream[next_id] = self.instrumentStream
            elif self.stream in joined_group:
                # This stream was already (or will be) processed
                # UNLESS there is a spaghetti case where
                # this stream is second in groupB, but first in groupA,
                # but PartStaffExporterMixin guarantees that won't happen
                return True
        return False

    def fixupNotationFlat(self):
        '''
        Runs makeNotation on a flatStream, such as one lacking measures.
        '''
        part = self.stream
        part.makeMutable()  # must mutate
        # try to add measures if none defined
        # returns a new stream w/ new Measures but the same objects
        part.makeNotation(meterStream=self.meterStream,
                          refStreamOrTimeRange=self.refStreamOrTimeRange,
                          inPlace=True)
        # environLocal.printDebug(['fixupNotationFlat: post makeNotation, length',
        #                    len(measureStream)])

        # after calling measuresStream, need to update Spanners, as a deepcopy
        # has been made
        # might need to getAll b/c might need spanners
        # from a higher level container
        # allContexts = []
        # spannerContext = measureStream.flatten().getContextByClass('Spanner')
        # while spannerContext:
        #    allContexts.append(spannerContext)
        #    spannerContext = spannerContext.getContextByClass('Spanner')
        #
        # spannerBundle = spanner.SpannerBundle(allContexts)
        # only getting spanners at this level
        # spannerBundle = spanner.SpannerBundle(measureStream.flatten())
        self.spannerBundle = part.spannerBundle

    def fixupNotationMeasured(self):
        '''
        Checks to see if there are any attributes in the part stream and moves
        them into the first measure if necessary.

        Checks if makeAccidentals is run, and haveBeamsBeenMade is done, and
        tuplets have been made.

        * Changed in v7: no longer accepts `measureStream` argument.
        '''
        part = self.stream
        measures = part.getElementsByClass(stream.Measure)
        first_measure = measures.first()
        if not first_measure:
            return
        # check that first measure has any attributes in outer Stream
        # this is for non-standard Stream formations (some kern imports)
        # that place key/clef information in the containing stream
        if hasattr(first_measure, 'clef') and first_measure.clef is None:
            first_measure.makeMutable()  # must mutate
            outerClefs = part.getElementsByClass(clef.Clef)
            if outerClefs:
                first_measure.clef = outerClefs.first()

        if hasattr(first_measure, 'keySignature') and first_measure.keySignature is None:
            first_measure.makeMutable()  # must mutate
            outerKeySignatures = part.getElementsByClass(key.KeySignature)
            if outerKeySignatures:
                first_measure.keySignature = outerKeySignatures.first()

        if hasattr(first_measure, 'timeSignature') and first_measure.timeSignature is None:
            first_measure.makeMutable()  # must mutate
            outerTimeSignatures = part.getElementsByClass(meter.TimeSignature)
            if outerTimeSignatures:
                first_measure.timeSignature = outerTimeSignatures.first()

        # see if accidentals/beams/tuplets should be processed
        if not part.streamStatus.haveAccidentalsBeenMade():
            part.makeAccidentals(inPlace=True)
        if not part.streamStatus.beams:
            try:
                part.makeBeams(inPlace=True)
            except exceptions21.StreamException as se:  # no measures or no time sig?
                # incorrectly flagging MusicXMLWarning as not a Warning
                # noinspection PyTypeChecker
                warnings.warn(MusicXMLWarning, str(se))
        if not part.streamStatus.tuplets:
            for m in measures:
                for m_or_v in [m, *m.voices]:
                    stream.makeNotation.makeTupletBrackets(m_or_v, inPlace=True)

        if not self.spannerBundle:
            self.spannerBundle = part.spannerBundle

    def getXmlScorePart(self):
        '''
        make a <score-part> from a music21 Part object and a parsed mxPart (<part>) element.

        contains details about instruments, etc.

        called directly by the ScoreExporter as a late part of the processing.
        '''
        part = self.stream
        mxScorePart = Element('score-part')
        # TODO: identification -- specific metadata... could go here...
        mxScorePart.set('id', self.xmlRoot.get('id'))

        mxPartName = SubElement(mxScorePart, 'part-name')
        if hasattr(part, 'partName') and part.partName is not None:
            mxPartName.text = part.partName
        else:
            mxPartName.text = defaults.partName

        if part.hasStyleInformation and not part.style.printPartName:
            mxPartName.set('print-object', 'no')

        # TODO: part-name-display

        if hasattr(self.stream, 'partAbbreviation') and part.partAbbreviation is not None:
            mxPartAbbreviation = SubElement(mxScorePart, 'part-abbreviation')
            mxPartAbbreviation.text = part.partAbbreviation

            if part.hasStyleInformation and not part.style.printPartAbbreviation:
                mxPartAbbreviation.set('print-object', 'no')

        # TODO: part-abbreviation-display
        # TODO: group

        seen_instrument_classes = set()
        # The first instrument of each Class appears as a <score-instrument>
        for inst in self.instrumentStream:
            # only use the first instance of this class
            if type(inst) in seen_instrument_classes:
                continue
            if (inst.instrumentName is not None
                    or inst.instrumentAbbreviation is not None
                    or inst.midiProgram is not None):
                mxScorePart.append(self.instrumentToXmlScoreInstrument(inst))
                seen_instrument_classes.add(type(inst))

        seen_instrument_classes = set()
        # now iterate again to write <midi-instrument> tags for those
        # same instruments, tags which must follow all <score-instrument> tags.
        for inst in self.instrumentStream:
            # TODO: disambiguate instrument instance with different midi programs?
            if type(inst) in seen_instrument_classes:
                continue
            # TODO: midi-device
            if inst.midiProgram is not None or isinstance(inst, instrument.UnpitchedPercussion):
                mxScorePart.append(self.instrumentToXmlMidiInstrument(inst))
                seen_instrument_classes.add(type(inst))

        return mxScorePart

    def instrumentToXmlScoreInstrument(self, i):
        # noinspection SpellCheckingInspection, PyShadowingNames
        '''
        Convert an :class:`~music21.instrument.Instrument` object to a
        <score-instrument> element and return it.

        >>> i = instrument.Clarinet()
        >>> i.instrumentId = 'clarinet1'
        >>> i.midiChannel = 4
        >>> PEX = musicxml.m21ToXml.PartExporter()
        >>> mxScoreInstrument = PEX.instrumentToXmlScoreInstrument(i)
        >>> PEX.dump(mxScoreInstrument)
        <score-instrument id="clarinet1">
          <instrument-name>Clarinet</instrument-name>
          <instrument-abbreviation>Cl</instrument-abbreviation>
        </score-instrument>

        >>> i.instrumentName = "Klarinette 1."
        >>> i.instrumentAbbreviation = 'Kl.1'
        >>> mxScoreInstrument = PEX.instrumentToXmlScoreInstrument(i)
        >>> PEX.dump(mxScoreInstrument)
        <score-instrument id="clarinet1">
          <instrument-name>Klarinette 1.</instrument-name>
          <instrument-abbreviation>Kl.1</instrument-abbreviation>
        </score-instrument>
        '''
        mxScoreInstrument = Element('score-instrument')
        mxScoreInstrument.set('id', str(i.instrumentId))
        mxInstrumentName = SubElement(mxScoreInstrument, 'instrument-name')
        mxInstrumentName.text = str(i.instrumentName)
        if i.instrumentAbbreviation is not None:
            mxInstrumentAbbreviation = SubElement(mxScoreInstrument, 'instrument-abbreviation')
            mxInstrumentAbbreviation.text = str(i.instrumentAbbreviation)
        # TODO: instrument-sound
        # TODO: solo / ensemble
        # TODO: virtual-instrument

        return mxScoreInstrument

    def instrumentToXmlMidiInstrument(self, i):
        # noinspection PyShadowingNames
        '''
        Convert an instrument object to a <midi-instrument> tag and return the element

        >>> i = instrument.Clarinet()
        >>> i.instrumentId = 'clarinet1'
        >>> i.midiChannel = 4
        >>> PEX = musicxml.m21ToXml.PartExporter()
        >>> mxMidiInstrument = PEX.instrumentToXmlMidiInstrument(i)
        >>> PEX.dump(mxMidiInstrument)
        <midi-instrument id="clarinet1">
          <midi-channel>5</midi-channel>
          <midi-program>72</midi-program>
        </midi-instrument>

        >>> m = instrument.Maracas()
        >>> m.instrumentId = 'my maracas'
        >>> m.midiChannel  # 0-indexed
        9
        >>> m.percMapPitch
        70
        >>> PEX = musicxml.m21ToXml.PartExporter()
        >>> mxMidiInstrument = PEX.instrumentToXmlMidiInstrument(m)
        >>> PEX.dump(mxMidiInstrument)  # 1-indexed in MusicXML
        <midi-instrument id="my maracas">
          <midi-channel>10</midi-channel>
          <midi-unpitched>71</midi-unpitched>
        </midi-instrument>
        '''
        mxMidiInstrument = Element('midi-instrument')
        mxMidiInstrument.set('id', str(i.instrumentId))
        if i.midiChannel is None:
            i.autoAssignMidiChannel()
            # TODO: allocate channels from a higher level
        mxMidiChannel = SubElement(mxMidiInstrument, 'midi-channel')
        mxMidiChannel.text = str(i.midiChannel + 1)
        # TODO: midi-name
        # TODO: midi-bank
        if i.midiProgram is not None:
            mxMidiProgram = SubElement(mxMidiInstrument, 'midi-program')
            mxMidiProgram.text = str(i.midiProgram + 1)
        if isinstance(i, instrument.UnpitchedPercussion) and i.percMapPitch is not None:
            mxMidiUnpitched = SubElement(mxMidiInstrument, 'midi-unpitched')
            mxMidiUnpitched.text = str(i.percMapPitch + 1)
        # TODO: volume
        # TODO: pan
        # TODO: elevation
        return mxMidiInstrument


# ------------------------------------------------------------------------------

class MeasureExporter(XMLExporterBase):
    classesToMethods = OrderedDict(
        [
            ('Note', 'noteToXml'),
            ('NoChord', 'noChordToXml'),
            ('ChordWithFretBoard', 'chordWithFretBoardToXml'),  # these three
            ('ChordSymbol', 'chordSymbolToXml'),  # must come before
            ('RomanNumeral', 'romanNumeralToXml'),  # ChordBase
            ('ChordBase', 'chordToXml'),
            ('Unpitched', 'unpitchedToXml'),
            ('Rest', 'restToXml'),
            ('Dynamic', 'dynamicToXml'),
            ('Segno', 'segnoToXml'),
            ('Coda', 'codaToXml'),
            ('TempoText', 'tempoIndicationToXml'),
            ('MetronomeMark', 'tempoIndicationToXml'),
            ('MetricModulation', 'tempoIndicationToXml'),
            ('TextExpression', 'textExpressionToXml'),
            ('RepeatExpression', 'textExpressionToXml'),
            ('RehearsalMark', 'rehearsalMarkToXml'),
        ]
    )
    # these need to be wrapped in an attributes tag if not at the beginning of the measure.
    wrapAttributeMethodClasses = OrderedDict(
        [('Clef', 'clefToXml'),
         ('KeySignature', 'keySignatureToXml'),
         ('TimeSignature', 'timeSignatureToXml'),
         ])

    ignoreOnParseClasses = {'LayoutBase', 'Barline'}

    def __init__(self,
                 measureObj: stream.Measure | None = None,
                 parent: PartExporter | None = None):
        super().__init__()
        if measureObj is None:  # no point, but...
            self.stream = stream.Measure()
        else:
            self.stream = measureObj

        self.parent = parent
        self.xmlRoot = Element('measure')
        self.currentDivisions = defaults.divisionsPerQuarter

        # Adding ids to measure in the MusicXML export
        _synchronizeIds(self.xmlRoot, self.stream)

        # TODO: allow for mid-measure transposition changes.
        self.transpositionInterval = None
        self.mxTranspose = None
        self.measureOffsetStart = 0.0
        self.offsetInMeasure = 0.0
        self.currentVoiceId: int | str | None = None
        self.nextFreeVoiceNumber: int = 1
        self.nextArpeggioNumber: int = 1
        self.arpeggioNumbers: dict[expressions.ArpeggioMarkSpanner, int] = {}

        self.rbSpanners: list[spanner.RepeatBracket] = []  # repeatBracket spanners

        if parent is None:
            self.spannerBundle = spanner.SpannerBundle()
        else:
            self.spannerBundle = parent.spannerBundle

        self.objectSpannerBundle = self.spannerBundle  # will change for each element.

    def parse(self):
        '''
        main parse call.

        deals with transposing, repeat brackets, setting measureNumber and width,
        the first mxPrint, the first <attributes> tag, the left barline, parsing all internal
        elements, setting the right barline, then returns the root <measure> tag.
        '''
        self.setTranspose()
        self.setRbSpanners()
        self.setMxAttributes()
        self.setMxPrint()
        self.setMxAttributesObjectForStartOfMeasure()
        self.setLeftBarline()
        # BIG ONE
        self.mainElementsParse()
        # continue
        self.setRightBarline()
        return self.xmlRoot

    def mainElementsParse(self):
        '''
        deals with parsing all the elements in a stream, whether it has voices or not.
        '''
        m = self.stream
        # need to handle objects in order when creating musicxml
        # we thus assume that objects are sorted here

        if not m.hasVoices():
            self.parseFlatElements(m, backupAfterwards=False)
            return

        nonVoiceMeasureItems = m.getElementsNotOfClass(stream.Voice).stream()
        self.parseFlatElements(nonVoiceMeasureItems, backupAfterwards=True)

        allVoices = list(m.voices)
        for i, v in enumerate(allVoices):
            if i == len(allVoices) - 1:
                backupAfterwards = False
            else:
                backupAfterwards = True

            # Assumes voices are flat...
            self.parseFlatElements(v, backupAfterwards=backupAfterwards)

    def moveForward(self, byOffset: OffsetQL):
        '''
        Moves self.offsetInMeasure forward by an OffsetQL, appending the appropriate
        <forward> tag (expressed in divisions) to self.xmlRoot.

        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> len(MEX.xmlRoot)
        0
        >>> MEX.moveForward(1)
        >>> MEX.dump(MEX.xmlRoot)
        <measure>
          <forward>
            <duration>10080</duration>
          </forward>
        </measure>
        >>> len(MEX.xmlRoot)
        1

        '''
        amountToMoveForward: int = int(round(byOffset * self.currentDivisions))
        if amountToMoveForward:
            mxForward = Element('forward')
            mxDuration = SubElement(mxForward, 'duration')
            mxDuration.text = str(amountToMoveForward)
            self.xmlRoot.append(mxForward)
            self.offsetInMeasure += byOffset

    def moveBackward(self, byOffset: OffsetQL):
        '''
        Moves self.offsetInMeasure backward by an OffsetQL, appending the appropriate
        <backup> tag (expressed in divisions) to self.xmlRoot.

        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> len(MEX.xmlRoot)
        0
        >>> MEX.moveBackward(2)
        >>> MEX.dump(MEX.xmlRoot)
        <measure>
          <backup>
            <duration>20160</duration>
          </backup>
        </measure>
        >>> len(MEX.xmlRoot)
        1
        '''
        amountToBackup: int = int(round(byOffset * self.currentDivisions))
        if amountToBackup:
            mxBackup = Element('backup')
            mxDuration = SubElement(mxBackup, 'duration')
            mxDuration.text = str(amountToBackup)
            self.xmlRoot.append(mxBackup)
            self.offsetInMeasure -= byOffset

    def parseFlatElements(
        self,
        m: stream.Measure | stream.Voice,
        *,
        backupAfterwards: bool = False
    ) -> None:
        '''
        Deals with parsing all the elements in .elements, assuming that .elements is flat.

        m here can be a Measure or Voice, but flat...

        If m is a 'Voice' class, we use the .id element to set self.currentVoiceId and then
        send a backup tag to go back to the beginning of the measure.

        Note that if the .id is high enough to be an id(x) memory location, then a small
        voice number is used instead.
        '''
        self.offsetInMeasure = 0.0
        voiceId: int | str | None
        if isinstance(m, stream.Voice):
            if isinstance(m.id, int) and m.id < defaults.minIdNumberToConsiderMemoryLocation:
                voiceId = m.id
                self.nextFreeVoiceNumber = voiceId + 1
            elif isinstance(m.id, int):
                # This voice id is actually a memory location, so we need to change it
                # to a low number so it can be used in MusicXML.
                voiceId = self.nextFreeVoiceNumber
                self.nextFreeVoiceNumber += 1
            else:
                voiceId = m.id
        else:
            voiceId = None

        self.currentVoiceId = voiceId

        # We order things differently if there are any SpannerAnchors in the flat stream.
        # If there are SpannerAnchors, we do two passes. The first pass skips all
        # relatedSpanners processing, and then the second pass goes back to the
        # beginning and does all the relatedSpanners processing.
        # If there are no SpannerAnchors, we do one pass, doing any relatedSpanners
        # processing as we process each element.

        hasSpannerAnchors: bool = bool(m.getElementsByClass(spanner.SpannerAnchor))

        # First (and possibly only) pass:
        # Group all objects by offsets and then do a different order than normal sort.
        # That way chord symbols and other 0-width objects appear before notes as much as
        # possible.
        objIterator: OffsetIterator[base.Music21Object] = OffsetIterator(m)
        for objGroup in objIterator:
            groupOffset = m.elementOffset(objGroup[0])
            offsetToMoveForward = groupOffset - self.offsetInMeasure
            # PyCharm typechecker does not properly read __next__ from OffsetIterator
            # noinspection PyTypeChecker
            if offsetToMoveForward > 0 and any(
                    isinstance(obj, (note.GeneralNote, clef.Clef)) for obj in objGroup):
                # gap in stream between GeneralNote/Clef objects: create <forward>
                self.moveForward(offsetToMoveForward)

            notesForLater = []
            # noinspection PyTypeChecker
            for obj in objGroup:
                # we do all non-note elements (including ChordSymbols not written as chord)
                # first before note elements, in musicxml
                if isinstance(obj, spanner.SpannerAnchor):
                    # nothing to do with this (only relatedSpanners, and
                    # we will do that below)
                    continue

                if isinstance(obj, note.GeneralNote) and (
                    not (isHarm := isinstance(obj, harmony.Harmony))
                    or (isHarm and obj.writeAsChord)
                ):
                    notesForLater.append(obj)
                else:
                    if hasSpannerAnchors:
                        self.parseOneElement(obj, AppendSpanners.NONE)
                    else:
                        self.parseOneElement(obj, AppendSpanners.NORMAL)

            for n in notesForLater:
                if n.isRest and n.style.hideObjectOnPrint and n.duration.type == 'inexpressible':
                    # Prefer a gap in stream, to be filled with a <forward> tag by
                    # fill_gap_with_forward_tag() rather than raising exceptions
                    continue
                if hasSpannerAnchors:
                    self.parseOneElement(n, AppendSpanners.NONE)
                else:
                    self.parseOneElement(n, AppendSpanners.NORMAL)

        # Second pass: If this flat stream (measure/voice) contains any SpannerAnchors, we
        # will perform a second pass, emitting any pre/postList for any object that is
        # functioning as a spanner anchor (the SpannerAnchors, as well as any GeneralNotes
        # that start or end spanners).

        # Before second pass, stash off self.offsetInMeasure in case we need to jump forward
        # to it after the second pass.
        firstPassEndOffsetInMeasure: OffsetQL = self.offsetInMeasure

        if hasSpannerAnchors:
            # return to the beginning of the measure, to emit any SpannerAnchors.
            if self.offsetInMeasure:
                self.moveBackward(self.offsetInMeasure)

            objIterator = OffsetIterator(m)
            for objGroup in objIterator:
                # noinspection PyTypeChecker
                if not any(self._hasRelatedSpanners(obj) for obj in objGroup):
                    continue
                groupOffset = m.elementOffset(objGroup[0])
                offsetToMoveForward = groupOffset - self.offsetInMeasure
                if offsetToMoveForward > 0:
                    # gap in stream before spanner start/stop: create <forward>
                    self.moveForward(offsetToMoveForward)

                # noinspection PyTypeChecker
                for obj in objGroup:
                    self.parseOneElement(obj, AppendSpanners.RELATED_ONLY)

        if backupAfterwards:
            # return to the beginning of the measure.
            if self.offsetInMeasure:
                self.moveBackward(self.offsetInMeasure)
        else:
            # if necessary, jump to end of the measure.
            if self.offsetInMeasure < firstPassEndOffsetInMeasure:
                self.moveForward(firstPassEndOffsetInMeasure)

        self.currentVoiceId = None

    def parseOneElement(
        self,
        obj,
        appendSpanners: AppendSpanners = AppendSpanners.NORMAL
    ):
        '''
        parse one element completely and add it to xmlRoot, updating
        offsetInMeasure, etc.
        '''
        root = self.xmlRoot
        self.objectSpannerBundle = self.spannerBundle.getBySpannedElement(obj)
        preList, postList = self.relatedSpanners(obj)

        # pre-spanners (if appropriate)
        if appendSpanners != AppendSpanners.NONE:
            # emit the related spanners that precede the element
            for sp in preList:
                root.append(sp)

        # element itself (if appropriate)
        if appendSpanners != AppendSpanners.RELATED_ONLY:
            # emit the object
            classes = obj.classes
            # Ignore Harmony objects having writeAsChord = False
            if 'GeneralNote' in classes and getattr(obj, 'writeAsChord', True):
                self.offsetInMeasure += obj.duration.quarterLength

            # turn inexpressible durations into complex durations (unless unlinked)
            if obj.duration.type == 'inexpressible':
                obj.duration.quarterLength = obj.duration.quarterLength
                objList = obj.splitAtDurations()
            # make dotGroups into normal notes
            elif len(obj.duration.dotGroups) > 1:
                obj.duration.splitDotGroups(inPlace=True)
                objList = obj.splitAtDurations()
            # otherwise, splitAtDurations() was already called by parse(), no need to repeat
            else:
                objList = [obj]

            parsedObject = False
            for className, methName in self.classesToMethods.items():
                if className in classes:
                    meth = getattr(self, methName)
                    for o in objList:
                        meth(o)
                    parsedObject = True
                    break

            # these are classes that need to be wrapped in an attribute tag if
            # not at the beginning of a measure
            for className, methName in self.wrapAttributeMethodClasses.items():
                if className in classes:
                    meth = getattr(self, methName)
                    for o in objList:
                        self.wrapObjectInAttributes(o, meth)
                    parsedObject = True
                    break

            if parsedObject is False:
                for className in classes:
                    if className in self.ignoreOnParseClasses:
                        parsedObject = True
                        break
                if parsedObject is False:
                    environLocal.printDebug(['did not convert object', obj])

        else:  # appendSpanners == AppendSpanners.RELATED_ONLY
            # skip the element itself, just move forward by element duration
            if postList and obj.quarterLength > 0:
                # gap in stream before spanner stop: create <forward>
                # Ignore Harmony objects having writeAsChord = False
                if 'GeneralNote' in obj.classes and getattr(obj, 'writeAsChord', True):
                    self.moveForward(obj.duration.quarterLength)

        # post-spanners (if appropriate)
        if appendSpanners != AppendSpanners.NONE:
            # emit the related spanners that follow the element
            for sp in postList:
                root.append(sp)

    def _hasRelatedSpanners(self, obj) -> bool:
        '''
        returns True if and only if:
        (1) there are spanners related to the object that should appear before the object
        to the <measure> tag, or (2) there are spanners related to the object that should
        appear after the object in the measure tag.
        '''
        spannerBundle = self.spannerBundle.getBySpannedElement(obj)
        if not spannerBundle:
            return False

        # this list of spanner classes must match the paramsSet keys in relatedSpanners()
        for thisSpanner in spannerBundle.getByClass((spanner.Ottava,
                                                     dynamics.DynamicWedge,
                                                     spanner.Line)):
            if thisSpanner.isFirst(obj) or thisSpanner.isLast(obj):
                return True

        return False

    def relatedSpanners(
        self,
        target: base.Music21Object
    ) -> tuple[t.Sequence[Element], t.Sequence[Element]]:
        '''
        return two lists or empty tuples:
        (1) spanners related to the object that should appear before the object
        to the <measure> tag. (2) spanners related to the object that should appear after the
        object in the measure tag.
        '''
        def getProc(su, innerTarget):
            if len(su) == 1:  # have a one element wedge
                proc = ('first', 'last')
            else:
                if su.isFirst(innerTarget) and su.isLast(innerTarget):
                    proc = ('first', 'last')  # same element can be first and last
                elif su.isFirst(innerTarget):
                    proc = ('first',)
                elif su.isLast(innerTarget):
                    proc = ('last',)
                else:
                    proc = ()
            return proc

        spannerBundle = self.objectSpannerBundle
        if not spannerBundle:
            return (), ()

        preList: list[Element] = []
        postList: list[Element] = []

        # number, type is assumed;
        # tuple: first is the elementType,
        #        second: tuple of parameters to set,
        paramsSet = {'Ottava': ('octave-shift', ('size',)),
                     # TODO: attrGroup: dashed-formatting, print-style
                     'DynamicWedge': ('wedge', ('spread',)),
                     # TODO: niente, attrGroups: line-type, dashed-formatting, position, color
                     'Line': ('bracket', ('line-end', 'end-length'))
                     # TODO: dashes???
                     }

        for m21spannerClass, infoTuple in paramsSet.items():
            mxTag, parameterSet = infoTuple
            for thisSpanner in spannerBundle.getByClass(m21spannerClass):
                for posSub in getProc(thisSpanner, target):
                    # create new tag
                    mxElement = Element(mxTag)
                    _synchronizeIds(mxElement, thisSpanner)

                    mxElement.set('number', str(thisSpanner.idLocal))
                    if m21spannerClass == 'Line':
                        mxElement.set('line-type', str(thisSpanner.lineType))

                    if posSub == 'first':
                        spannerParams = self._spannerStartParameters(m21spannerClass, thisSpanner)
                    elif posSub == 'last':
                        spannerParams = self._spannerEndParameters(m21spannerClass, thisSpanner)
                    else:
                        spannerParams = {}

                    if 'type' in spannerParams:
                        mxElement.set('type', str(spannerParams['type']))

                    for attrName in parameterSet:
                        if attrName in spannerParams and spannerParams[attrName] is not None:
                            mxElement.set(attrName, str(spannerParams[attrName]))

                    mxDirection = Element('direction')
                    _synchronizeIds(mxDirection, thisSpanner)

                    # Not all spanners have placements
                    if hasattr(thisSpanner, 'placement') and thisSpanner.placement is not None:
                        mxDirection.set('placement', str(thisSpanner.placement))
                    mxDirectionType = SubElement(mxDirection, 'direction-type')
                    mxDirectionType.append(mxElement)
                    # Not todo: ID: direction-type has no direct music21 equivalent.

                    if posSub == 'first':
                        preList.append(mxDirection)
                    else:
                        postList.append(mxDirection)

        return preList, postList

    @staticmethod
    def _spannerStartParameters(spannerClass, sp):
        '''
        Return a dict of the parameters for the start of this spanner required by MusicXML output.

        >>> ssp = musicxml.m21ToXml.MeasureExporter._spannerStartParameters

        >>> ottava = spanner.Ottava(type='8va')
        >>> st = ssp('Ottava', ottava)
        >>> st['type']  # this is the opposite of what you might expect...
        'down'
        >>> st['size']
        8

        >>> cresc = dynamics.Crescendo()
        >>> st = ssp('DynamicWedge', cresc)
        >>> st['type']
        'crescendo'
        >>> st['spread']
        0

        >>> diminuendo = dynamics.Diminuendo()
        >>> st = ssp('DynamicWedge', diminuendo)
        >>> st['type']
        'diminuendo'
        >>> st['spread']
        15
        '''
        post = {'type': 'start'}
        if spannerClass == 'Ottava':
            post['size'] = sp.shiftMagnitude()
            post['type'] = sp.shiftDirection(reverse=True)  # up or down
        elif spannerClass == 'Line':
            post['line-end'] = sp.startTick
            post['end-length'] = sp.startHeight
        elif spannerClass == 'DynamicWedge':
            post['type'] = sp.type
            if sp.type == 'crescendo':
                post['spread'] = 0
                if sp.niente:
                    post['niente'] = 'yes'
            else:
                post['spread'] = sp.spread

        return post

    @staticmethod
    def _spannerEndParameters(spannerClass, sp):
        '''
        Return a dict of the parameters for the end of this spanner required by MusicXML output.

        >>> ottava = spanner.Ottava(type='8va')
        >>> en = musicxml.m21ToXml.MeasureExporter._spannerEndParameters('Ottava', ottava)
        >>> en['type']
        'stop'
        >>> en['size']
        8
        '''
        post = {'type': 'stop'}
        if spannerClass == 'Ottava':
            post['size'] = sp.shiftMagnitude()
        elif spannerClass == 'Line':
            post['line-end'] = sp.endTick
            post['end-length'] = sp.endHeight
        elif spannerClass == 'DynamicWedge':
            if sp.type == 'crescendo':
                post['spread'] = sp.spread
            else:
                post['spread'] = 0
                if sp.niente:
                    post['niente'] = 'yes'

        return post

    def getArpeggioNumber(self, arp: expressions.ArpeggioMarkSpanner) -> int:
        arpeggioNumber: int = self.arpeggioNumbers.get(arp, -1)
        if arpeggioNumber == -1:
            arpeggioNumber = self.nextArpeggioNumber
            self.nextArpeggioNumber += 1
            if self.nextArpeggioNumber > 16:
                self.nextArpeggioNumber = 1
            self.arpeggioNumbers[arp] = arpeggioNumber

        return arpeggioNumber

    def objectAttachedSpannersToNotations(
        self,
        obj: base.Music21Object,
        noteIndexInChord: int = 0,
        objectSpannerBundle: spanner.SpannerBundle | None = None
    ) -> list[Element]:
        '''
        return a list of <notations> from spanners related to the object that should appear
        in the notations tag (slurs, slides, etc.)

        >>> n0 = note.Note('C')
        >>> n1 = note.Note('D')
        >>> trem = expressions.TremoloSpanner([n0, n1])
        >>> m = stream.Measure()
        >>> m.insert(0, trem)
        >>> m.append(n0)
        >>> m.append(n1)
        >>> mex = musicxml.m21ToXml.MeasureExporter(m)
        >>> out = mex.objectAttachedSpannersToNotations(n0, objectSpannerBundle=m.spannerBundle)
        >>> out
        [<Element 'ornaments' at 0x1114d9408>]
        >>> mex.dump(out[0])
        <ornaments>
          <tremolo type="start">3</tremolo>
        </ornaments>

        >>> out = mex.objectAttachedSpannersToNotations(n1, objectSpannerBundle=m.spannerBundle)
        >>> mex.dump(out[0])
        <ornaments>
          <tremolo type="stop">3</tremolo>
        </ornaments>
        '''
        notations: list[Element] = []
        if objectSpannerBundle is not None:
            sb = objectSpannerBundle
        else:
            sb = self.objectSpannerBundle

        if not sb:
            return notations

        self.appendArpeggioMarkSpannersToNotations(obj, noteIndexInChord, notations, sb)

        isSingleNoteOrFirstInChord = (noteIndexInChord == 0)

        # Everything below this point is only for single note or first note in chord
        if not isSingleNoteOrFirstInChord:
            return notations

        ornaments = []

        for su in sb.getByClass('Slur'):
            mxSlur = Element('slur')
            if su.isFirst(obj):
                mxSlur.set('type', 'start')
                self.setLineStyle(mxSlur, su)
                self.setPosition(mxSlur, su)
                self.setStyleAttributes(mxSlur,
                                        su,
                                        ('bezier-offset', 'bezier-offset2',
                                         'bezier-x', 'bezier-y',
                                         'bezier-x2', 'bezier-y2'),
                                        )
                if su.placement is not None:
                    mxSlur.set('placement', str(su.placement))
            elif su.isLast(obj):
                mxSlur.set('type', 'stop')
            else:
                continue  # do not put a notation on mid-slur notes.
            mxSlur.set('number', str(su.idLocal))
            notations.append(mxSlur)

        for su in sb.getByClass('Glissando'):
            if su.slideType == 'continuous':
                mxTag = 'slide'
            else:
                mxTag = 'glissando'

            mxGlissando = Element(mxTag)
            mxGlissando.set('number', str(su.idLocal))
            if su.lineType is not None:
                mxGlissando.set('line-type', str(su.lineType))
            # is this note first in this spanner?
            if su.isFirst(obj):
                if su.label is not None:
                    mxGlissando.text = str(su.label)
                mxGlissando.set('type', 'start')
            elif su.isLast(obj):
                mxGlissando.set('type', 'stop')
            else:
                continue  # do not put a notation on mid-gliss notes.

            _synchronizeIds(mxGlissando, su)
            # placement???
            notations.append(mxGlissando)

        # These add to Ornaments...

        for su in sb.getByClass('TremoloSpanner'):
            mxTrem = Element('tremolo')
            mxTrem.text = str(su.numberOfMarks)
            if su.isFirst(obj):
                mxTrem.set('type', 'start')
                if su.placement is not None:
                    mxTrem.set('placement', str(su.placement))
            elif su.isLast(obj):
                mxTrem.set('type', 'stop')
            else:
                # this is always an error for tremolos
                environLocal.printDebug(
                    ['spanner w/ a component that is neither a start nor an end.', su, obj])
            # Tremolos get in a separate ornaments tag...
            ornaments.append(mxTrem)

        for su in sb.getByClass('TrillExtension'):
            mxWavyLine = Element('wavy-line')
            mxWavyLine.set('number', str(su.idLocal))
            isFirstOrLast = False
            isFirstANDLast = False
            # is this note first in this spanner?
            if su.isFirst(obj):
                mxWavyLine.set('type', 'start')
                # print('Trill is first')
                isFirstOrLast = True
                if su.placement is not None:
                    mxWavyLine.set('placement', su.placement)

            # a Trill on a single Note can be both first and last!
            if su.isLast(obj):
                if isFirstOrLast is True:
                    isFirstANDLast = True
                else:
                    mxWavyLine.set('type', 'stop')
                    isFirstOrLast = True
                # print('Trill is last')

            if isFirstOrLast is False:
                continue  # do not put a wavy-line tag on mid-trill notes
            ornaments.append(mxWavyLine)
            if isFirstANDLast is True:
                # make another one...
                mxWavyLine = Element('wavy-line')
                mxWavyLine.set('number', str(su.idLocal))
                mxWavyLine.set('type', 'stop')
                ornaments.append(mxWavyLine)

        if ornaments:
            mxOrnGroup = Element('ornaments')
            for mxOrn in ornaments:
                mxOrnGroup.append(mxOrn)
            notations.append(mxOrnGroup)

        return notations

    def objectAttachedSpannersToTechnicals(self, obj, objectSpannerBundle=None):
        '''
        return a list of <technical> from spanners related to the object that should appear
        in the technical tag of the notations tag (hammer-on, pull-off etc.)

        >>> n0 = note.Note('C')
        >>> n1 = note.Note('D')
        >>> n2 = note.Note('F')
        >>> n3 = note.Note('E')
        >>> hammerOn01 = articulations.HammerOn([n0, n1])
        >>> pullOff23 = articulations.PullOff([n2, n3])
        >>> m = stream.Measure()
        >>> m.insert(0, hammerOn01)
        >>> m.insert(0, pullOff23)
        >>> m.append(n0)
        >>> m.append(n1)
        >>> m.append(n2)
        >>> m.append(n3)
        >>> mex = musicxml.m21ToXml.MeasureExporter(m)
        >>> out = mex.objectAttachedSpannersToTechnicals(n0, m.spannerBundle)
        >>> out
        [<Element 'hammer-on' at 0x102857f40>]
        >>> mex.dump(out[0])
        <hammer-on number="1" type="start">H</hammer-on>
        >>> out = mex.objectAttachedSpannersToTechnicals(n3, m.spannerBundle)
        >>> mex.dump(out[0])
        <pull-off number="1" type="stop" />

        OMIT_FROM_DOCS

        The other permutations of class and first/last:

        >>> out = mex.objectAttachedSpannersToTechnicals(n1, m.spannerBundle)
        >>> mex.dump(out[0])
        <hammer-on number="1" type="stop" />
        >>> out = mex.objectAttachedSpannersToTechnicals(n2, m.spannerBundle)
        >>> mex.dump(out[0])
        <pull-off number="1" type="start">P</pull-off>
        '''
        technicals = []
        if objectSpannerBundle is not None:
            sb = objectSpannerBundle
        else:
            sb = self.objectSpannerBundle

        if not sb:
            return technicals

        for su in sb.getByClass(articulations.HammerOn):
            mxHammerOn = Element('hammer-on')
            if su.isFirst(obj):
                mxHammerOn.set('type', 'start')
                mxHammerOn.text = 'H'
            elif su.isLast(obj):
                mxHammerOn.set('type', 'stop')
            else:
                continue
            mxHammerOn.set('number', '1')
            technicals.append(mxHammerOn)

        for su in sb.getByClass(articulations.PullOff):
            mxPullOff = Element('pull-off')
            if su.isFirst(obj):
                mxPullOff.set('type', 'start')
                mxPullOff.text = 'P'
            elif su.isLast(obj):
                mxPullOff.set('type', 'stop')
            else:
                continue
            mxPullOff.set('number', '1')
            technicals.append(mxPullOff)

        return technicals

    def appendArpeggioMarkSpannersToNotations(
        self,
        obj: base.Music21Object,
        noteIndexInChord: int,
        notations: list[Element],
        sb: spanner.SpannerBundle,
    ) -> None:
        for ams in sb.getByClass(expressions.ArpeggioMarkSpanner):
            if not ams.hasSpannedElement(obj):
                continue

            # putting this check inside the loop rather than outside,
            # because it'll run rarely.
            sub_obj = obj
            if isinstance(obj, chord.Chord):
                sub_obj = obj[noteIndexInChord]

            mxArpeggio: Element | None = None
            if ams.type == 'non-arpeggio':
                min_note, max_note = ams.noteExtremes()
                # <non-arpeggiate> goes only on top and bottom note in chord
                if sub_obj is min_note:
                    mxArpeggio = Element('non-arpeggiate')
                    mxArpeggio.set('type', 'bottom')
                elif sub_obj is max_note:
                    mxArpeggio = Element('non-arpeggiate')
                    mxArpeggio.set('type', 'top')
            else:
                mxArpeggio = Element('arpeggiate')
                if ams.type != 'normal':
                    mxArpeggio.set('direction', ams.type)
            if mxArpeggio is not None and (len(ams) > 1 or (len(ams) == 1 and len(ams[0]) > 1)):
                # There is more than one GeneralNote in the arpeggio, so we must
                # add a number attribute that will be the same for all GeneralNotes
                # in this spanner.  In MusicXML this number must be between
                # 1 and 16.  We just cycle through that range.
                arpeggioNumber: int = self.getArpeggioNumber(ams)
                mxArpeggio.set('number', str(arpeggioNumber))
            if mxArpeggio is not None:
                notations.append(mxArpeggio)

    def noteToXml(self, n: note.GeneralNote, noteIndexInChord=0, chordParent=None):
        # noinspection PyShadowingNames
        '''
        Translate a music21 :class:`~music21.note.Note` or a Rest into a
        ElementTree, note element.

        Note that, some note-attached spanners, such
        as octave shifts, produce direction (and direction types)
        in this method.

        >>> n = note.Note('D#5')
        >>> n.quarterLength = 3
        >>> n.volume.velocityScalar = 0.5
        >>> n.style.color = 'silver'

        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> len(MEX.xmlRoot)
        0
        >>> mxNote = MEX.noteToXml(n)
        >>> mxNote
        <Element 'note' at 0x10113cb38>
        >>> MEX.dump(mxNote)
        <note color="#C0C0C0" dynamics="70.56">
          <pitch>
            <step>D</step>
            <alter>1</alter>
            <octave>5</octave>
          </pitch>
          <duration>30240</duration>
          <type>half</type>
          <dot />
          <accidental>sharp</accidental>
          <notehead color="#C0C0C0" parentheses="no">normal</notehead>
        </note>
        >>> len(MEX.xmlRoot)
        1


        >>> r = note.Rest()
        >>> r.quarterLength = 1/3
        >>> r.duration.tuplets[0].type = 'start'
        >>> mxRest = MEX.noteToXml(r)
        >>> MEX.dump(mxRest)
        <note>
          <rest />
          <duration>3360</duration>
          <type>eighth</type>
          <time-modification>
            <actual-notes>3</actual-notes>
            <normal-notes>2</normal-notes>
            <normal-type>eighth</normal-type>
          </time-modification>
          <notations>
            <tuplet bracket="yes" number="1" placement="above" type="start">
              <tuplet-actual>
                <tuplet-number>3</tuplet-number>
                <tuplet-type>eighth</tuplet-type>
              </tuplet-actual>
              <tuplet-normal>
                <tuplet-number>2</tuplet-number>
                <tuplet-type>eighth</tuplet-type>
              </tuplet-normal>
            </tuplet>
          </notations>
        </note>
        >>> len(MEX.xmlRoot)
        2

        >>> n.notehead = 'diamond'
        >>> n.articulations.append(articulations.Pizzicato())
        >>> mxNote = MEX.noteToXml(n)
        >>> MEX.dump(mxNote)
        <note color="#C0C0C0" dynamics="70.56" pizzicato="yes">
          ...
          <notehead color="#C0C0C0" parentheses="no">diamond</notehead>
        </note>

        Notes with complex durations need to be simplified before coming here
        otherwise they raise :class:`MusicXMLExportException`:

        >>> nComplex = note.Note()
        >>> nComplex.duration.quarterLength = 5.0
        >>> mxComplex = MEX.noteToXml(nComplex)
        Traceback (most recent call last):
        music21.musicxml.xmlObjects.MusicXMLExportException:
        Cannot convert complex durations to MusicXML.
        Try exporting with makeNotation=True or manually running splitAtDurations()

        TODO: Test with spanners...

        '''
        addChordTag = (noteIndexInChord != 0)
        setb = _setAttributeFromAttribute

        mxNote = Element('note')
        chordOrN: note.GeneralNote
        if chordParent is None:
            chordOrN = n
        else:
            chordOrN = chordParent
            # Ensure style is read from `n` before reading from `chordOrN`
            self.setPrintStyle(mxNote, n)  # sets color

        # self.setFont(mxNote, chordOrN)
        self.setPrintStyle(mxNote, chordOrN)  # sets color
        # TODO: attr-group: printout -- replaces print-object, print-spacing below (3.1)
        # TODO: attr: print-leger -- musicxml 3.1
        if (isinstance(chordOrN, note.NotRest)
                and chordOrN.hasVolumeInformation()
                and chordOrN.volume.velocityScalar is not None):
            vel = chordOrN.volume.velocityScalar * 100 * (127 / 90)
            mxNote.set('dynamics', f'{vel:.2f}')

        # TODO: attr: end-dynamics
        # TODO: attr: attack
        # TODO: attr: release
        # TODO: attr: time-only
        _synchronizeIds(mxNote, n)

        d = chordOrN.duration

        if isinstance(d, duration.GraceDuration):
            graceElement = SubElement(mxNote, 'grace')
            try:
                if d.slash in (True, False):
                    setb(d, graceElement, 'slash', transform=xmlObjects.booleanToYesNo)

                if d.stealTimePrevious is not None:
                    setb(d,
                         graceElement,
                         'steal-time-previous',
                         transform=xmlObjects.fractionToPercent)

                if d.stealTimeFollowing is not None:
                    setb(d,
                         graceElement,
                         'steal-time-following',
                         transform=xmlObjects.fractionToPercent)
                # TODO: make-time -- specifically not implemented for now.

            except AttributeError:
                environLocal.warn(f'Duration set as Grace while not being a GraceDuration {d}')

        # TODO: cue... / cue-grace

        self.setPrintObject(mxNote, n)
        if n.hasStyleInformation and n.style.hideObjectOnPrint is True:
            mxNote.set('print-spacing', 'yes')

        for art in chordOrN.articulations:
            if 'Pizzicato' in art.classes:
                mxNote.set('pizzicato', 'yes')

        if addChordTag:
            SubElement(mxNote, 'chord')

        if hasattr(n, 'pitch'):
            n = t.cast(note.Note, n)
            mxPitch = self.pitchToXml(n.pitch)
            mxNote.append(mxPitch)
        elif n.isRest:
            SubElement(mxNote, 'rest')

        if d.isGrace is not True:
            mxDuration = self.durationXml(d)
            mxNote.append(mxDuration)
            # divisions only
        # TODO: skip if cue:
        if n.tie is not None:
            mxTieList = self.tieToXmlTie(n.tie)
            for mxTie in mxTieList:
                mxNote.append(mxTie)

        if isinstance(n, note.NotRest):
            self.setNoteInstrument(n, mxNote, chordParent)
        self.setEditorial(mxNote, n)
        if self.currentVoiceId is not None:
            mxVoice = SubElement(mxNote, 'voice')
            mxVoice.text = str(self.currentVoiceId)

        mxType = Element('type')
        if d.isGrace is True and d.type == 'zero':
            # Default type-less grace durations to eighths
            mxType.text = 'eighth'
        else:
            try:
                mxType.text = typeToMusicXMLType(d.type)
            except MusicXMLExportException:
                if isinstance(n, note.Rest) and helpers.isFullMeasureRest(n):
                    # type will be removed in xmlToRest()
                    pass
                else:
                    raise

        self.setStyleAttributes(mxType, n, 'size', 'noteSize')
        mxNote.append(mxType)
        for unused_dotCounter in range(d.dots):
            SubElement(mxNote, 'dot')
            # TODO: dot placement...

        if (isinstance(n, note.Note)
                and n.pitch.accidental is not None
                and n.pitch.accidental.displayStatus in (True, None)):
            mxAccidental = self.accidentalToMx(n.pitch.accidental)
            mxNote.append(mxAccidental)

        if len(d.tuplets) == 1:
            mxTimeModification = self.tupletToTimeModification(d.tuplets[0])
            mxNote.append(mxTimeModification)
        elif len(d.tuplets) > 1:
            # create a composite tuplet to use as a timeModification guide
            tupletFraction = fractions.Fraction(d.aggregateTupletMultiplier()
                                                ).limit_denominator(1000)
            tempTuplet = duration.Tuplet(tupletFraction.denominator,
                                         tupletFraction.numerator)
            # don't set durationType until this can be done properly.
            # tempTuplet.setDurationType(d.tuplets[0].durationNormal.type,
            #                            d.tuplets[0].durationNormal.dots)
            mxTimeModification = self.tupletToTimeModification(tempTuplet)
            mxNote.append(mxTimeModification)

        # stem...
        stemDirection = None
        # if we are not in a chord, or we are the first note of a chord, get stem
        # direction from the chordOrNote object
        if (addChordTag is False
                and isinstance(chordOrN, note.NotRest)
                and chordOrN.stemDirection != 'unspecified'):
            chordOrN = t.cast(note.NotRest, chordOrN)
            stemDirection = chordOrN.stemDirection
        # or if we are in a chord, but the sub-note has its own stem direction,
        # record that.
        elif (chordOrN is not n
                and isinstance(n, note.NotRest)
                and n.stemDirection != 'unspecified'):
            n = t.cast(note.NotRest, n)
            stemDirection = n.stemDirection

        if stemDirection is not None:
            mxStem = SubElement(mxNote, 'stem')
            sdText = stemDirection
            if sdText == 'noStem':
                sdText = 'none'
            mxStem.text = sdText
            if (chordOrN.hasStyleInformation
                    and isinstance(chordOrN.style, style.NoteStyle)
                    and chordOrN.style.stemStyle is not None):
                self.setColor(mxStem, chordOrN.style.stemStyle)
                self.setPosition(mxStem, chordOrN.style.stemStyle)

        # end Stem

        # notehead
        self.dealWithNotehead(mxNote, n, chordParent)

        # TODO: notehead-text

        # beam
        if addChordTag is False:
            if isinstance(chordOrN, note.NotRest) and chordOrN.beams is not None:
                nBeamsList = self.beamsToXml(chordOrN.beams)
                for mxB in nBeamsList:
                    mxNote.append(mxB)

        mxNotationsList = self.noteToNotations(n, noteIndexInChord, chordParent)

        # add tuplets if it's a note or the first <note> of a chord.
        if addChordTag is False:
            for i, tup in enumerate(d.tuplets):
                tupTagList = self.tupletToXmlTuplet(tup, i + 1)
                mxNotationsList.extend(tupTagList)

        if mxNotationsList:
            mxNotations = SubElement(mxNote, 'notations')
            for mxN in mxNotationsList:
                mxNotations.append(mxN)

        # lyric
        if addChordTag is False:
            for lyricObj in chordOrN.lyrics:
                if lyricObj.text is None:
                    continue  # happens sometimes...
                mxLyric = self.lyricToXml(lyricObj)
                mxNote.append(mxLyric)
        # TODO: play
        self.xmlRoot.append(mxNote)
        return mxNote

    def setNoteInstrument(self,
                          n: note.NotRest,
                          mxNote: Element,
                          chordParent: chord.Chord | None):
        '''
        Insert <instrument> tags if necessary, that is, when there is more than one
        instrument anywhere in the same musicxml <part>.
        '''
        if self.parent is None or self.parent.instrumentStream is None:
            return

        if len(self.parent.instrumentStream) <= 1:
            return

        if n.isRest:
            return

        searchingObject: note.NotRest | chord.Chord = chordParent if chordParent else n
        closest_inst = searchingObject.getInstrument(returnDefault=True)

        instance_to_use = None
        inst: instrument.Instrument
        for inst in self.parent.instrumentStream:
            if inst.classSet == closest_inst.classSet:
                instance_to_use = inst
                break

        if instance_to_use is None:
            # exempt coverage, because this is only for safety/unreachable
            raise MusicXMLExportException(
                f'Could not find instrument instance for note {n} in instrumentStream'
            )  # pragma: no cover
        mxInstrument = SubElement(mxNote, 'instrument')
        if instance_to_use.instrumentId is not None:
            mxInstrument.set('id', instance_to_use.instrumentId)

    def restToXml(self, r: note.Rest):
        # noinspection PyShadowingNames
        '''
        Convert a Rest object to a <note> with a <rest> tag underneath it.

        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> r = note.Rest(quarterLength=2.0)

        Give the rest some context:

        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('4/4')
        >>> m.append(r)
        >>> mxNoteRest = MEX.restToXml(r)
        >>> MEX.dump(mxNoteRest)
        <note>
          <rest />
          <duration>20160</duration>
          <type>half</type>
        </note>

        Now it is a full measure:

        >>> m.timeSignature = meter.TimeSignature('2/4')
        >>> mxNoteRest = MEX.restToXml(r)
        >>> MEX.dump(mxNoteRest)
        <note>
          <rest measure="yes" />
          <duration>20160</duration>
        </note>

        Unless we specify that it should not be converted to a full measure:

        >>> r.fullMeasure = False
        >>> mxNoteRest = MEX.restToXml(r)
        >>> MEX.dump(mxNoteRest)
        <note>
          <rest />
          <duration>20160</duration>
          <type>half</type>
        </note>

        With True or "always" it will be converted to full measure even if
        it does not match:

        >>> m.timeSignature = meter.TimeSignature('4/4')
        >>> r.duration.dots = 1
        >>> r.fullMeasure = True
        >>> mxNoteRest = MEX.restToXml(r)
        >>> MEX.dump(mxNoteRest)
        <note>
          <rest measure="yes" />
          <duration>30240</duration>
        </note>


        Note that if a measure has paddingLeft/paddingRight (such as a pickup)
        then a fullMeasure duration might not match the TimeSignature duration.


        The display-step and display-octave are set from a Rest's stepShift:

        >>> r = note.Rest()
        >>> r.stepShift = 1
        >>> mxNoteRest = MEX.restToXml(r)
        >>> MEX.dump(mxNoteRest)
        <note>
          <rest>
            <display-step>C</display-step>
            <display-octave>5</display-octave>
          </rest>
          <duration>10080</duration>
          <type>quarter</type>
        </note>

        Clef context matters:

        >>> m = stream.Measure()
        >>> m.clef = clef.BassClef()
        >>> m.append(r)
        >>> mxNoteRest = MEX.restToXml(r)
        >>> MEX.dump(mxNoteRest)
        <note>
          <rest>
            <display-step>E</display-step>
            <display-octave>3</display-octave>
          </rest>
          <duration>10080</duration>
          <type>quarter</type>
        </note>
        '''
        mxNote = self.noteToXml(r)
        mxRestTag = mxNote.find('rest')
        if mxRestTag is None:
            raise MusicXMLExportException('Something went wrong -- converted rest w/o rest tag')

        if helpers.isFullMeasureRest(r):
            mxRestTag.set('measure', 'yes')
            mxType = mxNote.find('type')
            if mxType is not None:
                mxNote.remove(mxType)
            mxDots = mxNote.findall('dot')
            for mxDot in mxDots:
                mxNote.remove(mxDot)
            # should tuplet, etc. be removed? hard to think of a full measure with one.

        if r.stepShift != 0:
            mxDisplayStep = SubElement(mxRestTag, 'display-step')
            mxDisplayOctave = SubElement(mxRestTag, 'display-octave')
            currentClef: clef.PitchClef | None = r.getContextByClass(clef.PitchClef)
            if currentClef is None or not hasattr(currentClef, 'lowestLine'):
                currentClef = clef.TrebleClef()
                # this should not be common enough to
                # worry about the overhead
            if t.TYPE_CHECKING:
                assert isinstance(currentClef, clef.PitchClef)
            midLineDNN = currentClef.lowestLine + 4
            restObjectPseudoDNN = midLineDNN + r.stepShift
            tempPitch = pitch.Pitch()
            tempPitch.diatonicNoteNum = restObjectPseudoDNN
            mxDisplayStep.text = tempPitch.step
            mxDisplayOctave.text = str(tempPitch.octave)

        return mxNote

    def chordToXml(self, c: chord.ChordBase) -> list[Element]:
        # noinspection PyShadowingNames
        '''
        Returns a list of <note> tags, all but the first with a <chord/> tag on them.
        And appends them to self.xmlRoot

        Attributes of notes are merged from different locations: first from the
        duration objects, then from the pitch objects. Finally, GeneralNote
        attributes are added.

        >>> ch = chord.Chord()
        >>> ch.quarterLength = 2
        >>> b = pitch.Pitch('A-2')
        >>> c = pitch.Pitch('D3')
        >>> d = pitch.Pitch('E4')
        >>> e = [b, c, d]
        >>> ch.pitches = e

        >>> len(ch.pitches)
        3
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> len(MEX.xmlRoot)
        0
        >>> mxNoteList = MEX.chordToXml(ch)
        >>> len(mxNoteList)  # get three mxNotes
        3
        >>> len(MEX.xmlRoot)
        3

        >>> MEX.dump(mxNoteList[0])
        <note>
          <pitch>
            <step>A</step>
            <alter>-1</alter>
            <octave>2</octave>
          </pitch>
          <duration>20160</duration>
          <type>half</type>
          <accidental>flat</accidental>
        </note>

        >>> MEX.dump(mxNoteList[1])
        <note>
          <chord />
          <pitch>
            <step>D</step>
            <octave>3</octave>
          </pitch>
          <duration>20160</duration>
          <type>half</type>
        </note>

        >>> MEX.dump(mxNoteList[2])
        <note>
          <chord />
          <pitch>
            <step>E</step>
            <octave>4</octave>
          </pitch>
          <duration>20160</duration>
          <type>half</type>
        </note>


        Test that notehead and style translation works:

        >>> g = pitch.Pitch('g3')
        >>> h = note.Note('b4')
        >>> h.notehead = 'diamond'
        >>> h.style.color = 'gold'
        >>> h.style.absoluteX = 176
        >>> ch2 = chord.Chord([g, h])
        >>> ch2.quarterLength = 2.0
        >>> mxNoteList = MEX.chordToXml(ch2)
        >>> MEX.dump(mxNoteList[1])
        <note color="#FFD700" default-x="176">
          <chord />
          <pitch>
            <step>B</step>
            <octave>4</octave>
          </pitch>
          <duration>20160</duration>
          <type>half</type>
          <notehead color="#FFD700" parentheses="no">diamond</notehead>
        </note>

        And unpitched chord members:

        >>> perc = percussion.PercussionChord([note.Unpitched(), note.Unpitched()])
        >>> for n in MEX.chordToXml(perc):
        ...     MEX.dump(n)
        <note>
          <unpitched>
            <display-step>B</display-step>
            <display-octave>4</display-octave>
          </unpitched>
          <duration>10080</duration>
          <type>quarter</type>
        </note>
        <note>
          <chord />
          <unpitched>
            <display-step>B</display-step>
            <display-octave>4</display-octave>
          </unpitched>
          <duration>10080</duration>
          <type>quarter</type>
        </note>

        Test articulations of chords with fingerings. Superfluous fingerings will be ignored.

        >>> testChord = chord.Chord('E4 C5')
        >>> testChord.articulations = [articulations.Fingering(1),
        ...        articulations.Accent(), articulations.Fingering(5), articulations.Fingering(3)]
        >>> for n in MEX.chordToXml(testChord):
        ...     MEX.dump(n)
        <note>
          ...
          <notations>
            <articulations>
              <accent />
            </articulations>
            <technical>
              <fingering alternate="no" substitution="no">1</fingering>
            </technical>
          </notations>
        </note>
        <note>
          <chord />
          ...
          <notations>
            <technical>
              <fingering alternate="no" substitution="no">5</fingering>
            </technical>
          </notations>
        </note>
        '''
        mxNoteList = []
        if isinstance(c, chord.Chord):
            c.sortAscending()

        for i, n in enumerate(c):
            if 'Unpitched' in n.classSet:
                mxNoteList.append(self.unpitchedToXml(n, noteIndexInChord=i, chordParent=c))
            else:
                mxNoteList.append(self.noteToXml(n, noteIndexInChord=i, chordParent=c))
        return mxNoteList

    def durationXml(self, dur: duration.Duration):
        # noinspection PyShadowingNames
        '''
        Convert a duration.Duration object to a <duration> tag using self.currentDivisions

        >>> d = duration.Duration(1.5)
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> MEX.currentDivisions = 10
        >>> mxDuration = MEX.durationXml(d)
        >>> MEX.dump(mxDuration)
        <duration>15</duration>
        '''
        mxDuration = Element('duration')
        mxDuration.text = str(int(round(self.currentDivisions * dur.quarterLength)))
        return mxDuration

    def pitchToXml(self, p: pitch.Pitch):
        # noinspection PyShadowingNames
        '''
        Convert a :class:`~music21.pitch.Pitch` to xml.
        Does not create the <accidental> tag.

        >>> p = pitch.Pitch('D#5')
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxPitch = MEX.pitchToXml(p)
        >>> MEX.dump(mxPitch)
        <pitch>
          <step>D</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        '''
        mxPitch = Element('pitch')
        _setTagTextFromAttribute(p, mxPitch, 'step')
        if p.accidental is not None:
            mxAlter = SubElement(mxPitch, 'alter')
            mxAlter.text = str(common.numToIntOrFloat(p.accidental.alter))
        _setTagTextFromAttribute(p, mxPitch, 'octave', 'implicitOctave')
        return mxPitch

    def unpitchedToXml(self,
                       up: note.Unpitched,
                       noteIndexInChord: int = 0,
                       chordParent: chord.ChordBase | None = None) -> Element:
        # noinspection PyShadowingNames
        '''
        Convert an :class:`~music21.note.Unpitched` to a <note>
        with an <unpitched> subelement.

        >>> up = note.Unpitched(displayName='D5')
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxUnpitched = MEX.unpitchedToXml(up)
        >>> MEX.dump(mxUnpitched)
        <note>
          <unpitched>
            <display-step>D</display-step>
            <display-octave>5</display-octave>
          </unpitched>
          <duration>10080</duration>
          <type>quarter</type>
        </note>

        >>> graceUp = up.getGrace()
        >>> mxUnpitched = MEX.unpitchedToXml(graceUp)
        >>> MEX.dump(mxUnpitched)
        <note>
          <grace slash="yes" />
          <unpitched>
            <display-step>D</display-step>
            <display-octave>5</display-octave>
          </unpitched>
          <type>quarter</type>
        </note>
        '''
        mxNote = self.noteToXml(up, noteIndexInChord=noteIndexInChord, chordParent=chordParent)

        mxUnpitched = Element('unpitched')
        _setTagTextFromAttribute(up, mxUnpitched, 'display-step')
        _setTagTextFromAttribute(up, mxUnpitched, 'display-octave')

        helpers.insertBeforeElements(mxNote, mxUnpitched, tagList=['duration', 'type'])

        return mxNote

    def fretNoteToXml(self, fretNote) -> Element:
        '''
        Converts a FretNote Object to MusicXML readable format.

        Note that, although music21 is referring to FretNotes as FretNotes,
        musicxml refers to the
        them as frame notes. To convert between the two formats, 'Fret-Note'
        must be converted to
        'Frame-Note'

        >>> fn = tablature.FretNote(string=3, fret=1, fingering=2)
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> MEXFretNote = MEX.fretNoteToXml(fn)
        >>> MEX.dump(MEXFretNote)
        <frame-note>
            <string>3</string>
            <fret>1</fret>
            <fingering>2</fingering>
        </frame-note>

        Without fingering!

        >>> fn2 = tablature.FretNote(string=5, fret=2)
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> MEXOtherFretNote = MEX.fretNoteToXml(fn2)
        >>> MEX.dump(MEXOtherFretNote)
        <frame-note>
            <string>5</string>
            <fret>2</fret>
        </frame-note>
        '''
        mxFrameNote = Element('frame-note')
        _setTagTextFromAttribute(fretNote, mxFrameNote, 'string')
        _setTagTextFromAttribute(fretNote, mxFrameNote, 'fret')

        if fretNote.fingering is not None:
            _setTagTextFromAttribute(fretNote, mxFrameNote, 'fingering')

        return mxFrameNote

    def fretBoardToXml(self, fretBoard) -> Element | None:
        '''
        The ChordWithFretBoard Object combines chord symbols with FretNote objects.

        >>> myFretNote1 = tablature.FretNote(1, 2, 2)
        >>> myFretNote2 = tablature.FretNote(2, 3, 3)
        >>> myFretNote3 = tablature.FretNote(3, 2, 1)
        >>> guitarChord = tablature.ChordWithFretBoard('DM', numStrings=6,
        ...                    fretNotes=[myFretNote1, myFretNote2, myFretNote3])
        >>> guitarChord.tuning = tablature.GuitarFretBoard().tuning
        >>> guitarChord.getPitches()
        [None, None, None,
         <music21.pitch.Pitch A3>, <music21.pitch.Pitch D4>, <music21.pitch.Pitch F#4>]
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> MEXChordWithFret = MEX.fretBoardToXml(guitarChord)
        >>> MEX.dump(MEXChordWithFret)
        <frame>
            <frame-strings>6</frame-strings>
            <frame-frets>4</frame-frets>
            <frame-note>
                <string>3</string>
                <fret>2</fret>
                <fingering>1</fingering>
            </frame-note>
            <frame-note>
                <string>2</string>
                <fret>3</fret>
                <fingering>3</fingering>
            </frame-note>
            <frame-note>
                <string>1</string>
                <fret>2</fret>
                <fingering>2</fingering>
            </frame-note>
        </frame>
        '''
        if not fretBoard.fretNotes:
            return None

        # why isn't this the same as the function above? This seems a good deal simpler!
        mxFrame = Element('frame')
        mxFrameStrings = SubElement(mxFrame, 'frame-strings')
        mxFrameStrings.text = str(fretBoard.numStrings)
        mxFrameFrets = SubElement(mxFrame, 'frame-frets')
        mxFrameFrets.text = str(fretBoard.displayFrets)

        for thisFretNote in fretBoard.fretNotesLowestFirst():
            mxFretNote = self.fretNoteToXml(thisFretNote)
            mxFrame.append(mxFretNote)

        return mxFrame

    def chordWithFretBoardToXml(self, cwf: tablature.ChordWithFretBoard) -> Element:
        '''
        Deals with both chords and frets.
        Generate harmony and append xml to it.
        '''
        mxHarmony = self.chordSymbolToXml(cwf)
        if t.TYPE_CHECKING:
            # should not write out lists of Elements.
            assert isinstance(mxHarmony, Element)

        mxFrame = self.fretBoardToXml(cwf)

        if mxFrame is not None:
            mxHarmony.append(mxFrame)

        return mxHarmony

    def tupletToTimeModification(self, tup) -> Element:
        # noinspection PyShadowingNames
        '''
        >>> tup = duration.Tuplet(11, 8)
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxTimeMod = MEX.tupletToTimeModification(tup)
        >>> MEX.dump(mxTimeMod)
        <time-modification>
          <actual-notes>11</actual-notes>
          <normal-notes>8</normal-notes>
        </time-modification>

        >>> tup.setDurationType('eighth', dots=2)
        >>> mxTimeMod = MEX.tupletToTimeModification(tup)
        >>> MEX.dump(mxTimeMod)
        <time-modification>
          <actual-notes>11</actual-notes>
          <normal-notes>8</normal-notes>
          <normal-type>eighth</normal-type>
          <normal-dot />
          <normal-dot />
        </time-modification>

        '''
        mxTimeModification = Element('time-modification')
        _setTagTextFromAttribute(tup, mxTimeModification, 'actual-notes', 'numberNotesActual')
        _setTagTextFromAttribute(tup, mxTimeModification, 'normal-notes', 'numberNotesNormal')
        if tup.durationNormal is not None:
            mxNormalType = SubElement(mxTimeModification, 'normal-type')
            mxNormalType.text = typeToMusicXMLType(tup.durationNormal.type)
            if tup.durationNormal.dots > 0:
                for i in range(tup.durationNormal.dots):
                    SubElement(mxTimeModification, 'normal-dot')

        return mxTimeModification

    def dealWithNotehead(
        self,
        mxNote: Element,
        n: note.GeneralNote,
        chordParent: chord.Chord | None = None
    ) -> None:
        '''
        Determine if an <notehead> element needs to be added to this <note>
        element (mxNote) and if it does then get the <notehead> element from
        noteheadToXml and add it to mxNote.

        Complicated because the chordParent might have notehead
        set, which would affect every note along the way.

        Returns nothing.  The mxNote is modified in place.
        '''
        foundANotehead = False
        if (isinstance(n, note.NotRest)
            and (n.notehead != 'normal'
                 or n.noteheadParenthesis
                 or n.noteheadFill is not None
                 or (n.hasStyleInformation and n.style.color not in (None, '')))):
            n = t.cast(note.NotRest, n)
            foundANotehead = True
            mxNotehead = self.noteheadToXml(n)
            mxNote.append(mxNotehead)
        if foundANotehead is False and chordParent is not None:
            if (hasattr(chordParent, 'notehead')
                and (chordParent.notehead != 'normal'
                     or chordParent.noteheadParenthesis
                     or chordParent.noteheadFill is not None
                     or (chordParent.hasStyleInformation
                         and chordParent.style.color not in (None, '')))):
                mxNotehead = self.noteheadToXml(chordParent)
                mxNote.append(mxNotehead)

    def noteheadToXml(self, n: note.NotRest) -> Element:
        # noinspection PyShadowingNames
        '''
        Translate a music21 :class:`~music21.note.NotRest` object
        such as a Note, or Chord into a `<notehead>` tag.

        >>> n = note.Note('C#4')
        >>> n.notehead = 'diamond'
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxN = MEX.noteheadToXml(n)
        >>> MEX.dump(mxN)
        <notehead parentheses="no">diamond</notehead>

        >>> n1 = note.Note('c3')
        >>> n1.style.color = 'red'
        >>> n1.notehead = 'diamond'
        >>> n1.noteheadParenthesis = True
        >>> n1.noteheadFill = False
        >>> mxN = MEX.noteheadToXml(n1)
        >>> MEX.dump(mxN)
        <notehead color="#FF0000" filled="no" parentheses="yes">diamond</notehead>

        >>> n1 = note.Note('c3')
        >>> n1.style.color = 'red'
        >>> n1.notehead = 'diamond'
        >>> n1.noteheadParenthesis = True
        >>> n1.noteheadFill = False
        >>> mxN = MEX.noteheadToXml(n1)
        >>> MEX.dump(mxN)
        <notehead color="#FF0000" filled="no" parentheses="yes">diamond</notehead>
        '''
        mxNotehead = Element('notehead')
        nh = n.notehead
        if nh is None:
            nh = 'none'
        mxNotehead.text = nh
        setb = _setAttributeFromAttribute
        setb(n, mxNotehead, 'filled', 'noteheadFill', transform=xmlObjects.booleanToYesNo)
        setb(n, mxNotehead, 'parentheses', 'noteheadParenthesis',
             transform=xmlObjects.booleanToYesNo)
        # TODO: font
        if n.hasStyleInformation and n.style.color:
            color = normalizeColor(n.style.color)
            mxNotehead.set('color', color)
        return mxNotehead

    def arpeggioMarkToMxExpression(self, arpeggioMark, chordOrNote, noteIndexInChord):
        mxExpression = None
        if arpeggioMark.type == 'non-arpeggio':
            # <non-arpeggiate> goes on top and bottom note in chord
            if noteIndexInChord == 0:
                mxExpression = self.expressionToXml(arpeggioMark)
                mxExpression.set('type', 'bottom')
            elif noteIndexInChord == len(chordOrNote.notes) - 1:
                mxExpression = self.expressionToXml(arpeggioMark)
                mxExpression.set('type', 'top')
        else:
            # <arpeggiate> goes on every note in the chord
            mxExpression = self.expressionToXml(arpeggioMark)
        return mxExpression

    def ornamentToMxAccidentalMarks(self, ornamentObj: expressions.Ornament) -> list[Element]:
        mxAccidentalMarks: list[Element] = []

        if isinstance(ornamentObj, expressions.Turn):
            # 0, 1, or 2 accidental marks
            if (ornamentObj.upperOrnamentalPitch
                    and ornamentObj.upperOrnamentalPitch.accidental
                    and ornamentObj.upperOrnamentalPitch.accidental.displayStatus is True):
                mxAccidentalMarks.append(
                    self.accidentalToMxAccidentalMark(ornamentObj.upperOrnamentalPitch.accidental)
                )
                mxAccidentalMarks[-1].set('placement', 'above')
            if (ornamentObj.lowerOrnamentalPitch
                    and ornamentObj.lowerOrnamentalPitch.accidental
                    and ornamentObj.lowerOrnamentalPitch.accidental.displayStatus is True):
                mxAccidentalMarks.append(
                    self.accidentalToMxAccidentalMark(ornamentObj.lowerOrnamentalPitch.accidental)
                )
                mxAccidentalMarks[-1].set('placement', 'below')
        elif isinstance(ornamentObj, (expressions.GeneralMordent, expressions.Trill)):
            # 0 or 1 accidental marks
            if (ornamentObj.ornamentalPitch
                    and ornamentObj.ornamentalPitch.accidental
                    and ornamentObj.ornamentalPitch.accidental.displayStatus is True):
                mxAccidentalMarks.append(
                    self.accidentalToMxAccidentalMark(ornamentObj.ornamentalPitch.accidental)
                )
                if ornamentObj.direction == 'down':
                    mxAccidentalMarks[-1].set('placement', 'below')
                else:
                    mxAccidentalMarks[-1].set('placement', 'above')

        return mxAccidentalMarks

    def noteToNotations(
        self,
        n: note.GeneralNote,
        noteIndexInChord: int = 0,
        chordParent: chord.Chord | None = None
    ) -> list[Element]:
        '''
        Take information from .expressions,
        .articulations, and spanners to
        make the <notations> tag for a note.
        '''
        mxArticulations = None
        mxTechnicalMark = None
        mxOrnaments = None
        isSingleNoteOrFirstInChord = (noteIndexInChord == 0)

        notations: list[Element] = []

        chordOrNote = n
        if chordParent is not None:
            # get expressions from first note of chord
            chordOrNote = chordParent

        # apply all expressions apart from arpeggios only to the first note of a chord.
        for expObj in chordOrNote.expressions:
            mxExpression = None
            if isinstance(expObj, expressions.ArpeggioMark):
                mxExpression = self.arpeggioMarkToMxExpression(
                    expObj, chordOrNote, noteIndexInChord
                )
                if mxExpression is None:
                    # the ArpeggioMark is not applicable on this note.
                    continue
                notations.append(mxExpression)

            elif isSingleNoteOrFirstInChord:
                mxExpression = self.expressionToXml(expObj)
                if mxExpression is None:
                    # print('Could not convert expression: ', mxExpression)
                    # TODO: should not!
                    continue
                if isinstance(expObj, expressions.Ornament):
                    if mxOrnaments is None:
                        mxOrnaments = Element('ornaments')
                    mxOrnaments.append(mxExpression)

                    mxAccidMarks: list[Element] = (
                        self.ornamentToMxAccidentalMarks(expObj)
                    )
                    for mxAccidMark in mxAccidMarks:
                        mxOrnaments.append(mxAccidMark)
                    # print(mxExpression)
                else:
                    notations.append(mxExpression)

        # apply all articulations apart from fingerings and hammer-on/pull-off
        # only to first note of chord
        applicableArticulations: list[articulations.Articulation] = []
        fingeringNumber = 0
        for a in chordOrNote.articulations:
            if isinstance(a, articulations.Fingering):
                if fingeringNumber == noteIndexInChord:
                    applicableArticulations.append(a)
                fingeringNumber += 1
            elif isSingleNoteOrFirstInChord:
                # Ignore hammer-on/pull-off:
                # are written from their Spanner representation instead.
                # It's an anti-pattern to find spanners in the articulations
                # array, and the musicxml importer doesn't put them here,
                # but it's a potential point of user confusion, so we guard
                # against it here to avoid writing out superfluous <other-technical>
                if not isinstance(a, (articulations.HammerOn, articulations.PullOff)):
                    applicableArticulations.append(a)

        for artObj in applicableArticulations:
            if isinstance(artObj, articulations.Pizzicato):
                continue
            if isinstance(artObj, articulations.StringIndication) and artObj.number < 1:
                continue
            if isinstance(artObj, articulations.TechnicalIndication):
                if mxTechnicalMark is None:
                    mxTechnicalMark = Element('technical')

                mxTechnicalMark.append(self.articulationToXmlTechnical(artObj))
            else:
                if mxArticulations is None:
                    mxArticulations = Element('articulations')
                mxArticulations.append(self.articulationToXmlArticulation(artObj))

        # TODO: attrGroup: print-object (for individual notations)
        # TODO: editorial (hard! -- requires parsing again in order...)

        # <tied>
        # for ties get for each note of chord too...
        if n.tie is not None:
            tiedList = self.tieToXmlTied(n.tie)
            notations.extend(tiedList)

        # <tuplet> handled elsewhere, because it's on the overall duration on chord...

        if chordParent is not None:
            notations.extend(self.objectAttachedSpannersToNotations(chordParent, noteIndexInChord))
        else:
            notations.extend(self.objectAttachedSpannersToNotations(n, noteIndexInChord))
        # TODO: slur
        # TODO: glissando
        # TODO: slide

        if isSingleNoteOrFirstInChord and chordParent is not None:
            spannerTechnicals = self.objectAttachedSpannersToTechnicals(chordParent)
        elif chordParent is not None:
            spannerTechnicals = None
        else:
            spannerTechnicals = self.objectAttachedSpannersToTechnicals(n)
        if spannerTechnicals:
            if mxTechnicalMark is None:
                mxTechnicalMark = Element('technical')
            mxTechnicalMark.extend(spannerTechnicals)

        for x in (mxArticulations,
                  mxTechnicalMark,
                  mxOrnaments):
            if x:
                notations.append(x)

        # TODO: dynamics in notations
        # TODO: accidental-mark (Notations; we've done Ornaments)
        # TODO: other-notation
        return notations

    def tieToXmlTie(self, m21Tie: tie.Tie):
        # noinspection PyShadowingNames
        '''
        returns a list of ties from a Tie object.

        A 'continue' tie requires two <tie> tags to represent.

        >>> tieObj = tie.Tie('continue')
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> tieList = MEX.tieToXmlTie(tieObj)
        >>> for mxT in tieList:
        ...     MEX.dump(mxT)
        <tie type="stop" />
        <tie type="start" />
        '''
        mxTieList = []

        if m21Tie.type == 'continue':
            musicxmlTieType = 'stop'
        else:
            musicxmlTieType = m21Tie.type
        mxTie = Element('tie')
        mxTie.set('type', musicxmlTieType)
        mxTieList.append(mxTie)

        if m21Tie.type == 'continue':
            mxTie = Element('tie')
            mxTie.set('type', 'start')
            mxTieList.append(mxTie)

        return mxTieList

    def tieToXmlTied(self, m21Tie: tie.Tie):
        # noinspection PyShadowingNames
        '''
        In musicxml, a tie is represented in sound
        by the tie tag (near the pitch object), and
        the <tied> tag in notations.  This
        creates the <tied> tag.

        Returns a list since a music21 "continue" tie type needs two tags
        in musicxml.  List may be empty if tie.style == "hidden"

        >>> tieObj = tie.Tie('continue')
        >>> tieObj.id = 'tied1'

        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> tiedList = MEX.tieToXmlTied(tieObj)
        >>> for mxT in tiedList:
        ...     MEX.dump(mxT)
        <tied id="tied1" type="stop" />
        <tied type="start" />

        >>> tieObj.style = 'hidden'
        >>> tiedList = MEX.tieToXmlTied(tieObj)
        >>> len(tiedList)
        0
        '''
        if m21Tie.style == 'hidden':
            return []

        mxTiedList = []
        if m21Tie.type == 'continue':
            musicxmlTieType = 'stop'
        else:
            musicxmlTieType = m21Tie.type

        mxTied = Element('tied')
        _synchronizeIds(mxTied, m21Tie)

        mxTied.set('type', musicxmlTieType)
        mxTiedList.append(mxTied)

        if m21Tie.type == 'continue':
            mxTied = Element('tied')
            mxTied.set('type', 'start')
            mxTiedList.append(mxTied)

        # TODO: attr: number (distinguishing ties on enharmonics)
        if m21Tie.style != 'normal' and m21Tie.type != 'stop':
            mxTied.set('line-type', m21Tie.style)
            # wavy is not supported as a tie type.

        # Tie style needs to be dealt with after changes to Tie object...

        # TODO: attrGroup: dashed-formatting
        # TODO: attrGroup: position

        if m21Tie.placement is not None:
            mxTied.set('placement', m21Tie.placement)
            orientation = None
            if m21Tie.placement == 'above':
                orientation = 'over'
            elif m21Tie.placement == 'below':
                orientation = 'under'
            else:
                orientation = ''

            # MuseScore requires 'orientation' not placement
            # should be no need for separate orientation
            # https://forums.makemusic.com/viewtopic.php?f=12&t=2179&start=0
            if orientation:
                mxTied.set('orientation', orientation)

        # TODO: attrGroup: bezier
        # TODO: attrGroup: color

        return mxTiedList

    def tupletToXmlTuplet(self, tuplet, tupletIndex=1):
        '''
        In musicxml, a tuplet is represented by
        a timeModification and visually by the
        <notations><tuplet> tag.  This method
        creates the latter.

        Returns a list of them because a
        startStop type tuplet needs two tuplet
        brackets.

        TODO: make sure something happens if
            makeTupletBrackets is not set.

        >>> tup = duration.Tuplet(11, 8)
        >>> tup.type = 'start'
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxTup = MEX.tupletToXmlTuplet(tup)
        >>> len(mxTup)
        1
        >>> MEX.dump(mxTup[0])
        <tuplet bracket="yes" number="1" placement="above" type="start">
          <tuplet-actual>
            <tuplet-number>11</tuplet-number>
          </tuplet-actual>
          <tuplet-normal>
            <tuplet-number>8</tuplet-number>
          </tuplet-normal>
        </tuplet>

        >>> tup.tupletActualShow = 'both'
        >>> tup.tupletNormalShow = 'type'
        >>> mxTup = MEX.tupletToXmlTuplet(tup)
        >>> MEX.dump(mxTup[0])
        <tuplet bracket="yes" number="1" placement="above"
            show-number="actual" show-type="both" type="start">...</tuplet>
        '''
        if tuplet.type in (None, False, ''):
            return []

        if tuplet.type not in ('start', 'stop', 'startStop'):
            raise MusicXMLExportException(
                'Cannot create music XML from a tuplet of type ' + tuplet.type)

        if tuplet.type == 'startStop':  # need two musicxml
            localType = ['start', 'stop']
        else:
            localType = [tuplet.type]  # place in list

        retList = []

        for tupletType in localType:
            # might be multiple in case of startStop
            mxTuplet = Element('tuplet')
            mxTuplet.set('type', tupletType)
            mxTuplet.set('number', str(tupletIndex))
            # only provide other parameters if this tuplet is a start
            if tupletType == 'start':
                tBracket = tuplet.bracket
                if tBracket == 'slur':
                    tBracket = True
                mxTuplet.set('bracket',
                             xmlObjects.booleanToYesNo(tBracket))
                if tuplet.placement is not None:
                    mxTuplet.set('placement', tuplet.placement)
                tas = tuplet.tupletActualShow
                tns = tuplet.tupletNormalShow
                if tas is None:
                    mxTuplet.set('show-number', 'none')
                    # cannot show normal without actual
                elif tas in ('both', 'number') and tns in ('both', 'number'):
                    mxTuplet.set('show-number', 'both')
                elif tas in ('both', 'actual'):
                    mxTuplet.set('show-number', 'actual')

                if tas in ('both', 'type') and tns in ('both', 'type'):
                    mxTuplet.set('show-type', 'both')
                elif tas in ('both', 'type'):
                    mxTuplet.set('show-type', 'actual')

                if tuplet.bracket == 'slur':
                    mxTuplet.set('line-shape', 'curved')
                # TODO: attrGroup: position

                mxTupletActual = SubElement(mxTuplet, 'tuplet-actual')
                mxTupletNumber = SubElement(mxTupletActual, 'tuplet-number')
                mxTupletNumber.text = str(tuplet.numberNotesActual)
                if tuplet.durationActual is not None:
                    actualType = typeToMusicXMLType(tuplet.durationActual.type)
                    if actualType:
                        mxTupletType = SubElement(mxTupletActual, 'tuplet-type')
                        mxTupletType.text = actualType
                    for unused_counter in range(tuplet.durationActual.dots):
                        SubElement(mxTupletActual, 'tuplet-dot')

                mxTupletNormal = SubElement(mxTuplet, 'tuplet-normal')
                mxTupletNumber = SubElement(mxTupletNormal, 'tuplet-number')
                mxTupletNumber.text = str(tuplet.numberNotesNormal)
                if tuplet.durationNormal is not None:
                    normalType = typeToMusicXMLType(tuplet.durationNormal.type)
                    if normalType:
                        mxTupletType = SubElement(mxTupletNormal, 'tuplet-type')
                        mxTupletType.text = normalType
                    for unused_counter in range(tuplet.durationNormal.dots):
                        SubElement(mxTupletNormal, 'tuplet-dot')

            retList.append(mxTuplet)
        return retList

    def expressionToXml(self, expression: expressions.Expression) -> Element:
        '''
        Convert a music21 Expression (expression or ornament)
        to a musicxml tag;
        return None if no conversion is possible.

        Expressions apply only to the first note of chord.

        >>> invTurn = expressions.InvertedTurn()
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxExpression = MEX.expressionToXml(invTurn)
        >>> MEX.dump(mxExpression)
        <inverted-turn placement="above" />

        >>> invDelayedTurn = expressions.InvertedTurn(delay=1.)
        >>> invDelayedTurn.placement = 'below'
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxExpression = MEX.expressionToXml(invDelayedTurn)
        >>> MEX.dump(mxExpression)
        <delayed-inverted-turn placement="below" />

        Some special types...

        >>> f = expressions.Fermata()
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxExpression = MEX.expressionToXml(f)
        >>> MEX.dump(mxExpression)
        <fermata type="inverted" />
        >>> f.shape = 'angled'
        >>> mxExpression = MEX.expressionToXml(f)
        >>> MEX.dump(mxExpression)
        <fermata type="inverted">angled</fermata>

        >>> trem = expressions.Tremolo()
        >>> trem.numberOfMarks = 4
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxExpression = MEX.expressionToXml(trem)
        >>> MEX.dump(mxExpression)
        <tremolo type="single">4</tremolo>

        >>> arp = expressions.ArpeggioMark()
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxExpression = MEX.expressionToXml(arp)
        >>> MEX.dump(mxExpression)
        <arpeggiate />
        >>> arp.type = 'down'
        >>> mxExpression = MEX.expressionToXml(arp)
        >>> MEX.dump(mxExpression)
        <arpeggiate direction="down" />

        >>> nonArp = expressions.ArpeggioMark('non-arpeggio')
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxExpression = MEX.expressionToXml(nonArp)
        >>> MEX.dump(mxExpression)
        <non-arpeggiate />
        '''
        mx = None
        classes = expression.classes

        # ArpeggioMark maps to two different elements
        if isinstance(expression, expressions.ArpeggioMark):
            if expression.type == 'non-arpeggio':
                mx = Element('non-arpeggiate')
            else:
                mx = Element('arpeggiate')
                if expression.type != 'normal':
                    mx.set('direction', expression.type)

        # InvertedTurn/Turn map to two different elements each
        if isinstance(expression, expressions.Turn):
            if isinstance(expression, expressions.InvertedTurn):
                if expression.isDelayed:
                    mx = Element('delayed-inverted-turn')
                else:
                    mx = Element('inverted-turn')
            else:
                if expression.isDelayed:
                    mx = Element('delayed-turn')
                else:
                    mx = Element('turn')

        if mx is None:
            mapping = OrderedDict([
                ('Trill', 'trill-mark'),
                # TODO: vertical-turn
                ('InvertedMordent', 'inverted-mordent'),
                ('Mordent', 'mordent'),
                ('Shake', 'shake'),
                ('Schleifer', 'schleifer'),
                ('Tremolo', 'tremolo'),  # non-spanner
                # non-ornaments...
                ('Fermata', 'fermata'),
                # keep last...
                ('Ornament', 'other-ornament'),
            ])

            for k, v in mapping.items():
                if k in classes:
                    mx = Element(v)
                    break

        if mx is None:
            environLocal.printDebug(['no musicxml conversion for:', expression])
            return Element('other-ornament')

        self.setPrintStyle(mx, expression)
        # TODO: trill-sound
        if hasattr(expression, 'placement') and expression.placement is not None:
            mx.set('placement', expression.placement)
        if isinstance(expression, expressions.Fermata):
            mx.set('type', str(expression.type))
            if expression.shape in ('angled', 'square'):  # only valid shapes
                mx.text = expression.shape
            _synchronizeIds(mx, expression)

        if isinstance(expression, expressions.Tremolo):
            mx.set('type', 'single')
            mx.text = str(expression.numberOfMarks)

        return mx

    def articulationToXmlArticulation(
        self,
        articulationMark: articulations.Articulation
    ) -> Element:
        # noinspection PyShadowingNames
        '''
        Returns a class (mxArticulationMark) that represents the
        MusicXML structure of an articulation mark.

        >>> a = articulations.Accent()
        >>> a.placement = 'below'

        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxArticulationMark = MEX.articulationToXmlArticulation(a)
        >>> MEX.dump(mxArticulationMark)
        <accent placement="below" />

        >>> a = articulations.Staccatissimo()
        >>> a.placement = 'below'

        >>> mxArticulationMark = MEX.articulationToXmlArticulation(a)
        >>> MEX.dump(mxArticulationMark)
        <staccatissimo placement="below" />

        Articulations can have style attached to them:

        >>> a = articulations.Doit()
        >>> a.style.lineShape = 'curved'
        >>> a.style.lineType = 'dashed'
        >>> a.style.dashLength = 2
        >>> a.style.spaceLength = 1
        >>> a.style.absoluteX = 5
        >>> a.style.absoluteY = 2

        >>> mxArticulationMark = MEX.articulationToXmlArticulation(a)
        >>> MEX.dump(mxArticulationMark)
        <doit dash-length="2" default-x="5" default-y="2"
            line-shape="curved" line-type="dashed" space-length="1" />
        '''
        # these articulations have extra information
        musicXMLArticulationName = None
        for c in xmlObjects.ARTICULATION_MARKS_REV:
            if isinstance(articulationMark, c):
                musicXMLArticulationName = xmlObjects.ARTICULATION_MARKS_REV[c]
                break
        if musicXMLArticulationName is None:
            musicXMLArticulationName = 'other-articulation'
            # raise MusicXMLExportException('Cannot translate %s to musicxml' % articulationMark)
        mxArticulationMark = Element(musicXMLArticulationName)
        if articulationMark.placement is not None:
            mxArticulationMark.set('placement', articulationMark.placement)
        self.setPrintStyle(mxArticulationMark, articulationMark)
        if musicXMLArticulationName == 'strong-accent':
            if t.TYPE_CHECKING:
                assert isinstance(articulationMark, articulations.StrongAccent)
            mxArticulationMark.set('type', articulationMark.pointDirection)
        if musicXMLArticulationName in ('doit', 'falloff', 'plop', 'scoop'):
            self.setLineStyle(mxArticulationMark, articulationMark)
        if musicXMLArticulationName == 'breath-mark':
            if t.TYPE_CHECKING:
                assert isinstance(articulationMark, articulations.BreathMark)
            if articulationMark.symbol is not None:
                mxArticulationMark.text = articulationMark.symbol
        if (musicXMLArticulationName == 'other-articulation'
                and articulationMark.displayText is not None):
            mxArticulationMark.text = articulationMark.displayText
        # mxArticulations.append(mxArticulationMark)
        return mxArticulationMark

    def setLineStyle(self, mxObject, m21Object):
        '''
        Sets four additional elements for line elements, conforms to entity
        %line-shape, %line-type, %dashed-formatting (dash-length and space-length)
        '''
        musicXMLNames = ('line-shape', 'line-type', 'dash-length', 'space-length')
        m21Names = ('lineShape', 'lineType', 'dashLength', 'spaceLength')
        self.setStyleAttributes(mxObject, m21Object, musicXMLNames, m21Names)

    # def fretboardToXmlFrame(self, fretboardMark):
    #     '''
    #     >>> MEX = musicxml.m21ToXml.MeasureExporter()
    #     >>> fb = instruments.fretted.FretBoard(1, 2, 3)
    #
    #     configure it here...
    #
    #     >>> mxFret = MEX.fretboardToXmlTechnical(fb)
    #     >>> MEX.dump(mxFret)
    #     <frame>lots of stuff here</frame>
    #     '''
    #     pass

    def articulationToXmlTechnical(self, articulationMark: articulations.Articulation):
        # noinspection PyShadowingNames, SpellCheckingInspection
        '''
        Returns a tag that represents the
        MusicXML structure of an articulation mark that is primarily a TechnicalIndication.

        >>> MEX = musicxml.m21ToXml.MeasureExporter()

        >>> a = articulations.UpBow()
        >>> a.placement = 'below'

        >>> mxTechnicalMark = MEX.articulationToXmlTechnical(a)
        >>> MEX.dump(mxTechnicalMark)
        <up-bow placement="below" />


        >>> f = articulations.Fingering(4)
        >>> f.substitution = True
        >>> mxFingering = MEX.articulationToXmlTechnical(f)
        >>> MEX.dump(mxFingering)
        <fingering alternate="no" substitution="yes">4</fingering>

        Technical marks too specific to express in musicxml just get other-technical.

        >>> g = articulations.OrganIndication()
        >>> g.displayText = 'unda maris'
        >>> mxOther = MEX.articulationToXmlTechnical(g)
        >>> MEX.dump(mxOther)
        <other-technical>unda maris</other-technical>
        '''
        # these technical have extra information
        # TODO: hammer-on
        # TODO: pull-off
        # TODO: bend
        # TODO: hole
        # TODO: arrow
        musicXMLTechnicalName = None
        for c in xmlObjects.TECHNICAL_MARKS_REV:
            if isinstance(articulationMark, c):
                musicXMLTechnicalName = xmlObjects.TECHNICAL_MARKS_REV[c]
                break
        if musicXMLTechnicalName is None:
            musicXMLTechnicalName = 'other-technical'

        # TODO: support additional technical marks listed above
        if musicXMLTechnicalName in ('bend', 'hole', 'arrow'):
            musicXMLTechnicalName = 'other-technical'

        mxTechnicalMark = Element(musicXMLTechnicalName)
        if articulationMark.placement is not None:
            mxTechnicalMark.set('placement', articulationMark.placement)
        if musicXMLTechnicalName == 'fingering':
            if t.TYPE_CHECKING:
                assert isinstance(articulationMark, articulations.Fingering)
            mxTechnicalMark.text = str(articulationMark.fingerNumber)
            mxTechnicalMark.set('alternate',
                                xmlObjects.booleanToYesNo(articulationMark.alternate))
        if (musicXMLTechnicalName in ('handbell', 'other-technical')
                and articulationMark.displayText is not None):
            #     The handbell element represents notation for various
            #     techniques used in handbell and handchime music. Valid
            #     values are belltree [v 3.1], damp, echo, gyro, hand martellato,
            #     mallet lift, mallet table, martellato, martellato lift,
            #     muted martellato, pluck lift, and swing.
            mxTechnicalMark.text = articulationMark.displayText
        if musicXMLTechnicalName in ('heel', 'toe', 'fingering'):
            if t.TYPE_CHECKING:
                assert isinstance(articulationMark, (articulations.Fingering,
                                                     articulations.OrganIndication))
            mxTechnicalMark.set('substitution',
                                xmlObjects.booleanToYesNo(articulationMark.substitution))
        if musicXMLTechnicalName == 'string':
            if t.TYPE_CHECKING:
                assert isinstance(articulationMark, articulations.StringIndication)
            mxTechnicalMark.text = str(articulationMark.number)
        if musicXMLTechnicalName == 'fret':
            if t.TYPE_CHECKING:
                assert isinstance(articulationMark, articulations.FretIndication)
            mxTechnicalMark.text = str(articulationMark.number)

        # harmonic needs to check for whether it is artificial or natural, and
        # whether it is base-pitch, sounding-pitch, or touching-pitch
        if musicXMLTechnicalName == 'harmonic':
            if t.TYPE_CHECKING:
                assert isinstance(articulationMark, articulations.StringHarmonic)
            self.setHarmonic(mxTechnicalMark, articulationMark)

        if (musicXMLTechnicalName == 'other-technical'
                and articulationMark.displayText is not None):
            mxTechnicalMark.text = articulationMark.displayText

        self.setPrintStyle(mxTechnicalMark, articulationMark)
        # mxArticulations.append(mxArticulationMark)
        return mxTechnicalMark

    @staticmethod
    def setHarmonic(mxh: Element, harm: articulations.StringHarmonic) -> None:
        # noinspection PyShadowingNames
        '''
        Sets the artificial or natural tag (or no tag) and
        zero or one of base-pitch, sounding-pitch, touching-pitch

        Called from articulationToXmlTechnical

        >>> MEXClass = musicxml.m21ToXml.MeasureExporter

        >>> a = articulations.StringHarmonic()
        >>> a.harmonicType = 'artificial'
        >>> a.pitchType = 'sounding'

        >>> from xml.etree.ElementTree import Element
        >>> mxh = Element('harmonic')

        >>> MEXClass.setHarmonic(mxh, a)
        >>> MEXClass.dump(mxh)
        <harmonic>
          <artificial />
          <sounding-pitch />
        </harmonic>

        :class:`~music21.articulations.Harmonic` is probably too general for most uses,
        but if you use it, you get a harmonic tag with no details:

        >>> b = articulations.Harmonic()
        >>> mxh2 = Element('harmonic')
        >>> MEXClass.setHarmonic(mxh2, b)
        >>> MEXClass.dump(mxh2)
        <harmonic />
        '''
        if not hasattr(harm, 'harmonicType'):
            return

        if harm.harmonicType == 'artificial':
            SubElement(mxh, 'artificial')
        elif harm.harmonicType == 'natural':
            SubElement(mxh, 'natural')

        if harm.pitchType == 'base':
            SubElement(mxh, 'base-pitch')
        elif harm.pitchType == 'sounding':
            SubElement(mxh, 'sounding-pitch')
        elif harm.pitchType == 'touching':
            SubElement(mxh, 'touching-pitch')

    def noChordToXml(self, cs: harmony.NoChord) -> Element:
        '''
        Convert a NoChord object to an mxHarmony object (or a rest
        if .writeAsChord = True).

        Expected attributes of the NoChord object:

        >>> nc = harmony.NoChord()
        >>> nc.chordKind
        'none'

        >>> nc.chordKindStr
        'N.C.'

        Other values may not export:

        >>> nc.chordKindStr = ''
        >>> nc.write()
        Traceback (most recent call last):
        music21.musicxml.xmlObjects.MusicXMLExportException:
             In part (None), measure (1): NoChord object's chordKindStr must be non-empty

        >>> nc.chordKind = None
        >>> nc.write()
        Traceback (most recent call last):
        music21.musicxml.xmlObjects.MusicXMLExportException:
             In part (None), measure (1): NoChord object's chordKind must be 'none'

        To realize the NoChord as a rest:

        >>> nc2 = harmony.NoChord()
        >>> nc2.writeAsChord = True
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxNote = MEX.noChordToXml(nc2)
        >>> MEX.dump(mxNote)
        <note>
            <rest />
            <duration>10080</duration>
            <type>quarter</type>
        </note>
        '''
        if cs.writeAsChord is True:
            r = note.Rest(duration=cs.duration)
            return self.restToXml(r)

        mxHarmony = Element('harmony')
        _synchronizeIds(mxHarmony, cs)

        self.setPrintObject(mxHarmony, cs)

        self.setPrintStyle(mxHarmony, cs)

        mxRoot = SubElement(mxHarmony, 'root')
        mxStep = SubElement(mxRoot, 'root-step')
        mxStep.text = 'C'
        mxStep.set('text', '')

        mxKind = SubElement(mxHarmony, 'kind')
        cKind = cs.chordKind
        if cs.chordKind != 'none':
            raise MusicXMLExportException("NoChord object's chordKind must be 'none'")
        mxKind.text = str(cKind)
        if cs.chordKindStr in (None, ''):
            raise MusicXMLExportException("NoChord object's chordKindStr must be non-empty")
        mxKind.set('text', cs.chordKindStr)

        self.setOffsetOptional(cs, mxHarmony)
        self.setEditorial(mxHarmony, cs)

        self.xmlRoot.append(mxHarmony)
        return mxHarmony

    def romanNumeralToXml(self, rn: roman.RomanNumeral) -> Element | list[Element]:
        '''
        Convert a RomanNumeral object to either a chord (if .writeAsChord is True)
        or a Harmony XML Element.

        >>> rnI = roman.RomanNumeral('I', 'C')
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> MEX.currentDivisions = 10

        >>> listMxChords = MEX.romanNumeralToXml(rnI)
        >>> len(listMxChords)
        3
        >>> MEX.dump(listMxChords[1])
        <note>
          <chord />
          <pitch>
            <step>E</step>
            <octave>4</octave>
          </pitch>
          <duration>10</duration>
          <type>quarter</type>
        </note>

        If writeAsChord is False, we create a MusicXML 4.0 <numeral> tag.
        This does not work in the current version of MuseScore (which only
        supports MusicXML 3.1) but outputs decently well in Finale.

        >>> rnI.writeAsChord = False
        >>> mxHarmonyFromRN = MEX.romanNumeralToXml(rnI)
        >>> MEX.dump(mxHarmonyFromRN)
        <harmony>
          <numeral>
            <numeral-root text="I">1</numeral-root>
            <numeral-key print-object="no">
              <numeral-fifths>0</numeral-fifths>
              <numeral-mode>major</numeral-mode>
            </numeral-key>
          </numeral>
          <kind>major</kind>
        </harmony>

        >>> complexRn = roman.RomanNumeral('#iio65', 'e-')
        >>> complexRn.followsKeyChange = True
        >>> complexRn.writeAsChord = False
        >>> mxHarmonyFromRN = MEX.romanNumeralToXml(complexRn)
        >>> MEX.dump(mxHarmonyFromRN)
        <harmony>
          <numeral>
            <numeral-root text="#iio65">2</numeral-root>
            <numeral-alter location="left">1.0</numeral-alter>
            <numeral-key>
              <numeral-fifths>-6</numeral-fifths>
              <numeral-mode>minor</numeral-mode>
            </numeral-key>
          </numeral>
          <kind>diminished-seventh</kind>
          <inversion>1</inversion>
        </harmony>

        >>> maj6 = roman.RomanNumeral('VI7', 'd')
        >>> maj6.writeAsChord = False
        >>> mxHarmonyFromRN = MEX.romanNumeralToXml(maj6)
        >>> MEX.dump(mxHarmonyFromRN)
        <harmony>
          <numeral>
            <numeral-root text="VI7">6</numeral-root>
            <numeral-key print-object="no">
              <numeral-fifths>-1</numeral-fifths>
              <numeral-mode>natural minor</numeral-mode>
            </numeral-key>
          </numeral>
          <kind>major-seventh</kind>
        </harmony>

        >>> min6 = roman.RomanNumeral('vi', 'd')
        >>> min6.writeAsChord = False
        >>> mxHarmonyFromRN = MEX.romanNumeralToXml(min6)
        >>> mxHarmonyFromRN.find('.//numeral-mode').text
        'melodic minor'

        >>> dim7 = roman.RomanNumeral('viiø65', 'd')
        >>> dim7.writeAsChord = False
        >>> mxHarmonyFromRN = MEX.romanNumeralToXml(dim7)
        >>> mxHarmonyFromRN.find('.//numeral-mode').text
        'harmonic minor'
        >>> mxHarmonyFromRN.find('kind').text
        'half-diminished'

        >>> maj7 = roman.RomanNumeral('VII64', 'd')
        >>> maj7.writeAsChord = False
        >>> mxHarmonyFromRN = MEX.romanNumeralToXml(maj7)
        >>> mxHarmonyFromRN.find('.//numeral-mode').text
        'natural minor'
        '''
        if rn.writeAsChord is True:
            return self.chordToXml(rn)

        # because parsing "kind" is very hard, it's easier to
        # create a new chordSymbol in order to get the musicxml "kind"
        # a little slower than needs to be.
        cs = harmony.chordSymbolFromChord(rn)
        cs.offset = rn.offset  # needed for not getting an extra offset tag w/ forward.
        mxHarmony = self.chordSymbolToXml(cs, append=False)
        if t.TYPE_CHECKING:
            # will not get a list of Elements because writeAsChord is False
            assert isinstance(mxHarmony, Element)

        mxRoot = mxHarmony.find('root')
        if mxRoot is not None:
            # should never be None, but for type checking
            mxHarmony.remove(mxRoot)
        mxBass = mxHarmony.find('bass')
        if mxBass is not None:
            mxHarmony.remove(mxBass)

        # use v4 RomanNumerals
        mxNumeral = Element('numeral')
        mxNumeralRoot = SubElement(mxNumeral, 'numeral-root')
        mxNumeralRoot.set('text', rn.primaryFigure)
        mxNumeralRoot.text = str(rn.scaleDegree)
        if rn.frontAlterationAccidental:
            mxNumeralAlter = SubElement(mxNumeral, 'numeral-alter')
            # float is allowed
            mxNumeralAlter.text = str(rn.frontAlterationAccidental.alter)
            mxNumeralAlter.set('location', 'left')
        if rn.key:
            mxNumeralKey = SubElement(mxNumeral, 'numeral-key')
            if not rn.followsKeyChange:
                mxNumeralKey.set('print-object', 'no')
            mxNumeralFifths = SubElement(mxNumeralKey, 'numeral-fifths')
            mxNumeralFifths.text = str(rn.key.sharps)
            mxNumeralMode = SubElement(mxNumeralKey, 'numeral-mode')
            modeText = ''
            if rn.key.mode == 'major':
                modeText = 'major'
            elif rn.scaleDegree not in (6, 7):
                modeText = 'minor'
            elif rn.scaleDegree == 6:
                # simplest way to figure this out.
                if (rn.root().pitchClass - rn.key.tonic.pitchClass) % 12 == 8:
                    modeText = 'natural minor'
                else:
                    modeText = 'melodic minor'
            else:
                if (rn.root().pitchClass - rn.key.tonic.pitchClass) % 12 == 10:
                    modeText = 'natural minor'
                else:
                    modeText = 'harmonic minor'
            mxNumeralMode.text = modeText

        mxHarmony.insert(0, mxNumeral)
        self.xmlRoot.append(mxHarmony)
        return mxHarmony

    def chordSymbolToXml(self,
                         cs: harmony.ChordSymbol,
                         *,
                         append: bool = True) -> Element | list[Element]:
        # noinspection PyShadowingNames
        '''
        Convert a ChordSymbol object to either a chord (if .writeAsChord is True)
        or a Harmony XML Element.

        >>> cs = harmony.ChordSymbol()
        >>> cs.root('E-')
        >>> cs.bass('B-', allow_add=True)
        >>> cs.inversion(2, transposeOnSet=False)
        >>> cs.chordKind = 'major'
        >>> cs.chordKindStr = 'M'
        >>> cs
        <music21.harmony.ChordSymbol E-/B->

        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> MEX.currentDivisions = 10

        >>> mxHarmony = MEX.chordSymbolToXml(cs)
        >>> MEX.dump(mxHarmony)
        <harmony>
          <root>
            <root-step>E</root-step>
            <root-alter>-1</root-alter>
          </root>
          <kind text="M">major</kind>
          <inversion>2</inversion>
          <bass>
            <bass-step>B</bass-step>
            <bass-alter>-1</bass-alter>
          </bass>
        </harmony>


        Now give function...

        >>> cs.romanNumeral = 'I64'
        >>> mxHarmony = MEX.chordSymbolToXml(cs)
        >>> MEX.dump(mxHarmony)
        <harmony>
          <function>I64</function>
          <kind text="M">major</kind>
          <inversion>2</inversion>
          <bass>
            <bass-step>B</bass-step>
            <bass-alter>-1</bass-alter>
          </bass>
        </harmony>

        >>> hd = harmony.ChordStepModification()
        >>> hd.modType = 'alter'
        >>> hd.interval = -1
        >>> hd.degree = 3
        >>> cs.addChordStepModification(hd)

        >>> mxHarmony = MEX.chordSymbolToXml(cs)
        >>> MEX.dump(mxHarmony)
        <harmony>
          <function>I64</function>
          <kind text="M">major</kind>
          <inversion>2</inversion>
          <bass>
            <bass-step>B</bass-step>
            <bass-alter>-1</bass-alter>
          </bass>
          <degree>
            <degree-value>3</degree-value>
            <degree-alter>-1</degree-alter>
            <degree-type>alter</degree-type>
          </degree>
        </harmony>

        Test altered chords:

        >>> f = harmony.ChordSymbol('F sus add 9')
        >>> f
        <music21.harmony.ChordSymbol F sus add 9>
        >>> mxHarmony = MEX.chordSymbolToXml(f)
        >>> MEX.dump(mxHarmony)
        <harmony>
          <root>
            <root-step>F</root-step>
          </root>
          <kind>suspended-fourth</kind>
          <degree>
            <degree-value>9</degree-value>
            <degree-alter>0</degree-alter>
            <degree-type>add</degree-type>
          </degree>
        </harmony>

        MusicXML uses "dominant" for "dominant-seventh" so check aliases back...

        >>> dom7 = harmony.ChordSymbol('C7')
        >>> dom7.chordKind
        'dominant-seventh'
        >>> mxHarmony = MEX.chordSymbolToXml(dom7)
        >>> MEX.dump(mxHarmony)
        <harmony>
          <root>
            <root-step>C</root-step>
          </root>
          <kind>dominant</kind>
        </harmony>

        set writeAsChord to not get a symbol, but the notes.  Will return a list of notes.

        >>> dom7.writeAsChord = True
        >>> harmonyList = MEX.chordSymbolToXml(dom7)
        >>> len(harmonyList)
        4
        >>> MEX.dump(harmonyList[0])
        <note>
          <pitch>
            <step>C</step>
            <octave>3</octave>
          </pitch>
          <duration>10</duration>
          <type>quarter</type>
        </note>
        '''
        if cs.writeAsChord is True:
            return self.chordToXml(cs)

        mxHarmony = Element('harmony')
        _synchronizeIds(mxHarmony, cs)

        self.setPrintObject(mxHarmony, cs)
        # TODO: attr: print-frame
        # TODO: attrGroup: placement

        self.setPrintStyle(mxHarmony, cs)

        csRoot = cs.root()
        csBass = cs.bass(find=False)
        # TODO: do not look at ._attributes...
        if cs._roman is not None:
            mxFunction = SubElement(mxHarmony, 'function')
            mxFunction.text = cs.romanNumeral.figure
        elif csRoot is not None:
            mxRoot = SubElement(mxHarmony, 'root')
            mxStep = SubElement(mxRoot, 'root-step')
            mxStep.text = str(csRoot.step)
            # not a todo, text attribute; use element.
            # TODO: attrGroup: print-style

            if csRoot.accidental is not None:
                mxAlter = SubElement(mxRoot, 'root-alter')
                mxAlter.text = str(common.numToIntOrFloat(csRoot.accidental.alter))
                # TODO: attrGroup: print-object (why here)??
                # TODO: attrGroup: print-style
                # TODO: attr: location (left, right)
        else:
            environLocal.printDebug(['need either a root or a _roman to show'])
            return mxHarmony

        mxKind = SubElement(mxHarmony, 'kind')
        cKind = cs.chordKind or 'none'
        for xmlAlias in harmony.CHORD_ALIASES:
            if harmony.CHORD_ALIASES[xmlAlias] == cKind:
                cKind = xmlAlias

        mxKind.text = str(cKind)
        if cs.chordKindStr not in (None, ''):
            mxKind.set('text', cs.chordKindStr)
        # TODO: attr: use-symbols
        # TODO: attr: stack-degrees
        # TODO: attr: parentheses-degrees
        # TODO: attr: bracket-degrees
        # TODO: attrGroup: print-style
        # TODO: attrGroup: halign
        # TODO: attrGroup: valign
        csInv = cs.inversion()
        if csInv not in (None, 0):
            mxInversion = SubElement(mxHarmony, 'inversion')
            mxInversion.text = str(csInv)

        if csBass is not None and (csRoot is None or csRoot.name != csBass.name):
            # TODO.. reuse above from Root...
            mxBass = SubElement(mxHarmony, 'bass')
            mxStep = SubElement(mxBass, 'bass-step')
            mxStep.text = str(csBass.step)
            # not a todo, text attribute; use element.
            # TODO: attrGroup: print-style

            if csBass.accidental is not None:
                mxAlter = SubElement(mxBass, 'bass-alter')
                mxAlter.text = str(common.numToIntOrFloat(csBass.accidental.alter))
                # TODO: attrGroup: print-object (why here)??
                # TODO: attrGroup: print-style
                # TODO: attr: location (left, right)

        csm = cs.getChordStepModifications()
        for hd in csm:
            mxDegree = SubElement(mxHarmony, 'degree')
            # types should be compatible
            # TODO: print-object
            mxDegreeValue = SubElement(mxDegree, 'degree-value')
            mxDegreeValue.text = str(hd.degree)
            mxDegreeAlter = SubElement(mxDegree, 'degree-alter')
            # will return -1 for '-a1'
            mxDegreeAlter.text = str(hd.interval.chromatic.directed) if hd.interval else '0'
            # TODO: attrGroup: print-style
            # TODO: attr: plus-minus (yes, no)
            mxDegreeType = SubElement(mxDegree, 'degree-type')
            mxDegreeType.text = str(hd.modType)
            # TODO: attr: text -- alternate display
            # TODO: attrGroup: print-style

        # TODO: frame -- fretboard
        self.setOffsetOptional(cs, mxHarmony)
        self.setEditorial(mxHarmony, cs)
        # staff: see joinPartStaffs()

        if append:
            self.xmlRoot.append(mxHarmony)
        return mxHarmony

    def setOffsetOptional(self,
                          m21Obj: base.Music21Object,
                          mxObj: Element | None = None,
                          *,
                          setSound: bool = True
                          ) -> Element | None:
        '''
        If this object has an offset different from self.offsetInMeasure,
        then create and return an offset Element.

        If mxObj is not None then the offset element will be appended to it.
        '''
        if m21Obj.offset == self.offsetInMeasure:
            return None
        offsetDifferenceInQl = m21Obj.offset - self.offsetInMeasure
        offsetDifferenceInDivisions = int(offsetDifferenceInQl * self.currentDivisions)
        if mxObj is not None:
            mxOffset = SubElement(mxObj, 'offset')
        else:
            mxOffset = Element('offset')
        mxOffset.text = str(offsetDifferenceInDivisions)
        if setSound:
            mxOffset.set('sound', 'yes')  # always affects sound at location in measure.
        return mxOffset

    def placeInDirection(self,
                         mxObj: Element,
                         m21Obj: base.Music21Object | None = None,
                         *,
                         setSound: bool = True
                         ) -> Element:
        '''
        Places the mxObj <element> inside <direction><direction-type>
        and sets <offset> if needed.

        * Changed in v8: added `setSound` keyword (see :meth:`setOffsetOptional`).
        '''
        mxDirection = Element('direction')
        mxDirectionType = SubElement(mxDirection, 'direction-type')
        mxDirectionType.append(mxObj)
        if m21Obj is not None:
            if hasattr(m21Obj, 'placement') and m21Obj.placement is not None:
                mxDirection.set('placement', m21Obj.placement)
            self.setOffsetOptional(m21Obj, mxDirection, setSound=setSound)

        return mxDirection

    def dynamicToXml(self, d: dynamics.Dynamic) -> Element:
        # noinspection PyShadowingNames
        '''
        return a nested tag:
        <direction><direction-type><dynamic><ff>
        or whatever...

        >>> ppp = dynamics.Dynamic('ppp')
        >>> print('%.2f' % ppp.volumeScalar)
        0.15
        >>> ppp.style.relativeY = -10

        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxDirection = MEX.dynamicToXml(ppp)
        >>> MEX.dump(mxDirection)
        <direction>
          <direction-type>
            <dynamics default-x="-36" default-y="-80" relative-y="-10">
              <ppp />
            </dynamics>
          </direction-type>
          <sound dynamics="19" />
        </direction>

        appends to score.

        Now with offset not zero.

        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> ppp.offset = 1.0
        >>> mxDirection = MEX.dynamicToXml(ppp)
        >>> MEX.dump(mxDirection)
        <direction>
          <direction-type>
            <dynamics default-x="-36" default-y="-80" relative-y="-10">
              <ppp />
            </dynamics>
          </direction-type>
          <offset sound="yes">10080</offset>
          <sound dynamics="19" />
        </direction>

        '''
        mxDynamics = Element('dynamics')
        _synchronizeIds(mxDynamics, d)
        if d.value in xmlObjects.DYNAMIC_MARKS:
            mxThisDynamic = SubElement(mxDynamics, d.value)
        else:
            mxThisDynamic = SubElement(mxDynamics, 'other-dynamics')
            mxThisDynamic.text = str(d.value)
            # TODO: smufl

        self.setPrintStyleAlign(mxDynamics, d)
        # TODO: attrGroup: placement (but done for direction, so okay...
        # TODO: attrGroup: text-decoration
        # TODO: attrGroup: enclosure

        mxDirection = self.placeInDirection(mxDynamics, d)  # also handles offset
        # direction todos
        self.setEditorial(mxDirection, d)
        # TODO: voice
        # staff: see joinPartStaffs()

        # sound
        vS = d.volumeScalar
        if vS is not None:
            mxSound = SubElement(mxDirection, 'sound')
            # do not set id, since the element is the same in music21.

            dynamicVolume = int(vS * 127)
            mxSound.set('dynamics', str(dynamicVolume))

        self.xmlRoot.append(mxDirection)
        return mxDirection

    def segnoToXml(self, segno: repeat.Segno) -> Element:
        '''
        returns a segno inside a direction-type inside a direction.

        appends to score

        >>> s = repeat.Segno()
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxSegnoDir = MEX.segnoToXml(s)
        >>> MEX.dump(mxSegnoDir)
        <direction>
          <direction-type>
            <segno default-y="20" />
          </direction-type>
        </direction>

        >>> s.id = 'segno0'
        >>> s.style.alignHorizontal = 'left'
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxSegnoDir = MEX.segnoToXml(s)
        >>> MEX.dump(mxSegnoDir)
        <direction>
          <direction-type>
            <segno default-y="20" halign="left" id="segno0" />
          </direction-type>
        </direction>

        '''
        mxSegno = Element('segno')
        _synchronizeIds(mxSegno, segno)
        self.setPrintStyleAlign(mxSegno, segno)
        mxDirection = self.placeInDirection(mxSegno, segno)
        self.xmlRoot.append(mxDirection)
        return mxDirection

    def codaToXml(self, coda: repeat.Coda) -> Element:
        '''
        returns a coda inside a direction-type inside a direction IF coda.useSymbol is
        True; otherwise returns a textExpression...

        appends to score

        >>> c = repeat.Coda()
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxCodaDir = MEX.codaToXml(c)
        >>> MEX.dump(mxCodaDir)
        <direction>
          <direction-type>
            <coda default-y="20" />
          </direction-type>
        </direction>

        turn coda.useSymbol to False to get a text expression instead

        >>> c.useSymbol = False
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxCodaText = MEX.codaToXml(c)
        >>> MEX.dump(mxCodaText)
        <direction>
          <direction-type>
            <words default-y="20" enclosure="none"
                justify="center">Coda</words>
          </direction-type>
        </direction>
        '''
        if coda.useSymbol:
            mxCoda = Element('coda')
            _synchronizeIds(mxCoda, coda)
            self.setPrintStyleAlign(mxCoda, coda)
            mxDirection = self.placeInDirection(mxCoda, coda)
            self.xmlRoot.append(mxDirection)
            return mxDirection
        else:
            codaTe = coda.getTextExpression()
            codaTe.offset = coda.offset
            return self.textExpressionToXml(codaTe)

    def tempoIndicationToXml(self, ti: tempo.TempoIndication) -> Element:
        # noinspection PyShadowingNames
        '''
        returns a <direction> tag for a single tempo indication.

        note that TWO direction tags may be added to xmlroot, the second one
        as a textExpression.... but only the first will be returned.

        >>> mm = tempo.MetronomeMark('slow', 40, note.Note(type='half'))
        >>> mm.style.justify = 'left'

        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxDirection = MEX.tempoIndicationToXml(mm)
        >>> MEX.dump(mxDirection)
        <direction>
          <direction-type>
            <metronome parentheses="no">
              <beat-unit>half</beat-unit>
              <per-minute>40</per-minute>
            </metronome>
          </direction-type>
          <sound tempo="80" />
        </direction>

        In this case, two directions were added to xmlRoot.  Here is the other one:

        >>> MEX.dump(MEX.xmlRoot.findall('direction')[1])
        <direction>
          <direction-type>
            <words default-y="45" enclosure="none" font-weight="bold"
                justify="left">slow</words>
          </direction-type>
        </direction>


        >>> mm = tempo.MetronomeMark('slow', 40, duration.Duration(quarterLength=1.5))
        >>> mxDirection = MEX.tempoIndicationToXml(mm)
        >>> MEX.dump(mxDirection)
        <direction>
          <direction-type>
            <metronome parentheses="no">
              <beat-unit>quarter</beat-unit>
              <beat-unit-dot />
              <per-minute>40</per-minute>
            </metronome>
          </direction-type>
          <sound tempo="60" />
        </direction>

        >>> mmod1 = tempo.MetricModulation()
        >>> mmod1.oldReferent = 0.75  # quarterLength
        >>> mmod1.newReferent = 'quarter'  # type
        >>> mxDirection = MEX.tempoIndicationToXml(mmod1)
        >>> MEX.dump(mxDirection)
        <direction>
          <direction-type>
            <metronome parentheses="no">
              <beat-unit>eighth</beat-unit>
              <beat-unit-dot />
              <beat-unit>quarter</beat-unit>
            </metronome>
          </direction-type>
        </direction>

        >>> mmod1.newReferent = 'longa'  # music21 type w/ different musicxml name...
        >>> mxDirection = MEX.tempoIndicationToXml(mmod1)
        >>> MEX.dump(mxDirection)
        <direction>
          <direction-type>
            <metronome parentheses="no">
              <beat-unit>eighth</beat-unit>
              <beat-unit-dot />
              <beat-unit>long</beat-unit>
            </metronome>
          </direction-type>
        </direction>

        This is the case where only a sound tag is added and no metronome mark

        >>> mm = tempo.MetronomeMark()
        >>> mm.numberSounding = 60

        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxDirection = MEX.tempoIndicationToXml(mm)
        >>> MEX.dump(mxDirection)
        <direction>
          <direction-type>
            <words />
          </direction-type>
          <sound tempo="60" />
        </direction>

        This is the case of a TempoText.

        >>> tt = tempo.TempoText('Andante')
        >>> mxDirection = MEX.tempoIndicationToXml(tt)
        >>> MEX.dump(mxDirection)
        <direction>
          <direction-type>
            <words default-y="45" enclosure="none" font-weight="bold">Andante</words>
          </direction-type>
        </direction>

        '''
        # if writing just a sound tag, place an empty words tag in a
        # direction type and then follow with sound declaration
        # storing lists to accommodate metric modulations
        durs = []  # duration objects
        numbers = []  # tempi
        hideNumericalMetro = False  # if numbers implicit, hide metronome numbers
        hideNumber = []  # hide the number after equal, e.g., quarter=120, hide 120
        # store the last value necessary as a sounding tag in bpm
        soundingQuarterBPM = 0.0  # use 0.0 as False/None/etc. since unplayable.

        # handle TempoText simply by exporting its textExpression.
        if isinstance(ti, tempo.TempoText):
            te = ti.getTextExpression()
            te.offset = ti.offset
            return self.textExpressionToXml(te)

        if isinstance(ti, tempo.MetronomeMark):
            # will not show a number of implicit
            if ti.numberImplicit or ti.number is None:
                # environLocal.printDebug(['found numberImplicit', ti.numberImplicit])
                hideNumericalMetro = True
            else:
                durs.append(ti.referent)
                numbers.append(ti.number)
                hideNumber.append(False)
            # determine number sounding; first, get from numberSounding, then
            # number (if implicit, that is fine); get in terms of quarter bpm
            soundingQuarterBPM = ti.getQuarterBPM() or 0.0

        elif isinstance(ti, tempo.MetricModulation):
            # may need to reverse order if classical style or otherwise
            # may want to show first number
            hideNumericalMetro = False  # must show for metric modulation
            for sub in (ti.oldMetronome, ti.newMetronome):
                hideNumber.append(True)  # cannot show numbers in a metric modulation
                durs.append(sub.referent)
                numbers.append(sub.number)
            # soundingQuarterBPM should be obtained from the last MetronomeMark
            soundingQuarterBPM = ti.newMetronome.getQuarterBPM() or 0.0

            # environLocal.printDebug(['found metric modulation', ti, durs, numbers])

        mxMetro = Element('metronome')
        _synchronizeIds(mxMetro, ti)

        for i, d in enumerate(durs):
            # charData of BeatUnit is the type string
            mxSub = Element('beat-unit')
            mxSub.text = typeToMusicXMLType(d.type)
            mxMetro.append(mxSub)
            for unused_dotCounter in range(d.dots):
                mxMetro.append(Element('beat-unit-dot'))
            if numbers and not hideNumber[i]:
                mxPerMinute = SubElement(mxMetro, 'per-minute')  # TODO: font.
                mxPerMinute.text = str(common.numToIntOrFloat(numbers[0]))

        if hasattr(ti, 'parentheses') and ti.parentheses:
            mxMetro.set('parentheses', 'yes')  # only attribute
        else:
            mxMetro.set('parentheses', 'no')  # only attribute

        # if writing just a sound tag, place an empty words tag in a
        # direction type and then follow with sound declaration
        if durs:
            mxDirection = self.placeInDirection(mxMetro, ti)
        else:
            mxWords = Element('words')
            _synchronizeIds(mxWords, ti)

            mxDirection = self.placeInDirection(mxWords, ti)

        if soundingQuarterBPM:
            mxSound = SubElement(mxDirection, 'sound')
            mxSound.set('tempo', str(common.numToIntOrFloat(soundingQuarterBPM)))

        if hideNumericalMetro is not None:
            self.xmlRoot.append(mxDirection)

        if isinstance(ti, tempo.MetronomeMark):
            if ti.getTextExpression(returnImplicit=False) is not None:
                te = ti.getTextExpression(returnImplicit=False)
                te.offset = ti.offset
                unused_mxDirectionText = self.textExpressionToXml(te)

        return mxDirection

    def rehearsalMarkToXml(self, rm: expressions.RehearsalMark) -> Element:
        # noinspection PyShadowingNames
        '''
        Convert a RehearsalMark object to a MusicXML <direction> tag with a <rehearsal> tag
        inside it.

        >>> rm = expressions.RehearsalMark('II')
        >>> rm.style.enclosure = 'square'
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxRehearsal = MEX.rehearsalMarkToXml(rm)
        >>> MEX.dump(mxRehearsal)
        <direction>
          <direction-type>
            <rehearsal enclosure="square" halign="center" valign="middle">II</rehearsal>
            </direction-type>
          </direction>
        '''
        mxRehearsal = Element('rehearsal')
        self.setTextFormatting(mxRehearsal, rm)
        mxRehearsal.text = str(rm.content)
        mxDirection = self.placeInDirection(mxRehearsal, rm)
        self.setStyleAttributes(mxDirection, rm, 'placement')

        self.xmlRoot.append(mxDirection)
        return mxDirection

    def textExpressionToXml(
        self,
        teOrRe: expressions.TextExpression | repeat.RepeatExpression
    ) -> Element:
        '''
        Convert a TextExpression or RepeatExpression to a MusicXML mxDirection type.
        returns a musicxml.mxObjects.Direction object
        '''
        # TODO: if expression is empty do not set an empty <words/> tag.
        mxWords = Element('words')
        te: expressions.TextExpression
        if isinstance(teOrRe, expressions.TextExpression):  # TextExpression
            te = teOrRe
            mxWords.text = str(te.content)
        elif isinstance(teOrRe, repeat.RepeatExpression):  # RepeatExpression
            te = teOrRe.getTextExpression()
            te.offset = teOrRe.offset
            mxWords.text = str(te.content)
        else:
            raise MusicXMLExportException('teOrRe must be a TextExpression or RepeatExpression')

        self.setTextFormatting(mxWords, te)

        mxDirection = self.placeInDirection(mxWords, te, setSound=False)  # handles offset
        self.xmlRoot.append(mxDirection)
        return mxDirection

    def wrapObjectInAttributes(
        self,
        objectToWrap: base.Music21Object,
        methodToMx: t.Callable[[t.Any], Element],
    ) -> Element | None:
        # noinspection PyShadowingNames
        '''
        given a Clef, KeySignature, or TimeSignature which is in .elements and not m.clef,
        etc. insert it in self.xmlRoot as
        part of the current mxAttributes using methodToMx as a wrapper function.

        (or insert into a new mxAttributes if Clef/KeySignature/etc. is not at the beginning
        of the measure and not at the same point as an existing mxAttributes)

        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> MEX.offsetInMeasure = 3.0
        >>> cl = clef.BassClef()
        >>> methodToMx = MEX.clefToXml
        >>> mxAttributes = MEX.wrapObjectInAttributes(cl, methodToMx)
        >>> MEX.dump(mxAttributes)
        <attributes>
          <clef>
            <sign>F</sign>
            <line>4</line>
          </clef>
        </attributes>

        Also puts it in MEX.xmlRoot.

        If offsetInMeasure is 0.0 then nothing is done or returned:

        >>> MEX.offsetInMeasure = 0.0
        >>> nothing = MEX.wrapObjectInAttributes(cl, methodToMx)
        >>> nothing is None
        True
        '''
        if self.offsetInMeasure == 0.0:
            return None

        mxAttributes = Element('attributes')

        mxObj = methodToMx(objectToWrap)
        mxAttributes.append(mxObj)

        self.xmlRoot.append(mxAttributes)

        return mxAttributes

    def _matchesPreviousPartStaffInGroup(
        self,
        obj: base.Music21Object,
        attr: str = 'keySignature',
        comparison: str = '__eq__'
    ) -> bool:
        '''
        If this measure is part of a subsequent PartStaff in a joinable staff
        group (e.g. the left hand of a keyboard part), then look up the
        corresponding measure by number in the previous PartStaff, retrieve
        the `attr` value there, and compare it to `obj` by `comparison`.
        '''
        if self.parent is None:  # pragma: no cover
            return False
        if self.parent.previousPartStaffInGroup is None:
            return False
        # Not a foolproof measure lookup: see more robust measure
        # matching algorithm in PartStaffExporterMixin.processSubsequentPartStaff().
        # getElementsByOffset() would not be a perfect solution either,
        # see https://groups.google.com/g/music21list/c/ObNOanMQjJU/m/2LMPz5NAAwAJ
        if obj.measureNumber is None:  # pragma: no cover
            return False
        maybe_measure = self.parent.previousPartStaffInGroup.measure(obj.measureNumber)
        if maybe_measure is None:
            return False
        comparison_wrapper = getattr(obj, comparison)
        return comparison_wrapper(getattr(maybe_measure, attr))

    # -----------------------------
    # note helpers...

    def lyricToXml(self, ly: note.Lyric):
        '''
        Translate a music21 :class:`~music21.note.Lyric` object
        to a <lyric> tag.

        Lyrics have attribute list %justify, %position, %placement, %color, %print-object
        '''
        mxLyric = Element('lyric')
        if not ly.isComposite:
            _setTagTextFromAttribute(ly, mxLyric, 'syllabic')
            _setTagTextFromAttribute(ly, mxLyric, 'text', forceEmpty=True)
        else:
            # composite must have at least one component
            if t.TYPE_CHECKING:
                assert ly.components is not None

            for i, component in enumerate(ly.components):
                if component.syllabic == 'composite':
                    # skip doubly nested lyrics -- why, oh, why would you do that!
                    continue
                if i >= 1:
                    mxElision = SubElement(mxLyric, 'elision')
                    if component.elisionBefore:
                        mxElision.text = component.elisionBefore
                _setTagTextFromAttribute(component, mxLyric, 'syllabic')
                _setTagTextFromAttribute(component, mxLyric, 'text', forceEmpty=True)

        # TODO: extend
        # TODO: laughing
        # TODO: humming
        # TODO: end-line
        # TODO: end-paragraph
        # TODO: editorial
        if ly.identifier is not None:
            mxLyric.set('name', str(ly.identifier))

        if ly.number is not None:
            mxLyric.set('number', str(ly.number))
        elif ly.identifier is not None:
            mxLyric.set('number', str(ly.identifier))

        self.setStyleAttributes(mxLyric, ly,
                                ('justify', 'placement'),
                                ('justify', 'placement'))
        self.setPrintObject(mxLyric, ly)

        self.setColor(mxLyric, ly)
        self.setPosition(mxLyric, ly)
        return mxLyric

    def beamsToXml(self, beams):
        # noinspection PyShadowingNames
        '''
        Returns a list of <beam> tags
        from a :class:`~music21.beam.Beams` object


        >>> a = beam.Beams()
        >>> a.fill(2, type='start')

        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxBeamList = MEX.beamsToXml(a)
        >>> len(mxBeamList)
        2
        >>> for b in mxBeamList:
        ...     MEX.dump(b)
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        '''
        mxBeamList = []
        for beamObj in beams.beamsList:
            mxBeamList.append(self.beamToXml(beamObj))
        return mxBeamList

    def beamToXml(self, beamObject):
        '''
        Returns an ElementTree Element from a :class:`~music21.beam.Beam` object

        >>> a = beam.Beam()
        >>> a.type = 'start'
        >>> a.number = 1

        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> b = MEX.beamToXml(a)
        >>> b
        <Element 'beam' at 0x104f3a728>
        >>> MEX.dump(b)
        <beam number="1">begin</beam>

        >>> a.type = 'continue'
        >>> b = MEX.beamToXml(a)
        >>> MEX.dump(b)
        <beam number="1">continue</beam>

        >>> a.type = 'stop'
        >>> b = MEX.beamToXml(a)
        >>> MEX.dump(b)
        <beam number="1">end</beam>

        >>> a.type = 'partial'
        >>> a.direction = 'left'
        >>> b = MEX.beamToXml(a)
        >>> MEX.dump(b)
        <beam number="1">backward hook</beam>

        >>> a.direction = 'right'
        >>> a.id = 'beam1'
        >>> b = MEX.beamToXml(a)
        >>> MEX.dump(b)
        <beam id="beam1" number="1">forward hook</beam>

        >>> a.direction = None
        >>> b = MEX.beamToXml(a)
        Traceback (most recent call last):
        music21.musicxml.xmlObjects.MusicXMLExportException: partial beam defined
            without a proper direction set (set to None)

        >>> a.type = 'crazy'
        >>> b = MEX.beamToXml(a)
        Traceback (most recent call last):
        music21.musicxml.xmlObjects.MusicXMLExportException: unexpected beam type
            encountered (crazy)
        '''
        mxBeam = Element('beam')
        _synchronizeIds(mxBeam, beamObject)
        beamToType = {'start': 'begin',
                      'continue': 'continue',
                      'stop': 'end',
                      }
        if beamObject.type in beamToType:
            mxBeam.text = beamToType[beamObject.type]
        elif beamObject.type == 'partial':
            if beamObject.direction == 'left':
                mxBeam.text = 'backward hook'
            elif beamObject.direction == 'right':
                mxBeam.text = 'forward hook'
            else:
                raise MusicXMLExportException(
                    'partial beam defined without a proper direction set (set to %s)' %
                    beamObject.direction)
        else:
            raise MusicXMLExportException(
                f'unexpected beam type encountered ({beamObject.type})'
            )

        mxBeam.set('number', str(beamObject.number))
        # BeamObject has no .id -- fix?
        # _synchronizeIds(mxBeam, beamObject)

        # not to be done: repeater (deprecated)
        self.setColor(mxBeam, beamObject)
        # again, we pass the name 'fan' twice, so we don't have to run
        # hyphenToCamelCase on it.
        self.setStyleAttributes(mxBeam, beamObject, 'fan', 'fan')

        return mxBeam

    def setRightBarline(self):
        '''
        Calls self.setBarline for the right side if the measure has a .rightBarline set.
        '''
        m = self.stream
        if not hasattr(m, 'rightBarline'):
            return
        # rb = repeatBracket
        rbSpanners = self.rbSpanners
        rightBarline = self.stream.rightBarline
        if (rightBarline is None
                and (not rbSpanners or not rbSpanners[0].isLast(m))):
            return
        else:
            # rightBarline may be None
            self.setBarline(rightBarline, 'right')

    def setLeftBarline(self):
        '''
        Calls self.setBarline for the left side if the measure has a .leftBarline set.
        '''
        m = self.stream
        if not hasattr(m, 'leftBarline'):
            return
        # rb = repeatBracket
        rbSpanners = self.rbSpanners
        leftBarline = m.leftBarline
        if (leftBarline is None
                and (not rbSpanners or not rbSpanners[0].isFirst(m))):
            return
        else:
            # leftBarline may be None. that's okay
            self.setBarline(leftBarline, 'left')

    def setBarline(self, barline, position):
        '''
        sets either a left or right barline from a
        bar.Barline() object or bar.Repeat() object
        '''
        mxRepeat = None
        if barline is None:
            mxBarline = Element('barline')
        else:
            if isinstance(barline, bar.Repeat):
                mxBarline = Element('barline')
                mxRepeat = self.repeatToXml(barline)
            else:
                mxBarline = self.barlineToXml(barline)

        _synchronizeIds(mxBarline, barline)

        mxBarline.set('location', position)
        # TODO: editorial
        # TODO: wavy-line
        # TODO: segno
        # TODO: coda
        # TODO: fermata

        if self.rbSpanners:
            if position == 'left' and self.rbSpanners[0].isFirst(self.stream):
                endingType = 'start'
            elif position == 'right' and self.rbSpanners[0].isLast(self.stream):
                endingType = 'stop'
            else:
                endingType = ''

            if endingType:
                mxEnding = Element('ending')
                numberList = self.rbSpanners[0].numberRange
                numberStr = str(numberList[0])
                # 0 is not a valid "ending-number"
                if numberStr == '0':
                    numberStr = ''
                for num in numberList[1:]:
                    numberStr += ',' + str(num)  # comma-separated ending numbers
                mxEnding.set('number', numberStr)
                mxEnding.set('type', endingType)
                mxBarline.append(mxEnding)  # make sure it is after fermata but before repeat.

        if mxRepeat is not None:
            mxBarline.append(mxRepeat)

        # TODO: attr: segno
        # TODO: attr: coda
        # TODO: attr: divisions

        self.xmlRoot.append(mxBarline)
        return mxBarline

    def barlineToXml(self, barObject):
        # noinspection PyShadowingNames
        '''
        Translate a music21 bar.Bar object to an mxBar
        while making two substitutions: double -> light-light
        and final -> light-heavy as shown below.

        >>> b = bar.Barline('final')
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxBarline = MEX.barlineToXml(b)
        >>> MEX.dump(mxBarline)
        <barline>
          <bar-style>light-heavy</bar-style>
        </barline>

        >>> b.location = 'right'
        >>> mxBarline = MEX.barlineToXml(b)
        >>> MEX.dump(mxBarline)
        <barline location="right">
          <bar-style>light-heavy</bar-style>
        </barline>
        '''
        mxBarline = Element('barline')
        mxBarStyle = SubElement(mxBarline, 'bar-style')
        mxBarStyle.text = barObject.musicXMLBarStyle()
        # TODO: mxBarStyle attr: color
        if barObject.location is not None:
            mxBarline.set('location', barObject.location)
        return mxBarline

    def repeatToXml(self, r):
        # noinspection PyShadowingNames
        '''
        returns a <repeat> tag from a barline object.

        >>> b = bar.Repeat(direction='end')
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxRepeat = MEX.repeatToXml(b)
        >>> MEX.dump(mxRepeat)
        <repeat direction="backward" />

        >>> b.times = 3
        >>> mxRepeat = MEX.repeatToXml(b)
        >>> MEX.dump(mxRepeat)
        <repeat direction="backward" times="3" />
        '''
        mxRepeat = Element('repeat')
        if r.direction == 'start':
            mxRepeat.set('direction', 'forward')
        elif r.direction == 'end':
            mxRepeat.set('direction', 'backward')
    #         elif self.direction == 'bidirectional':
    #             environLocal.printDebug(['skipping bi-directional repeat'])
        else:
            raise bar.BarException('cannot handle direction format:', r.direction)

        if r.times is not None:
            mxRepeat.set('times', str(r.times))

        # TODO: attr: winged
        return mxRepeat

    def setMxAttributesObjectForStartOfMeasure(self):
        '''
        creates an <attributes> tag at the start of the measure.

        We create one for each measure unless it is identical to self.parent.mxAttributes
        '''
        m = self.stream
        mxAttributes = Element('attributes')
        # TODO: footnote
        # TODO: level

        # TODO: Do something more intelligent with this...
        self.currentDivisions = defaults.divisionsPerQuarter

        if self.parent is None or self.currentDivisions != self.parent.lastDivisions:
            mxDivisions = SubElement(mxAttributes, 'divisions')
            mxDivisions.text = str(self.currentDivisions)
            self.parent.lastDivisions = self.currentDivisions

        if (m.keySignature is not None
                and not self._matchesPreviousPartStaffInGroup(
                    m.keySignature, 'keySignature'
                )):
            mxAttributes.append(self.keySignatureToXml(m.keySignature))
        if (m.timeSignature is not None
                and not self._matchesPreviousPartStaffInGroup(
                    m.timeSignature, 'timeSignature', comparison='ratioEqual'
                )):
            mxAttributes.append(self.timeSignatureToXml(m.timeSignature))
        smts = list(m.getElementsByClass(meter.SenzaMisuraTimeSignature))
        if smts:
            mxAttributes.append(self.timeSignatureToXml(smts[0]))

        # For staves, see joinPartStaffs()
        # TODO: part-symbol
        # TODO: instruments
        if m.clef is not None:
            mxAttributes.append(self.clefToXml(m.clef))

        found = m.getElementsByClass(layout.StaffLayout)
        if found:
            sl = found[0]  # assume only one per measure
            mxAttributes.append(self.staffLayoutToXmlStaffDetails(sl))

        if self.transpositionInterval is not None:
            mxAttributes.append(self.intervalToXmlTranspose(self.transpositionInterval))

        # directive goes here, but is deprecated, do not support
        # measureStyle
        mxMeasureStyle = self.measureStyle()
        if mxMeasureStyle is not None:
            mxAttributes.append(mxMeasureStyle)

        # pylint: disable=len-as-condition
        if len(mxAttributes) > 0 or mxAttributes.attrib:
            self.xmlRoot.append(mxAttributes)
        return mxAttributes

    def measureStyle(self):
        '''
        return a <measure-style> Element or None according to the contents of the Stream.

        Currently, only multiple-rest is supported.
        '''
        m = self.stream

        mxMeasureStyle = None
        mxMultipleRest = None

        rests = m.getElementsByClass(note.Rest)
        if rests:
            hasMMR = rests[0].getSpannerSites('MultiMeasureRest')
            if hasMMR:
                firstRestMMR = hasMMR[0]
                if firstRestMMR.isFirst(rests[0]):
                    mxMultipleRest = Element('multiple-rest')
                    if firstRestMMR.useSymbols:
                        mxMultipleRest.set('use-symbols', 'yes')
                    else:
                        mxMultipleRest.set('use-symbols', 'no')
                    mxMultipleRest.text = str(firstRestMMR.numRests)

        if mxMultipleRest is not None:
            mxMeasureStyle = Element('measure-style')
            # Skip: id: has no corresponding element.
            # TODO or skip: font, color, number.
            mxMeasureStyle.append(mxMultipleRest)

        return mxMeasureStyle

    def staffLayoutToXmlStaffDetails(self, staffLayout):
        '''
        Convert a :class:`~music21.layout.StaffLayout` object to a
        <staff-details> element.

        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> sl = layout.StaffLayout()
        >>> sl.staffLines = 3  # tenor drums?
        >>> sl.staffType = stream.enums.StaffType.CUE
        >>> sl.hidden = True
        >>> mxDetails = MEX.staffLayoutToXmlStaffDetails(sl)
        >>> MEX.dump(mxDetails)
        <staff-details print-object="no">
              <staff-type>cue</staff-type>
              <staff-lines>3</staff-lines>
        </staff-details>
        '''
        # TODO: number lines from the bottom and hide others as necessary
        # see: https://github.com/w3c/musicxml/issues/351
        # TODO: number (bigger issue)
        # TODO: show-frets
        # TODO: print-spacing
        mxStaffDetails = Element('staff-details')
        if staffLayout.hidden is True:
            mxStaffDetails.set('print-object', 'no')
        else:
            mxStaffDetails.set('print-object', 'yes')

        StaffType = stream.enums.StaffType
        if staffLayout.staffType not in (StaffType.REGULAR, StaffType.OTHER):
            mxStaffType = SubElement(mxStaffDetails, 'staff-type')
            mxStaffType.text = staffLayout.staffType.value
        if staffLayout.staffLines is not None:
            mxStaffLines = SubElement(mxStaffDetails, 'staff-lines')
            mxStaffLines.text = str(staffLayout.staffLines)

        # TODO: staff-tuning
        # TODO: capo
        # TODO: staff-size
        return mxStaffDetails

    def timeSignatureToXml(self, ts: meter.TimeSignature | meter.SenzaMisuraTimeSignature):
        '''
        Returns a single <time> tag from a meter.TimeSignature object.

        Compound meters are represented as multiple pairs of beat
        and beat-type elements

        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> a = meter.TimeSignature('3/4')
        >>> b = MEX.timeSignatureToXml(a)
        >>> MEX.dump(b)
        <time>
          <beats>3</beats>
          <beat-type>4</beat-type>
        </time>

        >>> a = meter.TimeSignature('3/4+2/4')
        >>> b = MEX.timeSignatureToXml(a)
        >>> MEX.dump(b)
        <time>
          <beats>3</beats>
          <beat-type>4</beat-type>
          <beats>2</beats>
          <beat-type>4</beat-type>
        </time>

        >>> a.setDisplay('5/4')
        >>> b = MEX.timeSignatureToXml(a)
        >>> MEX.dump(b)
        <time>
          <beats>5</beats>
          <beat-type>4</beat-type>
        </time>

        >>> a = meter.TimeSignature('4/4')
        >>> a.symbol = 'common'
        >>> b = MEX.timeSignatureToXml(a)
        >>> MEX.dump(b)
        <time symbol="common">
          <beats>4</beats>
          <beat-type>4</beat-type>
        </time>

        >>> a.symbol = ''
        >>> a.symbolizeDenominator = True
        >>> b = MEX.timeSignatureToXml(a)
        >>> MEX.dump(b)
        <time symbol="note">
          <beats>4</beats>
          <beat-type>4</beat-type>
        </time>

        >>> sm = meter.SenzaMisuraTimeSignature('free')
        >>> b = MEX.timeSignatureToXml(sm)
        >>> MEX.dump(b)
        <time>
          <senza-misura>free</senza-misura>
        </time>
        '''
        # mxTimeList = []
        mxTime = Element('time')
        _synchronizeIds(mxTime, ts)
        if isinstance(ts, meter.SenzaMisuraTimeSignature):
            mxSenzaMisura = SubElement(mxTime, 'senza-misura')
            if ts.text is not None:
                mxSenzaMisura.text = ts.text
            return mxTime

        # always get a flat version to display any subdivisions created
        fList = tuple((mt.numerator, mt.denominator) for mt in ts.displaySequence.flatten())
        if ts.summedNumerator:
            # this will try to reduce any common denominators into
            # a common group
            fList = meter.tools.fractionToSlashMixed(fList)

        for n, d in fList:
            mxBeats = SubElement(mxTime, 'beats')
            mxBeats.text = str(n)
            mxBeatType = SubElement(mxTime, 'beat-type')
            mxBeatType.text = str(d)
            # TODO: interchangeable

        # TODO: choice -- senza-misura

        # TODO: attr: interchangeable

        # attr: symbol
        if ts.symbolizeDenominator:
            mxTime.set('symbol', 'note')
        elif ts.symbol != '':
            mxTime.set('symbol', ts.symbol)
            # symbol: dotted-note not supported

        # TODO: attr: separator
        self.setPrintStyleAlign(mxTime, ts)
        self.setPrintObject(mxTime, ts)
        return mxTime

    def keySignatureToXml(self, keyOrKeySignature):
        # noinspection PyShadowingNames
        '''
        returns a key tag from a music21
        key.KeySignature or key.Key object

        >>> ks = key.KeySignature(-3)
        >>> ks
        <music21.key.KeySignature of 3 flats>

        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxKey = MEX.keySignatureToXml(ks)
        >>> MEX.dump(mxKey)
        <key>
          <fifths>-3</fifths>
        </key>

        >>> ks.mode = 'major'
        >>> mxKey = MEX.keySignatureToXml(ks)
        >>> MEX.dump(mxKey)
        <key>
          <fifths>-3</fifths>
          <mode>major</mode>
        </key>

        >>> ksNonTrad = key.KeySignature(sharps=None)
        >>> ksNonTrad.alteredPitches = ['C#', 'E-4']
        >>> ksNonTrad
        <music21.key.KeySignature of pitches: [C#, E-4]>

        >>> mxKeyNonTrad = MEX.keySignatureToXml(ksNonTrad)
        >>> MEX.dump(mxKeyNonTrad)
        <key>
          <key-step>C</key-step>
          <key-alter>1</key-alter>
          <key-step>E</key-step>
          <key-alter>-1</key-alter>
          <key-octave number="2">4</key-octave>
        </key>
        '''
        seta = _setTagTextFromAttribute
        mxKey = Element('key')
        _synchronizeIds(mxKey, keyOrKeySignature)
        # TODO: attr: number
        self.setPrintStyle(mxKey, keyOrKeySignature)
        # TODO: attr: print-object

        if not keyOrKeySignature.isNonTraditional:
            # Choice traditional-key
            # TODO: cancel
            seta(keyOrKeySignature, mxKey, 'fifths', 'sharps')
            if hasattr(keyOrKeySignature, 'mode') and keyOrKeySignature.mode is not None:
                seta(keyOrKeySignature, mxKey, 'mode')

        else:
            # choice... non-traditional-key...
            for p in keyOrKeySignature.alteredPitches:
                seta(p, mxKey, 'key-step', 'step')
                a = p.accidental
                if a is None:  # can't imagine why it would be...
                    a = pitch.Accidental(0)
                mxAlter = SubElement(mxKey, 'key-alter')
                mxAlter.text = str(common.numToIntOrFloat(a.alter))
                # TODO: key-accidental

        for i, p in enumerate(keyOrKeySignature.alteredPitches):
            if p.octave is not None:
                mxKeyOctave = SubElement(mxKey, 'key-octave')
                mxKeyOctave.text = str(p.octave)
                mxKeyOctave.set('number', str(i + 1))

        return mxKey

    def clefToXml(self, clefObj):
        '''
        Given a music21 Clef object, return a MusicXML clef
        tag.

        >>> gc = clef.GClef()
        >>> gc
        <music21.clef.GClef>
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxc = MEX.clefToXml(gc)
        >>> MEX.dump(mxc)
        <clef>
          <sign>G</sign>
        </clef>

        >>> b = clef.Treble8vbClef()
        >>> b.octaveChange
        -1
        >>> mxc2 = MEX.clefToXml(b)
        >>> MEX.dump(mxc2)
        <clef>
          <sign>G</sign>
          <line>2</line>
          <clef-octave-change>-1</clef-octave-change>
        </clef>

        >>> pc = clef.PercussionClef()
        >>> mxc3 = MEX.clefToXml(pc)
        >>> MEX.dump(mxc3)
        <clef>
          <sign>percussion</sign>
        </clef>

        Clefs without signs get exported as G clefs with a warning

        >>> generic = clef.Clef()
        >>> mxc4 = MEX.clefToXml(generic)
        Clef with no .sign exported; setting as a G clef
        >>> MEX.dump(mxc4)
        <clef>
          <sign>G</sign>
        </clef>
        '''
        mxClef = Element('clef')
        _synchronizeIds(mxClef, clefObj)

        self.setPrintStyle(mxClef, clefObj)
        # TODO: attr: print-object
        # For attr: number, see joinPartStaffs()
        # TODO: attr: additional
        # TODO: attr: size
        # TODO: attr: after-barline
        sign = clefObj.sign
        if sign is None:
            print('Clef with no .sign exported; setting as a G clef')
            sign = 'G'

        mxSign = SubElement(mxClef, 'sign')
        mxSign.text = sign
        _setTagTextFromAttribute(clefObj, mxClef, 'line')
        if clefObj.octaveChange not in (0, None):
            _setTagTextFromAttribute(clefObj, mxClef, 'clef-octave-change', 'octaveChange')

        return mxClef

    def intervalToXmlTranspose(self, i=None):
        # noinspection PyShadowingNames
        '''
        >>> ME = musicxml.m21ToXml.MeasureExporter()
        >>> i = interval.Interval('P5')
        >>> mxTranspose = ME.intervalToXmlTranspose(i)
        >>> ME.dump(mxTranspose)
        <transpose>
          <diatonic>4</diatonic>
          <chromatic>7</chromatic>
        </transpose>


        >>> i = interval.Interval('A13')
        >>> mxTranspose = ME.intervalToXmlTranspose(i)
        >>> ME.dump(mxTranspose)
        <transpose>
          <diatonic>5</diatonic>
          <chromatic>10</chromatic>
          <octave-change>1</octave-change>
        </transpose>

        >>> i = interval.Interval('-M6')
        >>> mxTranspose = ME.intervalToXmlTranspose(i)
        >>> ME.dump(mxTranspose)
        <transpose>
          <diatonic>-5</diatonic>
          <chromatic>-9</chromatic>
        </transpose>


        >>> i = interval.Interval('-M9')
        >>> mxTranspose = ME.intervalToXmlTranspose(i)
        >>> ME.dump(mxTranspose)
        <transpose>
          <diatonic>-1</diatonic>
          <chromatic>-2</chromatic>
          <octave-change>-1</octave-change>
        </transpose>

        '''
        # TODO: number attribute (staff number)
        # TODO: double empty attribute
        if i is None:
            i = self.transpositionInterval

        genericSteps = i.diatonic.generic.directed
        musicxmlOctaveShift, musicxmlDiatonic = divmod(abs(genericSteps) - 1, 7)
        musicxmlChromatic = abs(i.chromatic.semitones) % 12

        if genericSteps < 0:
            musicxmlDiatonic *= -1
            musicxmlOctaveShift *= -1
            musicxmlChromatic *= -1

        mxTranspose = Element('transpose')
        _synchronizeIds(mxTranspose, i)

        mxDiatonic = SubElement(mxTranspose, 'diatonic')
        mxDiatonic.text = str(musicxmlDiatonic)

        mxChromatic = SubElement(mxTranspose, 'chromatic')
        mxChromatic.text = str(musicxmlChromatic)

        if musicxmlOctaveShift != 0:
            mxOctaveChange = SubElement(mxTranspose, 'octave-change')
            mxOctaveChange.text = str(musicxmlOctaveShift)

        return mxTranspose

    def setMxPrint(self):
        '''
        Creates a <print> element and appends it to root, if one is needed.
        '''
        m = self.stream
        # print objects come before attributes
        # note: this class match is a problem in cases where the object
        #    is created in the module itself, as in a test.

        # do a quick search for any layout objects before searching individually...
        foundAny = m.getElementsByClass(layout.LayoutBase)
        if not foundAny:
            return

        mxPrint = None
        found = foundAny.getElementsByClass(layout.PageLayout)
        if found:
            pl = found[0]  # assume only one per measure
            mxPrint = self.pageLayoutToXmlPrint(pl)
        found = foundAny.getElementsByClass(layout.SystemLayout)
        if found:
            sl = found[0]  # assume only one per measure
            if mxPrint is None:
                mxPrint = self.systemLayoutToXmlPrint(sl)
            else:
                self.systemLayoutToXmlPrint(sl, mxPrint)
        found = foundAny.getElementsByClass(layout.StaffLayout)
        if found:
            sl = found[0]  # assume only one per measure
            if mxPrint is None:
                mxPrint = self.staffLayoutToXmlPrint(sl)
            else:
                self.staffLayoutToXmlPrint(sl, mxPrint)

        # TODO: measure-layout
        if m.hasStyleInformation and m.style.measureNumbering is not None:
            if mxPrint is None:
                mxPrint = Element('print')
            mxMeasureNumbering = SubElement(mxPrint, 'measure-numbering')
            mxMeasureNumbering.text = m.style.measureNumbering
            mnStyle = m.style.measureNumberStyle
            if mnStyle is not None:
                self.setPrintStyleAlign(mxMeasureNumbering, mnStyle)
        # TODO: part-name-display
        # TODO: part-abbreviation-display

        # TODO: attr: blank-page
        # TODO: attr: page-number

        if mxPrint is not None:
            self.xmlRoot.append(mxPrint)

    def staffLayoutToXmlPrint(self, staffLayout, mxPrint=None):
        if mxPrint is None:
            mxPrint = Element('print')
        _synchronizeIds(mxPrint, staffLayout)

        mxStaffLayout = self.staffLayoutToXmlStaffLayout(staffLayout)
        mxPrint.append(mxStaffLayout)
        return mxPrint

    def setMxAttributes(self):
        '''
        sets the attributes (x=y) for a measure,
        that is, number, implicit, and layoutWidth

        Does not create the <attributes> tag. That's elsewhere...
        '''
        m = self.stream
        if hasattr(m, 'measureNumberWithSuffix'):
            self.xmlRoot.set('number', m.measureNumberWithSuffix())
        _setAttributeFromAttribute(
            m, self.xmlRoot, 'implicit', 'showNumber',
            lambda showNum: xmlObjects.booleanToYesNo(showNum is stream.enums.ShowNumber.NEVER))
        # TODO: attr: non-controlling
        if hasattr(m, 'layoutWidth') and m.layoutWidth is not None:
            _setAttributeFromAttribute(m, self.xmlRoot, 'width', 'layoutWidth')

    def setRbSpanners(self):
        '''
        Makes a set of spanners from repeat brackets
        '''
        spannersOnStream = self.spannerBundle.getBySpannedElement(self.stream)
        self.rbSpanners = spannersOnStream.getByClass('RepeatBracket')

    def setTranspose(self):
        '''
        Set the transposition interval based on whether the active
        instrument for this period has a transposition object.

        Stores in self.transpositionInterval.  Returns None
        '''
        if self.parent is None:
            return None
        if self.parent.stream is None:
            return None

        m = self.stream
        self.measureOffsetStart = m.getOffsetBySite(self.parent.stream)

        instSubStream = self.parent.instrumentStream.getElementsByOffset(
            self.measureOffsetStart,
            self.measureOffsetStart + m.duration.quarterLength,
            includeEndBoundary=False)
        if not instSubStream:
            return None

        instSubObj = instSubStream.first()
        if instSubObj.transposition is None:
            return None
        self.transpositionInterval = instSubObj.transposition
        # do here???
        # self.mxTranspose = self.intervalToMXTranspose()
        return None


# unittests moved to test_m21ToXml

if __name__ == '__main__':
    import music21
    music21.mainTest()  # doctests only
