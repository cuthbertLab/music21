# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         musicxml/m21ToXml.py
# Purpose:      Translate from music21 objects to musicxml representation
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010-2012, 2015-19 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Converters for music21 objects to musicxml using ElementTree
'''
from collections import OrderedDict
import copy
import datetime
import fractions
import io
import math
import unittest
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement, ElementTree
from typing import Optional

# external dependencies
import webcolors

# modules that import this include converter.py.
# thus, cannot import these here
from music21 import base
from music21 import common
from music21 import defaults
from music21 import exceptions21

from music21 import bar
from music21 import clef
from music21 import chord  # for typing
from music21 import duration
from music21 import metadata
from music21 import note
from music21 import meter
from music21 import pitch
from music21 import spanner
from music21 import stream
from music21 import style
from music21.stream.iterator import OffsetIterator

from music21.musicxml import xmlObjects

from music21 import environment
_MOD = "musicxml.m21ToXml"
environLocal = environment.Environment(_MOD)

# ------------------------------------------------------------------------------


class MusicXMLExportException(exceptions21.Music21Exception):
    pass


class NoteheadException(MusicXMLExportException):
    pass


def typeToMusicXMLType(value):
    '''Convert a music21 type to a MusicXML type.

    >>> musicxml.m21ToXml.typeToMusicXMLType('longa')
    'long'
    >>> musicxml.m21ToXml.typeToMusicXMLType('quarter')
    'quarter'
    '''
    # MusicXML uses long instead of longa
    if value == 'longa':
        return 'long'
    elif value == '2048th':
        raise MusicXMLExportException('Cannot convert "2048th" duration to MusicXML (too short).')
    else:
        return value


def normalizeColor(color):
    '''
    Normalize a css3 name to hex or leave it alone...

    >>> musicxml.m21ToXml.normalizeColor('')
    ''
    >>> musicxml.m21ToXml.normalizeColor('red')
    '#FF0000'
    >>> musicxml.m21ToXml.normalizeColor('#00ff00')
    '#00FF00'
    '''
    if color in (None, ''):
        return color
    if '#' not in color:
        return webcolors.name_to_hex(color).upper()
    else:
        return color.upper()


def getMetadataFromContext(s):
    '''
    Get metadata from site or context, so that a Part
    can be shown and have the rich metadata of its Score

    >>> s = stream.Stream()
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


def _setTagTextFromAttribute(m21El, xmlEl, tag, attributeName=None,
                             *, transform=None, forceEmpty=False):
    '''
    If m21El has an attribute called attributeName, create a new SubElement
    for xmlEl and set its text to the value of the m21El attribute.

    Pass a function or lambda function as transform to transform the
    value before setting it.  String transformation is assumed.

    Returns the SubElement

    Will not create an empty element unless forceEmpty is True


    >>> from music21.musicxml.m21ToXml import Element
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


def _setAttributeFromAttribute(m21El, xmlEl, xmlAttributeName, attributeName=None, transform=None):
    '''
    If m21El has a at least one element of tag==tag with some text. If
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


def _synchronizeIds(element: Element, m21Object: Optional[base.Music21Object]) -> None:
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
    if m21Object is None or not hasattr(m21Object, 'id'):
        return
    if not xmlObjects.isValidXSDID(m21Object.id):
        return
    element.set('id', m21Object.id)


class GeneralObjectExporter:
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

    def __init__(self, obj=None):
        self.generalObj = obj

    def parse(self, obj=None):
        r'''
        return a bytes object representation of anything from a
        Score to a single pitch.

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
            <measure number="1">
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
        outObj = self.fromGeneralObject(obj)
        # TODO: set whether to do an additional score copy in submethods.
        return self.parseWellformedObject(outObj)

    def parseWellformedObject(self, sc):
        '''
        parse an object that has already gone through the
        `.fromGeneralObject` conversion.  Returns bytes.
        '''
        scoreExporter = ScoreExporter(sc)
        scoreExporter.parse()
        return scoreExporter.asBytes()

    def fromGeneralObject(self, obj):
        '''
        Converts any Music21Object (or a duration or a pitch) to something that
        can be passed to ScoreExporter()

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
        >>> s.flat.notes[0].duration
        <music21.duration.Duration 3.0>
        '''
        classes = obj.classes
        outObj = None
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
        the best one of all -- a perfectly made Score (or something like that)
        '''
        scOut = sc.makeNotation(inPlace=False)
        # scOut.makeImmutable()
        return scOut

    def fromPart(self, p):
        '''
        from a part, put it in a score...
        '''
        if p.isFlat:
            p = p.makeMeasures()
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
        mCopy = m.makeNotation()
        if not m.recurse().getElementsByClass('Clef').getElementsByOffset(0.0):
            mCopy.clef = clef.bestClef(mCopy, recurse=True)
        p = stream.Part()
        p.append(mCopy)
        p.metadata = copy.deepcopy(getMetadataFromContext(m))
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
            if not st.getElementsByClass('Clef').getElementsByOffset(0.0):
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

        elif st.getElementsByClass('Stream')[0].isFlat:  # like a part w/ measures...
            st2 = stream.Part()
            st2.mergeAttributes(st)
            st2.elements = copy.deepcopy(st)
            if not st.getElementsByClass('Clef').getElementsByOffset(0.0):
                bestClef = True
            else:
                bestClef = False
            st2.makeNotation(inPlace=True, bestClef=bestClef)
            st2.metadata = copy.deepcopy(getMetadataFromContext(st))
            return self.fromPart(st2)

        else:
            # probably a problem? or a voice...
            if not st.getElementsByClass('Clef').getElementsByOffset(0.0):
                bestClef = True
            else:
                bestClef = False
            st2 = st.makeNotation(inPlace=False, bestClef=bestClef)
            return self.fromScore(st)

    def fromDuration(self, d):
        '''
        Translate a music21 :class:`~music21.duration.Duration` into
        a complete MusicXML representation.

        Rarely rarely used.  Only if you call .show() on a duration object
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
    #         m = stream.Measure()
    #         m.timeSignature = tsCopy
    #         m.append(note.Rest())
        out = stream.Measure(number=1)
        out.append(objCopy)
        return self.fromMeasure(out)

    def fromGeneralNote(self, n):
        '''
        Translate a music21 :class:`~music21.note.Note` into an object
        ready to be parsed.

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
        '''
        # make a copy, as this process will change tuple types
        # this method is called infrequently, and only for display of a single
        # note
        nCopy = copy.deepcopy(n)

        # modifies in place
        stream.makeNotation.makeTupletBrackets([nCopy.duration], inPlace=True)
        out = stream.Measure(number=1)
        out.append(nCopy)

        # call the musicxml property on Stream
        return self.fromMeasure(out)

    def fromPitch(self, p):
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


def dumpString(obj, *, noCopy=False) -> str:
    r'''
    wrapper around xml.etree.ElementTree as ET that returns a string
    in every case and indents tags and sorts attributes.  (Prints, does not return)

    >>> from music21.musicxml.m21ToXml import Element
    >>> e = Element('accidental')

    >>> musicxml.m21ToXml.dumpString(e)
    '<accidental />'

    >>> e.text = '∆'
    >>> e.text == '∆'
    True
    >>> musicxml.m21ToXml.dumpString(e)
    '<accidental>∆</accidental>'
    '''
    if noCopy is False:
        xmlEl = copy.deepcopy(obj)  # adds 5% overhead
    else:
        xmlEl = obj
    XMLExporterBase.indent(xmlEl)  # adds 5% overhead

    for el in xmlEl.iter():
        attrib = el.attrib
        if len(attrib) > 1:
            # adjust attribute order, e.g. by sorting
            attribs = sorted(attrib.items())
            attrib.clear()
            attrib.update(attribs)
    xStr = ET.tostring(xmlEl, encoding='unicode')
    xStr = xStr.rstrip()
    return xStr


class XMLExporterBase:
    '''
    contains functions that could be called
    at multiple levels of exporting (Score, Part, Measure).
    '''
    def __init__(self):
        self.xmlRoot = None

    def asBytes(self, noCopy=True) -> bytes:
        '''
        returns the xmlRoot as a bytes object. If noCopy is True
        (default), modifies the file for pretty-printing in place.  Otherwise,
        make a copy.
        '''
        sio = io.BytesIO()
        sio.write(self.xmlHeader())
        rootObj = self.xmlRoot
        rootObj_string = dumpString(rootObj, noCopy=noCopy)
        sio.write(rootObj_string.encode('utf-8'))
        v = sio.getvalue()
        sio.close()
        return v

    def addDividerComment(self, comment: str = '') -> None:
        '''
        Add a divider to xmlRoot.

        >>> from music21.musicxml.m21ToXml import Element
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
        commentLength = len(comment)
        if commentLength > 60:
            commentLength = 60
        spacerLengthLow = math.floor((60 - commentLength) / 2)
        spacerLengthHigh = math.ceil((60 - commentLength) / 2)

        commentText = ('=' * spacerLengthLow) + ' ' + comment + ' ' + ('=' * spacerLengthHigh)

        divider = ET.Comment(commentText)
        self.xmlRoot.append(divider)

    # ------------------------------------------------------------------------------
    @staticmethod
    def dump(obj):
        r'''
        wrapper around xml.etree.ElementTree as ET that prints a string
        in every case and indents tags and sorts attributes.  (Prints, does not return)

        >>> from music21.musicxml.m21ToXml import Element
        >>> e = Element('accidental')

        >>> XB = musicxml.m21ToXml.XMLExporterBase
        >>> XB.dump(e)
        <accidental />

        >>> e.text = '∆'
        >>> e.text == '∆'
        True
        >>> XB.dump(e)
        <accidental>∆</accidental>
        '''
        print(dumpString(obj))

    @staticmethod
    def indent(elem, level=0):
        '''
        helper method, indent an element in place:
        '''
        i = '\n' + level * '  '
        lenL = len(elem)
        if lenL:
            if not elem.text or not elem.text.strip():
                elem.text = i + '  '
            if not elem.tail or not elem.tail.strip():
                elem.tail = i

            subElem = None
            for subElem in elem:
                XMLExporterBase.indent(subElem, level + 1)
            if subElem is not None:  # last el...
                subElem.tail = i

            if not elem.tail or not elem.tail.strip():
                elem.tail = '\n' + level * '  '
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

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
            musicXMLNames = [musicXMLNames]

        if m21Names is None:
            m21Names = [common.hyphenToCamelCase(x) for x in musicXMLNames]
        elif not common.isIterable(m21Names):
            m21Names = [m21Names]

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
        self.setStyleAttributes(mxObject, m21Object, 'color')
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

    def accidentalToMx(self, a):
        '''
        Convert a pitch.Accidental object to a Element of tag accidental

        >>> a = pitch.Accidental()
        >>> a.set('half-sharp')
        >>> a.alter == 0.5
        True

        >>> XB = musicxml.m21ToXml.XMLExporterBase()
        >>> a2m = XB.accidentalToMx
        >>> XB.dump(a2m(a))
        <accidental>quarter-sharp</accidental>

        >>> a.set('double-flat')
        >>> XB.dump(a2m(a))
        <accidental>flat-flat</accidental>


        >>> a.set('one-and-a-half-sharp')
        >>> XB.dump(a2m(a))
        <accidental>three-quarters-sharp</accidental>

        >>> a.set('half-flat')
        >>> XB.dump(a2m(a))
        <accidental>quarter-flat</accidental>

        >>> a.set('one-and-a-half-flat')
        >>> XB.dump(a2m(a))
        <accidental>three-quarters-flat</accidental>

        >>> a.set('sharp')
        >>> a.displayStyle = 'parentheses'
        >>> XB.dump(a2m(a))
        <accidental parentheses="yes">sharp</accidental>

        >>> a.displayStyle = 'bracket'
        >>> XB.dump(a2m(a))
        <accidental bracket="yes">sharp</accidental>

        >>> a.displayStyle = 'both'
        >>> XB.dump(a2m(a))
        <accidental bracket="yes" parentheses="yes">sharp</accidental>

        >>> a = pitch.Accidental('flat')
        >>> a.style.relativeX = -2
        >>> XB.dump(a2m(a))
        <accidental relative-x="-2">flat</accidental>

        >>> a = pitch.Accidental()
        >>> a.name = 'double-sharp-down'  # musicxml 3.1
        >>> XB.dump(a2m(a))
        <accidental>double-sharp-down</accidental>

        >>> a.name = 'funnyAccidental'  # unknown
        >>> XB.dump(a2m(a))
        <accidental>other</accidental>
        '''
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

        mxAccidental = Element('accidental')
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


# ---------

class ScoreExporter(XMLExporterBase):
    '''
    Convert a Score (or outer stream with .parts) into
    a musicxml Element.
    '''

    def __init__(self, score=None):
        super().__init__()
        if score is None:
            # should not be done this way.
            self.stream = stream.Score()
        else:
            self.stream = score

        self.xmlRoot = Element('score-partwise', version=defaults.musicxmlVersion)
        self.mxIdentification = None

        self.scoreMetadata = None

        self.spannerBundle = None
        self.meterStream = None
        self.scoreLayouts = None
        self.firstScoreLayout = None
        self.textBoxes = None
        self.highestTime = 0.0

        self.refStreamOrTimeRange = [0.0, self.highestTime]

        self.partExporterList = []

        self.instrumentList = []
        self.midiChannelList = []

        self.parts = []

    def parse(self):
        '''
        the main function to call.

        If self.stream is empty, call self.emptyObject().  Otherwise,

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

        self.scorePreliminaries()

        if s.hasPartLikeStreams():
            self.parsePartlikeScore()
        else:
            self.parseFlatScore()  # TODO(msc): determine if ever called.

        self.postPartProcess()

        # clean up for circular references.
        self.partExporterList.clear()

        return self.xmlRoot

    def emptyObject(self):
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
        out = stream.Stream()
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

    def scorePreliminaries(self):
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
        self.textBoxes = self.stream.flat.getElementsByClass('TextBox')

        # we need independent sub-stream elements to shift in presentation
        self.highestTime = 0.0  # redundant, but set here.

        if self.spannerBundle is None:
            self.spannerBundle = self.stream.spannerBundle

    def setPartsAndRefStream(self):
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
        '''
        s = self.stream
        # environLocal.printDebug('streamToMx(): interpreting multipart')
        streamOfStreams = s.getElementsByClass('Stream')
        for innerStream in streamOfStreams:
            # may need to copy element here
            # apply this stream's offset to elements
            # but retain offsets if inner stream is a Measure
            # https://github.com/cuthbertLab/music21/issues/580
            if isinstance(innerStream, stream.Measure):
                ht = innerStream.offset + innerStream.highestTime
            else:
                innerStream.transferOffsetToElements()
                ht = innerStream.highestTime
            if ht > self.highestTime:
                self.highestTime = ht
        self.refStreamOrTimeRange = [0.0, self.highestTime]
        self.parts = streamOfStreams

    def setMeterStream(self):
        '''
        sets `self.meterStream` or uses a default.

        Used in makeNotation in Part later.

        >>> b = corpus.parse('bwv66.6')
        >>> SX = musicxml.m21ToXml.ScoreExporter(b)
        >>> SX.setMeterStream()
        >>> SX.meterStream
        <music21.stream.Score 0x...>
        >>> len(SX.meterStream)
        4
        >>> SX.meterStream[0]
        <music21.meter.TimeSignature 4/4>
        '''
        s = self.stream
        # search context probably should always be True here
        # to search container first, we need a non-flat version
        # searching a flattened version, we will get contained and non-container
        # this meter  stream is passed to makeNotation()
        meterStream = s.getTimeSignatures(searchContext=False,
                                          sortByCreationTime=False, returnDefault=False)
        # environLocal.printDebug(['setMeterStream: post meterStream search',
        #                meterStream, meterStream[0]])
        if not meterStream:
            # note: this will return a default if no meters are found
            meterStream = s.flat.getTimeSignatures(searchContext=False,
                                                   sortByCreationTime=True, returnDefault=True)
        self.meterStream = meterStream

    def setScoreLayouts(self):
        '''
        sets `self.scoreLayouts` and `self.firstScoreLayout`

        >>> b = corpus.parse('schoenberg/opus19', 2)
        >>> SX = musicxml.m21ToXml.ScoreExporter(b)
        >>> SX.setScoreLayouts()
        >>> SX.scoreLayouts
        <music21.stream.Score 0x...>
        >>> len(SX.scoreLayouts)
        1
        >>> SX.firstScoreLayout
        <music21.layout.ScoreLayout>
        '''
        s = self.stream
        scoreLayouts = s.getElementsByClass('ScoreLayout').stream()
        if scoreLayouts:
            scoreLayout = scoreLayouts[0]
        else:
            scoreLayout = None
        self.scoreLayouts = scoreLayouts
        self.firstScoreLayout = scoreLayout

    def parsePartlikeScore(self):
        '''
        called by .parse() if the score has individual parts.

        Calls makeRests() for the part, then creates a PartExporter for each part,
        and runs .parse() on that part.  appends the PartExporter to self.partExporterList()
        '''
        # would like to do something like this but cannot
        # replace object inside of the stream
        sp = list(self.parts)
        for innerStream in sp:
            innerStream.makeRests(self.refStreamOrTimeRange, inPlace=True)

        count = 0
        for innerStream in sp:
            count += 1
            if count > len(sp):
                raise MusicXMLExportException('infinite stream encountered')

            pp = PartExporter(innerStream, parent=self)
            pp.spannerBundle = self.spannerBundle
            pp.parse()
            self.partExporterList.append(pp)

    def parseFlatScore(self):
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
          <measure number="1">...</measure>
        </part>
        >>> del SX.partExporterList[:]  # for garbage collection
        '''
        s = self.stream
        pp = PartExporter(s, parent=self)
        pp.parse()
        self.partExporterList.append(pp)

    def postPartProcess(self):
        '''
        calls .setScoreHeader() then appends each PartExporter's xmlRoot from
        self.partExporterList to self.xmlRoot

        Called automatically by .parse()
        '''
        self.setScoreHeader()
        for i, pex in enumerate(self.partExporterList):
            self.addDividerComment('Part ' + str(i + 1))
            self.xmlRoot.append(pex.xmlRoot)

    def setScoreHeader(self):
        '''
        Sets the group score-header in <score-partwise>.  Note that score-header is not
        a separate tag, but just a way of grouping things from the tag.

        runs `setTitles()`, `setIdentification()`, `setDefaults()`, changes textBoxes
        to `<credit>` and does the major task of setting up the part-list with `setPartList()`

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

    def textBoxToXmlCredit(self, textBox):
        '''
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
        '''
        # use line carriages to separate messages
        mxCredit = Element('credit')
        # TODO: credit-type
        # TODO: link
        # TODO: bookmark
        # TODO: credit-image

        if textBox.page is not None:
            mxCredit.set('page', str(textBox.page))
        else:
            mxCredit.set('page', '1')

        # add all credit words to components
        count = 0

        for line in textBox.content.split('\n'):
            mxCreditWords = Element('credit-words')
            mxCreditWords.text = line
            # TODO: link/bookmark in credit-words
            if count == 0:  # on first, configure properties
                self.setPrintStyleAlign(mxCreditWords, textBox)
                if textBox.hasStyleInformation and textBox.style.justify is not None:
                    mxCreditWords.set('justify', textBox.style.justify)
            mxCredit.append(mxCreditWords)
            count += 1
        return mxCredit

    def setDefaults(self):
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
            from music21 import layout
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
        if not hasattr(st, 'lineWidths'):
            return  # TODO: remove in v.5 release after all old data is gone.

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
        '''

        spannerBundle = self.spannerBundle

        mxPartList = SubElement(self.xmlRoot, 'part-list')
        # mxComponents is just a list
        # returns a spanner bundle
        staffGroups = spannerBundle.getByClass('StaffGroup')
        # environLocal.printDebug(['got staff groups', staffGroups])

        # first, find which parts are start/end of partGroups
        partGroupIndexRef = {}  # have id be key
        partGroupIndex = 1  # start by 1 by convention
        for pex in self.partExporterList:
            p = pex.stream
            # check for first
            for sg in staffGroups:
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
                if sg.isLast(p):
                    # find the spanner in the dictionary already-assigned
                    for key, value in partGroupIndexRef.items():
                        if value is sg:
                            activeIndex = key
                            break
                    mxPartGroup = Element('part-group')
                    mxPartGroup.set('type', 'stop')
                    if activeIndex is not None:
                        mxPartGroup.set('number', str(activeIndex))
                    mxPartList.append(mxPartGroup)

        return mxPartList

    def staffGroupToXmlPartGroup(self, staffGroup):
        '''
        Create and configure an mxPartGroup object for the 'start' tag
        from a staff group spanner. Note that this object
        is not completely formed by this procedure. (number isn't done...)

        >>> b = corpus.parse('bwv66.6')
        >>> SX = musicxml.m21ToXml.ScoreExporter(b)
        >>> firstStaffGroup = b.spannerBundle.getByClass('StaffGroup')[0]
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
        '''
        mxPartGroup = Element('part-group')
        mxPartGroup.set('type', 'start')
        seta = _setTagTextFromAttribute
        seta(staffGroup, mxPartGroup, 'group-name', 'name')
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

    def setIdentification(self):
        # noinspection SpellCheckingInspection
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

        '''
        if self.mxIdentification is not None:
            mxId = self.mxIdentification
        else:
            mxId = SubElement(self.xmlRoot, 'identification')
            self.mxIdentification = mxId

        # creators
        foundOne = False
        if self.scoreMetadata is not None:
            for c in self.scoreMetadata.contributors:
                mxCreator = self.contributorToXmlCreator(c)
                mxId.append(mxCreator)
                foundOne = True

        if foundOne is False:
            mxCreator = SubElement(mxId, 'creator')
            mxCreator.set('type', 'composer')
            mxCreator.text = defaults.author

        if self.scoreMetadata is not None and self.scoreMetadata.copyright is not None:
            c = self.scoreMetadata.copyright
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

    def metadataToMiscellaneous(self, md=None):
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
          <miscellaneous-field name="date">1689/--/-- or earlier</miscellaneous-field>
          <miscellaneous-field name="localeOfComposition">Rome</miscellaneous-field>
        </miscellaneous>
        '''
        if md is None and self.scoreMetadata is None:
            return None
        elif md is None:
            md = self.scoreMetadata

        mxMiscellaneous = Element('miscellaneous')

        foundOne = False
        for name, value in md.all(skipContributors=True):
            if name in ('movementName', 'movementNumber', 'title', 'copyright'):
                continue
            mxMiscField = SubElement(mxMiscellaneous, 'miscellaneous-field')
            mxMiscField.set('name', name)
            mxMiscField.text = value
            foundOne = True

        if self.mxIdentification is not None and foundOne:
            self.mxIdentification.append(mxMiscellaneous)

        # for testing:
        return mxMiscellaneous

    def setEncoding(self):
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

        if self.scoreMetadata is not None and hasattr(self.scoreMetadata, 'software'):
            # TODO: Remove hasattr after all caches are cleared after v5 release.
            for software in self.scoreMetadata.software:
                mxSoftware = SubElement(mxEncoding, 'software')
                mxSoftware.text = software

        else:
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
        # pylint: disable=redefined-builtin
        def getSupport(attribute, type, value, element):  # @ReservedAssignment
            su = Element('supports')
            su.set('attribute', attribute)
            su.set('type', type)
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

    def setTitles(self):
        '''
        puts work (with work-title), movement-number, movement-title into the self.xmlRoot
        '''
        mdObj = self.scoreMetadata
        if self.scoreMetadata is None:
            mdObj = metadata.Metadata()
        mxScoreHeader = self.xmlRoot
        mxWork = Element('work')
        # TODO: work-number
        if mdObj.title not in (None, ''):
            # environLocal.printDebug(['metadataToMx, got title', mdObj.title])
            mxWorkTitle = SubElement(mxWork, 'work-title')
            mxWorkTitle.text = str(mdObj.title)

        if mxWork:
            mxScoreHeader.append(mxWork)

        if mdObj.movementNumber not in (None, ''):
            mxMovementNumber = SubElement(mxScoreHeader, 'movement-number')
            mxMovementNumber.text = str(mdObj.movementNumber)

        # musicxml often defaults to show only movement title
        # if no movement title is found, get the .title attr
        mxMovementTitle = SubElement(mxScoreHeader, 'movement-title')
        if mdObj.movementName not in (None, ''):
            mxMovementTitle.text = str(mdObj.movementName)
        else:  # it is none
            if mdObj.title is not None:
                mxMovementTitle.text = str(mdObj.title)
            else:
                mxMovementTitle.text = defaults.title

    def contributorToXmlCreator(self, c):
        # noinspection SpellCheckingInspection
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

    def __init__(self, partObj=None, parent=None):
        super().__init__()
        if partObj is None:
            partObj = stream.Part()
        self.stream = partObj
        self.parent = parent  # ScoreExporter
        self.xmlRoot = Element('part')

        if parent is None:
            self.meterStream = stream.Stream()
            self.refStreamOrTimeRange = [0.0, 0.0]
            self.midiChannelList = []
        else:
            self.meterStream = parent.meterStream
            self.refStreamOrTimeRange = parent.refStreamOrTimeRange
            self.midiChannelList = parent.midiChannelList  # shared list

        self.instrumentStream = None
        self.firstInstrumentObject = None

        # keep track of this so that we only put out new attributes when something
        # has changed
        self.lastDivisions = None

        self.spannerBundle = partObj.spannerBundle

    def parse(self):
        '''
        Set up instruments, create a partId (if no good one exists) and sets it on
        <part>, fixes up the notation (`fixupNotationFlat()` or `fixupNotationMeasured()`)
        setsIdLocals on spanner bundle. runs parse() on each measure's MeasureExporter and
        appends the output to the <part> object.

        In other words, one-stop shopping.
        '''
        self.instrumentSetup()

        self.xmlRoot.set('id', str(self.firstInstrumentObject.partId))
        measureStream = self.stream.getElementsByClass('Stream').stream()  # suppose that everything
        # below this is a measure
        if not measureStream:
            self.fixupNotationFlat()
        else:
            self.fixupNotationMeasured(measureStream)
        # make sure that all instances of the same class have unique ids
        self.spannerBundle.setIdLocals()
        for m in measureStream:
            self.addDividerComment('Measure ' + str(m.number))
            measureExporter = MeasureExporter(m, parent=self)
            measureExporter.spannerBundle = self.spannerBundle
            mxMeasure = measureExporter.parse()
            self.xmlRoot.append(mxMeasure)

        return self.xmlRoot

    def instrumentSetup(self):
        '''
        sets self.instrumentStream and self.firstInstrumentObject for the stream,
        checks for a unique midiChannel and then blocks it off from future use.

        Note that there's a deficiency currently that only the first instrument is fully
        converted.

        >>> p = converter.parse('tinyNotation: 4/4 c1 d1 e1')
        >>> p.getElementsByClass('Measure')[0].insert(0, instrument.Clarinet())
        >>> p.getElementsByClass('Measure')[1].insert(0, instrument.BassClarinet())
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

        for thisInstrument in self.instrumentStream:
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

            # add to list for checking on next part
            if self.parent is not None:
                self.parent.instrumentList.append(thisInstrument)
            # force this instrument into this part
            # meterStream is only used here if there are no measures
            # defined in this part

            if thisInstrument.instrumentId is None:
                thisInstrument.instrumentIdRandomize()

    def fixupNotationFlat(self):
        '''
        Runs makeNotation on a flatStream...

        TODO: test if this is redundant.
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
        # spannerContext = measureStream.flat.getContextByClass('Spanner')
        # while spannerContext:
        #    allContexts.append(spannerContext)
        #    spannerContext = spannerContext.getContextByClass('Spanner')
        #
        # spannerBundle = spanner.SpannerBundle(allContexts)
        # only getting spanners at this level
        # spannerBundle = spanner.SpannerBundle(measureStream.flat)
        self.spannerBundle = part.spannerBundle

    def fixupNotationMeasured(self, measureStream):
        '''
        Checks to see if there are any attributes in the part stream and moves
        them into the first measure if necessary.

        Checks if makeAccidentals is run, and haveBeamsBeenMade is done, and
        haveTupletBracketsBeenMade is done.
        '''
        part = self.stream
        # check that first measure has any attributes in outer Stream
        # this is for non-standard Stream formations (some kern imports)
        # that place key/clef information in the containing stream
        if hasattr(measureStream[0], 'clef') and measureStream[0].clef is None:
            measureStream[0].makeMutable()  # must mutate
            outerClefs = part.getElementsByClass('Clef')
            if outerClefs:
                measureStream[0].clef = outerClefs[0]

        if hasattr(measureStream[0], 'keySignature') and measureStream[0].keySignature is None:
            measureStream[0].makeMutable()  # must mutate
            outerKeySignatures = part.getElementsByClass('KeySignature')
            if outerKeySignatures:
                measureStream[0].keySignature = outerKeySignatures[0]

        if hasattr(measureStream[0], 'timeSignature') and measureStream[0].timeSignature is None:
            measureStream[0].makeMutable()  # must mutate
            outerTimeSignatures = part.getElementsByClass('TimeSignature')
            if outerTimeSignatures:
                measureStream[0].timeSignature = outerTimeSignatures[0]
        # see if accidentals/beams can be processed
        if not measureStream.streamStatus.haveAccidentalsBeenMade():
            measureStream.makeAccidentals(inPlace=True)
        if not measureStream.streamStatus.beams:
            try:
                measureStream.makeBeams(inPlace=True)
            except exceptions21.StreamException:
                pass
        if measureStream.streamStatus.haveTupletBracketsBeenMade() is False:
            stream.makeNotation.makeTupletBrackets(measureStream, inPlace=True)

        if not self.spannerBundle:
            self.spannerBundle = spanner.SpannerBundle(measureStream.flat)

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

        # TODO: unbounded...
        i = self.firstInstrumentObject

        if (i.instrumentName is not None or i.instrumentAbbreviation is not None
                or i.midiProgram is not None):
            mxScorePart.append(self.instrumentToXmlScoreInstrument(i))

        # TODO: midi-device
        if i.midiProgram is not None:
            mxScorePart.append(self.instrumentToXmlMidiInstrument(i))

        return mxScorePart

    def instrumentToXmlScoreInstrument(self, i):
        # noinspection SpellCheckingInspection
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
        mxMidiProgram = SubElement(mxMidiInstrument, 'midi-program')
        mxMidiProgram.text = str(i.midiProgram + 1)
        # TODO: midi-unpitched
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
            ('ChordWithFretBoard', 'chordWithFretBoardToXml'),
            ('ChordSymbol', 'chordSymbolToXml'),
            ('Chord', 'chordToXml'),
            ('Rest', 'restToXml'),
            # Skipping unpitched for now
            ('Dynamic', 'dynamicToXml'),
            ('Segno', 'segnoToXml'),
            ('Coda', 'codaToXml'),
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

    def __init__(self, measureObj=None, parent=None):
        super().__init__()
        if measureObj is not None:
            self.stream = measureObj
        else:  # no point, but...
            self.stream = stream.Measure()

        self.parent = parent  # PartExporter
        self.xmlRoot = Element('measure')
        self.currentDivisions = defaults.divisionsPerQuarter

        # TODO: allow for mid-measure transposition changes.
        self.transpositionInterval = None
        self.mxTranspose = None
        self.measureOffsetStart = 0.0
        self.offsetInMeasure = 0.0
        self.currentVoiceId: Optional[int] = None
        self.nextFreeVoiceNumber = 1

        self.rbSpanners = []  # repeatBracket spanners

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

        nonVoiceMeasureItems = m.getElementsNotOfClass('Voice').stream()
        self.parseFlatElements(nonVoiceMeasureItems, backupAfterwards=True)

        allVoices = list(m.voices)
        for i, v in enumerate(allVoices):
            if i == len(allVoices) - 1:
                backupAfterwards = False
            else:
                backupAfterwards = True

            # Assumes voices are flat...
            self.parseFlatElements(v, backupAfterwards=backupAfterwards)

    def parseFlatElements(self, m, *, backupAfterwards=False):
        '''
        Deals with parsing all the elements in .elements, assuming that .elements is flat.

        m here can be a Measure or Voice, but flat...

        If m is a 'Voice' class, we use the .id element to set self.currentVoiceId and then
        send a backup tag to go back to the beginning of the measure.

        Note that if the .id is high enough to be an id(x) memory location, then a small
        voice number is used instead.
        '''
        # TODO: fix mid-measure clef change with voices and part-staff in Schoenberg op. 19 no 2
        # staff 2, m. 6... -- placed at the beginning of the measure not at the appropriate place.
        root = self.xmlRoot
        divisions = self.currentDivisions
        self.offsetInMeasure = 0.0
        if 'Voice' in m.classes:
            m: stream.Voice
            if isinstance(m.id, int) and m.id < defaults.minIdNumberToConsiderMemoryLocation:
                voiceId = m.id
            elif isinstance(m.id, int):
                voiceId = self.nextFreeVoiceNumber
                self.nextFreeVoiceNumber += 1
            else:
                voiceId = m.id
        else:
            voiceId = None

        self.currentVoiceId = voiceId

        # group all objects by offsets and then do a different order than normal sort.
        # that way chord symbols and other 0-width objects appear before notes as much as
        # possible.
        for objGroup in OffsetIterator(m):
            groupOffset = m.elementOffset(objGroup[0])
            amountToMoveForward = int(round(divisions * (groupOffset
                                                             - self.offsetInMeasure)))
            if amountToMoveForward > 0:
                # gap in stream!
                mxForward = Element('forward')
                mxDuration = SubElement(mxForward, 'duration')
                mxDuration.text = str(amountToMoveForward)
                root.append(mxForward)
                self.offsetInMeasure = groupOffset

            notesForLater = []
            for obj in objGroup:
                # we do all non-note elements (including ChordSymbols)
                # first before note elements, in musicxml
                if 'GeneralNote' in obj.classes and 'Harmony' not in obj.classes:
                    notesForLater.append(obj)
                else:
                    self.parseOneElement(obj)

            for n in notesForLater:
                self.parseOneElement(n)

        if backupAfterwards:
            # return to the beginning of the measure.
            amountToBackup = round(divisions * self.offsetInMeasure)
            if amountToBackup:
                mxBackup = Element('backup')
                mxDuration = SubElement(mxBackup, 'duration')
                mxDuration.text = str(amountToBackup)
                root.append(mxBackup)

        self.currentVoiceId = None

    def parseOneElement(self, obj):
        '''
        parse one element completely and add it to xmlRoot, updating
        offsetInMeasure, etc.
        '''
        root = self.xmlRoot
        self.objectSpannerBundle = self.spannerBundle.getBySpannedElement(obj)
        preList, postList = self.prePostObjectSpanners(obj)

        for sp in preList:  # directions that precede the element
            root.append(sp)

        classes = obj.classes
        if 'GeneralNote' in classes:
            self.offsetInMeasure += obj.duration.quarterLength

        # turn inexpressible durations into complex durations (unless unlinked)
        if obj.duration.type == 'inexpressible':
            obj.duration.quarterLength = obj.duration.quarterLength

        # make dotGroups into normal notes
        if len(obj.duration.dotGroups) > 1:
            obj.duration.splitDotGroups(inPlace=True)

        # split at durations...
        if 'GeneralNote' in classes and obj.duration.type == 'complex':
            objList = obj.splitAtDurations()
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

        for sp in postList:  # directions that follow the element
            root.append(sp)

    def prePostObjectSpanners(self, target):
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

        preList = []
        postList = []

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

    def objectAttachedSpannersToNotations(self, obj, objectSpannerBundle=None):
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
        >>> out = mex.objectAttachedSpannersToNotations(n0, m.spannerBundle)
        >>> out
        [<Element 'ornaments' at 0x1114d9408>]
        >>> mex.dump(out[0])
        <ornaments>
          <tremolo type="start">3</tremolo>
        </ornaments>

        >>> out = mex.objectAttachedSpannersToNotations(n1, m.spannerBundle)
        >>> mex.dump(out[0])
        <ornaments>
          <tremolo type="stop">3</tremolo>
        </ornaments>


        '''
        notations = []
        if objectSpannerBundle is not None:
            sb = objectSpannerBundle
        else:
            sb = self.objectSpannerBundle

        if not sb:
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

    def noteToXml(self, n: note.GeneralNote, noteIndexInChord=0, chordParent=None):
        '''
        Translate a music21 :class:`~music21.note.Note` or a Rest into a
        ElementTree, note element.

        Note that, some note-attached spanners, such
        as octave shifts, produce direction (and direction types)
        in this method.

        >>> n = note.Note('D#5')
        >>> n.quarterLength = 3
        >>> n.volume.velocityScalar = 0.5

        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> len(MEX.xmlRoot)
        0
        >>> mxNote = MEX.noteToXml(n)
        >>> mxNote
        <Element 'note' at 0x10113cb38>
        >>> MEX.dump(mxNote)
        <note dynamics="70.56">
          <pitch>
            <step>D</step>
            <alter>1</alter>
            <octave>5</octave>
          </pitch>
          <duration>30240</duration>
          <type>half</type>
          <dot />
          <accidental>sharp</accidental>
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
        <note dynamics="70.56" pizzicato="yes">
          ...
          <notehead parentheses="no">diamond</notehead>
        </note>

        Notes with complex durations need to be simplified before coming here
        otherwise they create an impossible musicxml type of "complex"

        >>> nComplex = note.Note()
        >>> nComplex.duration.quarterLength = 5.0
        >>> mxComplex = MEX.noteToXml(nComplex)
        >>> MEX.dump(mxComplex)
        <note>
          <pitch>
            <step>C</step>
            <octave>4</octave>
          </pitch>
          <duration>50400</duration>
          <type>complex</type>
        </note>

        TODO: Test with spanners...

        '''
        addChordTag = (noteIndexInChord != 0)
        setb = _setAttributeFromAttribute

        chordOrN: note.GeneralNote
        if chordParent is None:
            chordOrN = n
        else:
            chordOrN = chordParent

        mxNote = Element('note')
        # self.setFont(mxNote, chordOrN)
        self.setPrintStyle(mxNote, chordOrN)
        # TODO: attr-group: printout -- replaces print-object, print-spacing below (3.1)
        # TODO: attr: print-leger -- musicxml 3.1
        if (chordOrN.isRest is False
                and chordOrN.hasVolumeInformation()
                and chordOrN.volume.velocityScalar is not None):
            vel = chordOrN.volume.velocityScalar * 100 * (127 / 90)
            mxNote.set('dynamics', '{:.2f}'.format(vel))

        # TODO: attr: end-dynamics
        # TODO: attr: attack
        # TODO: attr: release
        # TODO: attr: time-only
        self.setColor(mxNote, n)  # TODO(msc): is this redundant with setColor below?
        _synchronizeIds(mxNote, n)

        d = chordOrN.duration

        if d.isGrace is True:
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
                environLocal.warn('Duration set as Grace while not being a GraceDuration %s' % d)

        # TODO: cue... / cue-grace
        self.setColor(mxNote, chordOrN)

        self.setPrintObject(mxNote, n)
        if n.hasStyleInformation and n.style.hideObjectOnPrint is True:
            mxNote.set('print-spacing', 'yes')

        for art in chordOrN.articulations:
            if 'Pizzicato' in art.classes:
                mxNote.set('pizzicato', 'yes')

        if addChordTag:
            SubElement(mxNote, 'chord')

        if hasattr(n, 'pitch'):
            n: note.Note
            mxPitch = self.pitchToXml(n.pitch)
            mxNote.append(mxPitch)
        else:
            # assume rest until unpitched works
            # TODO: unpitched
            SubElement(mxNote, 'rest')

        if d.isGrace is not True:
            mxDuration = self.durationXml(d)
            mxNote.append(mxDuration)
            # divisions only
        # TODO: skip if cue:
        if n.tie is not None:
            mxTieList = self.tieToXmlTie(n.tie)
            for t in mxTieList:
                mxNote.append(t)

        # TODO: instrument
        self.setEditorial(mxNote, n)
        if self.currentVoiceId is not None:
            mxVoice = SubElement(mxNote, 'voice')
            mxVoice.text = str(self.currentVoiceId)

        if d.type != 'zero':
            mxType = Element('type')
            mxType.text = typeToMusicXMLType(d.type)
            self.setStyleAttributes(mxType, n, 'size', 'noteSize')
            mxNote.append(mxType)
            for unused_dotCounter in range(d.dots):
                SubElement(mxNote, 'dot')
                # TODO: dot placement...

        elif d.components:
            mxType = Element('type')
            mxType.text = typeToMusicXMLType(d.components[0].type)
            self.setStyleAttributes(mxType, n, 'size', 'noteSize')
            if (n.hasStyleInformation
                    and hasattr(n.style, 'noteSize')
                    and n.style.noteSize is not None):
                mxType.set('size', n.style.noteSize)

            mxNote.append(mxType)
            for unused_dotCounter in range(d.components[0].dots):
                SubElement(mxNote, 'dot')

        if (hasattr(n, 'pitch')
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
                and hasattr(chordOrN, 'stemDirection')
                and chordOrN.stemDirection != 'unspecified'):
            chordOrN: note.NotRest
            stemDirection = chordOrN.stemDirection
        # or if we are in a chord, but the sub-note has its own stem direction,
        # record that.
        elif (chordOrN is not n
                and hasattr(n, 'stemDirection')
                and n.stemDirection != 'unspecified'):
            n: note.NotRest
            stemDirection = n.stemDirection

        if stemDirection is not None:
            mxStem = SubElement(mxNote, 'stem')
            sdText = stemDirection
            if sdText == 'noStem':
                sdText = 'none'
            mxStem.text = sdText
            if chordOrN.hasStyleInformation and chordOrN.style.stemStyle is not None:
                self.setColor(mxStem, chordOrN.style.stemStyle)
                self.setPosition(mxStem, chordOrN.style.stemStyle)

        # end Stem

        # notehead
        self.dealWithNotehead(mxNote, n, chordParent)

        # TODO: notehead-text

        # beam
        if addChordTag is False:
            if hasattr(chordOrN, 'beams') and chordOrN.beams is not None:
                chordOrN: note.NotRest
                nBeamsList = self.beamsToXml(chordOrN.beams)
                for mxB in nBeamsList:
                    mxNote.append(mxB)

        # TODO: staff

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

    def restToXml(self, r: note.Rest):
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


        display-step and display-octave should work:

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

        isFullMeasure = False
        if r.fullMeasure in (True, 'always'):
            isFullMeasure = True
            mxRestTag.set('measure', 'yes')
        elif r.fullMeasure == 'auto':
            tsContext = r.getContextByClass('TimeSignature')
            if tsContext and tsContext.barDuration.quarterLength == r.duration.quarterLength:
                isFullMeasure = True

        if isFullMeasure:
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
            currentClef = r.getContextByClass('Clef')
            if currentClef is None or not hasattr(currentClef, 'lowestLine'):
                currentClef = clef.TrebleClef()  # this should not be common enough to
                # worry about the overhead
            midLineDNN = currentClef.lowestLine + 4
            restObjectPseudoDNN = midLineDNN + r.stepShift
            tempPitch = pitch.Pitch()
            tempPitch.diatonicNoteNum = restObjectPseudoDNN
            mxDisplayStep.text = tempPitch.step
            mxDisplayOctave.text = str(tempPitch.octave)

        return mxNote

    def chordToXml(self, c: chord.Chord):
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


        Test that notehead translation works:

        >>> g = pitch.Pitch('g3')
        >>> h = note.Note('b4')
        >>> h.notehead = 'diamond'
        >>> ch2 = chord.Chord([g, h])
        >>> ch2.quarterLength = 2.0
        >>> mxNoteList = MEX.chordToXml(ch2)
        >>> MEX.dump(mxNoteList[1])
        <note>
          <chord />
          <pitch>
            <step>B</step>
            <octave>4</octave>
          </pitch>
          <duration>20160</duration>
          <type>half</type>
          <notehead parentheses="no">diamond</notehead>
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
        for i, n in enumerate(c):
            mxNoteList.append(self.noteToXml(n, i, chordParent=c))
        return mxNoteList

    def durationXml(self, dur: duration.Duration):
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
        '''
        convert a pitch to xml... does not create the <accidental> tag...

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

    def fretBoardToXml(self, fretBoard) -> Optional[Element]:
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

    def chordWithFretBoardToXml(self, cwf) -> Element:
        '''
        Deals with both chords and frets.
        Generate harmony and append xml to it.
        '''
        mxHarmony = self.chordSymbolToXml(cwf)
        mxFrame = self.fretBoardToXml(cwf)

        if mxFrame is not None:
            mxHarmony.append(mxFrame)

        return mxHarmony

    def tupletToTimeModification(self, tup) -> Element:
        '''
        >>> t = duration.Tuplet(11, 8)
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxTimeMod = MEX.tupletToTimeModification(t)
        >>> MEX.dump(mxTimeMod)
        <time-modification>
          <actual-notes>11</actual-notes>
          <normal-notes>8</normal-notes>
        </time-modification>

        >>> t.setDurationType('eighth', dots=2)
        >>> mxTimeMod = MEX.tupletToTimeModification(t)
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
        chordParent: Optional[chord.Chord] = None
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
        if (hasattr(n, 'notehead')
            and (n.notehead != 'normal'
                 or n.noteheadParenthesis
                 or n.noteheadFill is not None
                 or (n.hasStyleInformation and n.style.color not in (None, '')))):
            n: note.NotRest
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
        '''
        Translate a music21 :class:`~music21.note.NotRest` object
        such as a Note, or Unpitched object, or Chord
        into a <notehead> tag

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
        if n.hasStyleInformation and n.style.color not in (None, ''):
            color = normalizeColor(n.style.color)
            mxNotehead.set('color', color)
        return mxNotehead

    def noteToNotations(self, n, noteIndexInChord=0, chordParent=None):
        '''
        Take information from .expressions,
        .articulations, and spanners to
        make the <notations> tag for a note.
        '''
        mxArticulations = None
        mxTechnicalMark = None
        mxOrnaments = None
        isSingleNoteOrFirstInChord = (noteIndexInChord == 0)

        notations = []

        chordOrNote = n
        if chordParent is not None:
            # get expressions from first note of chord
            chordOrNote = chordParent

        # only apply expressions to notes or the first note of a chord...
        if isSingleNoteOrFirstInChord:
            for expObj in chordOrNote.expressions:
                mxExpression = self.expressionToXml(expObj)
                if mxExpression is None:
                    # print('Could not convert expression: ', mxExpression)
                    # TODO: should not!
                    continue
                if 'Ornament' in expObj.classes:
                    if mxOrnaments is None:
                        mxOrnaments = Element('ornaments')
                    mxOrnaments.append(mxExpression)
                    # print(mxExpression)
                else:
                    notations.append(mxExpression)

        # apply all articulations apart from fingerings only to first note of chord
        applicableArticulations = []
        fingeringNumber = 0
        for a in chordOrNote.articulations:
            if 'Fingering' in a.classSet:
                if fingeringNumber == noteIndexInChord:
                    applicableArticulations.append(a)
                fingeringNumber += 1
            elif isSingleNoteOrFirstInChord:
                applicableArticulations.append(a)

        for artObj in applicableArticulations:
            if 'Pizzicato' in artObj.classes:
                continue
            if 'TechnicalIndication' in artObj.classes:
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

        if isSingleNoteOrFirstInChord and chordParent is not None:
            notations.extend(self.objectAttachedSpannersToNotations(chordParent))
        elif chordParent is not None:
            pass
        else:
            notations.extend(self.objectAttachedSpannersToNotations(n))
        # TODO: slur
        # TODO: glissando
        # TODO: slide

        for x in (mxArticulations,
                  mxTechnicalMark,
                  mxOrnaments):
            if x:
                notations.append(x)

        # TODO: dynamics in notations
        # TODO: arpeggiate
        # TODO: non-arpeggiate
        # TODO: accidental-mark
        # TODO: other-notation
        return notations

    def tieToXmlTie(self, t):
        '''
        returns a list of ties from a Tie object.

        A 'continue' tie requires two <tie> tags to represent.

        >>> t = tie.Tie('continue')
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> tieList = MEX.tieToXmlTie(t)
        >>> for mxT in tieList:
        ...     MEX.dump(mxT)
        <tie type="stop" />
        <tie type="start" />
        '''
        mxTieList = []

        if t.type == 'continue':
            musicxmlTieType = 'stop'
        else:
            musicxmlTieType = t.type
        mxTie = Element('tie')
        mxTie.set('type', musicxmlTieType)
        mxTieList.append(mxTie)

        if t.type == 'continue':
            mxTie = Element('tie')
            mxTie.set('type', 'start')
            mxTieList.append(mxTie)

        return mxTieList

    def tieToXmlTied(self, t):
        '''
        In musicxml, a tie is represented in sound
        by the tie tag (near the pitch object), and
        the <tied> tag in notations.  This
        creates the <tied> tag.

        Returns a list since a music21
        "continue" tie type needs two tags
        in musicxml.  List may be empty
        if tie.style == "hidden"

        >>> t = tie.Tie('continue')
        >>> t.id = 'tied1'

        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> tiedList = MEX.tieToXmlTied(t)
        >>> for mxT in tiedList:
        ...     MEX.dump(mxT)
        <tied id="tied1" type="stop" />
        <tied type="start" />

        >>> t.style = 'hidden'
        >>> tiedList = MEX.tieToXmlTied(t)
        >>> len(tiedList)
        0
        '''
        if t.style == 'hidden':
            return []

        mxTiedList = []
        if t.type == 'continue':
            musicxmlTieType = 'stop'
        else:
            musicxmlTieType = t.type

        mxTied = Element('tied')
        _synchronizeIds(mxTied, t)

        mxTied.set('type', musicxmlTieType)
        mxTiedList.append(mxTied)

        if t.type == 'continue':
            mxTied = Element('tied')
            mxTied.set('type', 'start')
            mxTiedList.append(mxTied)

        # TODO: attr: number (distinguishing ties on enharmonics)
        if t.style != 'normal' and t.type != 'stop':
            mxTied.set('line-type', t.style)
            # wavy is not supported as a tie type.

        # Tie style needs to be dealt with after changes to Tie object...

        # TODO: attrGroup: dashed-formatting
        # TODO: attrGroup: position

        if t.placement is not None:
            mxTied.set('placement', t.placement)
            orientation = None
            if t.placement == 'above':
                orientation = 'over'
            elif t.placement == 'below':
                orientation = 'under'
            # MuseScore requires 'orientation' not placement
            # should be no need for separate orientation
            # http://forums.makemusic.com/viewtopic.php?f=12&t=2179&start=0
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

        >>> t = duration.Tuplet(11, 8)
        >>> t.type = 'start'
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxTup = MEX.tupletToXmlTuplet(t)
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

        >>> t.tupletActualShow = 'both'
        >>> t.tupletNormalShow = 'type'
        >>> mxTup = MEX.tupletToXmlTuplet(t)
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

    def expressionToXml(self, expression):
        '''
        Convert a music21 Expression (expression or ornament)
        to a musicxml tag;
        return None if no conversion is possible.

        Expressions apply only to the first note of chord.

        >>> t = expressions.InvertedTurn()
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxExpression = MEX.expressionToXml(t)
        >>> MEX.dump(mxExpression)
        <inverted-turn placement="above" />

        Two special types...

        >>> f = expressions.Fermata()
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxExpression = MEX.expressionToXml(f)
        >>> MEX.dump(mxExpression)
        <fermata type="inverted" />
        >>> f.shape = 'angled'
        >>> mxExpression = MEX.expressionToXml(f)
        >>> MEX.dump(mxExpression)
        <fermata type="inverted">angled</fermata>

        >>> t = expressions.Tremolo()
        >>> t.numberOfMarks = 4
        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> mxExpression = MEX.expressionToXml(t)
        >>> MEX.dump(mxExpression)
        <tremolo type="single">4</tremolo>
        '''
        mapping = OrderedDict([
            ('Trill', 'trill-mark'),
            # TODO: delayed-inverted-turn
            # TODO: vertical-turn
            # TODO: 'delayed-turn'
            ('InvertedTurn', 'inverted-turn'),
            # last as others are subclasses
            ('Turn', 'turn'),
            ('InvertedMordent', 'inverted-mordent'),
            ('Mordent', 'mordent'),
            ('Shake', 'shake'),
            ('Schleifer', 'schleifer'),
            # TODO: 'accidental-mark'
            ('Tremolo', 'tremolo'),  # non-spanner
            # non-ornaments...
            ('Fermata', 'fermata'),
            # keep last...
            ('Ornament', 'other-ornament'),
        ])
        mx = None
        classes = expression.classes
        for k, v in mapping.items():
            if k in classes:
                mx = Element(v)
                break
        if mx is None:
            environLocal.printDebug(['no musicxml conversion for:', expression])
            return

        self.setPrintStyle(mx, expression)
        # TODO: trill-sound
        if hasattr(expression, 'placement') and expression.placement is not None:
            mx.set('placement', expression.placement)
        if 'Fermata' in classes:
            mx.set('type', str(expression.type))
            if expression.shape in ('angled', 'square'):  # only valid shapes
                mx.text = expression.shape
            _synchronizeIds(mx, expression)

        if 'Tremolo' in classes:
            mx.set('type', 'single')
            mx.text = str(expression.numberOfMarks)

        return mx

    def articulationToXmlArticulation(self, articulationMark):
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


        Some style!

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
            mxArticulationMark.set('type', articulationMark.pointDirection)
        if musicXMLArticulationName in ('doit', 'falloff', 'plop', 'scoop'):
            self.setLineStyle(mxArticulationMark, articulationMark)
        if musicXMLArticulationName == 'breath-mark' and articulationMark.symbol is not None:
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

    def articulationToXmlTechnical(self, articulationMark):
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
            raise MusicXMLExportException(
                'Cannot translate technical indication %s to musicxml' % articulationMark)
        mxTechnicalMark = Element(musicXMLTechnicalName)
        if articulationMark.placement is not None:
            mxTechnicalMark.set('placement', articulationMark.placement)
        if musicXMLTechnicalName == 'fingering':
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
            mxTechnicalMark.set('substitution',
                                xmlObjects.booleanToYesNo(articulationMark.substitution))
        if musicXMLTechnicalName == 'string':
            mxTechnicalMark.text = str(articulationMark.number)
        if musicXMLTechnicalName == 'fret':
            mxTechnicalMark.text = str(articulationMark.number)

        # harmonic needs to check for whether it is artificial or natural, and
        # whether it is base-pitch, sounding-pitch, or touching-pitch
        if musicXMLTechnicalName == 'harmonic':
            self.setHarmonic(mxTechnicalMark, articulationMark)

        self.setPrintStyle(mxTechnicalMark, articulationMark)
        # mxArticulations.append(mxArticulationMark)
        return mxTechnicalMark

    @staticmethod
    def setHarmonic(mxh, harm):
        '''
        Sets the artificial or natural tag (or no tag) and
        zero or one of base-pitch, sounding-pitch, touching-pitch

        Called from articulationToXmlTechnical

        >>> MEXClass = musicxml.m21ToXml.MeasureExporter

        >>> a = articulations.Harmonic()
        >>> a.harmonicType = 'artificial'
        >>> a.pitchType = 'sounding'

        >>> from music21.musicxml.m21ToXml import Element
        >>> mxh = Element('harmonic')

        >>> MEXClass.setHarmonic(mxh, a)
        >>> MEXClass.dump(mxh)
        <harmonic>
          <artificial />
          <sounding-pitch />
        </harmonic>
        '''
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

    def noChordToXml(self, cs):
        '''
        Convert a NoChord object to an mxHarmony object.

        '''
        if cs.writeAsChord is True:
            return self.chordToXml(cs)

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
        assert cs.chordKind == 'none'
        mxKind.text = str(cKind)
        assert cs.chordKindStr not in (None, '')
        mxKind.set('text', cs.chordKindStr)

        self.setOffsetOptional(cs, mxHarmony)
        self.setEditorial(mxHarmony, cs)

        self.xmlRoot.append(mxHarmony)
        return mxHarmony

    def chordSymbolToXml(self, cs):
        '''
        Convert a ChordSymbol object to an mxHarmony object.

        >>> cs = harmony.ChordSymbol()
        >>> cs.root('E-')
        >>> cs.bass('B-')
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
            <degree-alter />
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

        from music21 import harmony

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
            return

        mxKind = SubElement(mxHarmony, 'kind')
        cKind = cs.chordKind
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
            if hd.interval is not None:
                # will return -1 for '-a1'
                mxDegreeAlter.text = str(hd.interval.chromatic.directed)
                # TODO: attrGroup: print-style
                # TODO: attr: plus-minus (yes, no)
            mxDegreeType = SubElement(mxDegree, 'degree-type')
            mxDegreeType.text = str(hd.modType)
            # TODO: attr: text -- alternate display
            # TODO: attrGroup: print-style

        # TODO: frame -- fretboard
        self.setOffsetOptional(cs, mxHarmony)
        self.setEditorial(mxHarmony, cs)
        # TODO: staff

        self.xmlRoot.append(mxHarmony)
        return mxHarmony

    def setOffsetOptional(self, m21Obj, mxObj=None, *, setSound=True):
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

    def placeInDirection(self, mxObj, m21Obj=None):
        '''
        places the mxObj <element> inside <direction><direction-type>
        '''
        mxDirection = Element('direction')
        mxDirectionType = SubElement(mxDirection, 'direction-type')
        mxDirectionType.append(mxObj)
        if (m21Obj is not None
                and hasattr(m21Obj, 'positionPlacement')
                and m21Obj.positionPlacement is not None):
            mxDirection.set('placement', m21Obj.positionPlacement)

        return mxDirection

    def dynamicToXml(self, d):
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

        mxDirection = self.placeInDirection(mxDynamics, d)
        # direction todos
        self.setOffsetOptional(d, mxDirection)
        self.setEditorial(mxDirection, d)
        # TODO: voice
        # TODO: staff

        # sound
        vS = d.volumeScalar
        if vS is not None:
            mxSound = SubElement(mxDirection, 'sound')
            # do not set id, since the element is the same in music21.

            dynamicVolume = int(vS * 127)
            mxSound.set('dynamics', str(dynamicVolume))

        self.xmlRoot.append(mxDirection)
        return mxDirection

    def segnoToXml(self, segno):
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

    def codaToXml(self, coda):
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

    def tempoIndicationToXml(self, ti):
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
            <words default-y="45" enclosure="none" font-style="bold"
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
        '''
        # if writing just a sound tag, place an empty words tag in a
        # direction type and then follow with sound declaration
        # storing lists to accommodate metric modulations
        durs = []  # duration objects
        numbers = []  # tempi
        hideNumericalMetro = False  # if numbers implicit, hide metronome numbers
        hideNumber = []  # hide the number after equal, e.g., quarter=120, hide 120
        # store the last value necessary as a sounding tag in bpm
        soundingQuarterBPM = False
        if 'MetronomeMark' in ti.classes:
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
            soundingQuarterBPM = ti.getQuarterBPM()

        elif 'MetricModulation' in ti.classes:
            # may need to reverse order if classical style or otherwise
            # may want to show first number
            hideNumericalMetro = False  # must show for metric modulation
            for sub in (ti.oldMetronome, ti.newMetronome):
                hideNumber.append(True)  # cannot show numbers in a metric modulation
                durs.append(sub.referent)
                numbers.append(sub.number)
            # soundingQuarterBPM should be obtained from the last MetronomeMark
            soundingQuarterBPM = ti.newMetronome.getQuarterBPM()

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

        if ti.parentheses:
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

        if soundingQuarterBPM is not None:
            mxSound = SubElement(mxDirection, 'sound')
            mxSound.set('tempo', str(common.numToIntOrFloat(soundingQuarterBPM)))

        if hideNumericalMetro is not None:
            self.xmlRoot.append(mxDirection)

        if 'MetronomeMark' in ti.classes:
            if ti.getTextExpression(returnImplicit=False) is not None:
                te = ti.getTextExpression(returnImplicit=False)
                te.offset = ti.offset
                unused_mxDirectionText = self.textExpressionToXml(te)

        return mxDirection

    def rehearsalMarkToXml(self, rm):
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

    def textExpressionToXml(self, teOrRe):
        '''
        Convert a TextExpression or RepeatExpression to a MusicXML mxDirection type.
        returns a musicxml.mxObjects.Direction object
        '''
        mxWords = Element('words')
        if hasattr(teOrRe, 'content'):  # TextExpression
            te = teOrRe
            mxWords.text = str(te.content)
        elif hasattr(teOrRe, 'getText'):  # RepeatExpression
            te = teOrRe.getTextExpression()
            te.offset = teOrRe.offset
            mxWords.text = str(te.content)
        else:
            raise MusicXMLExportException('teOrRe must be a TextExpression or RepeatExpression')

        self.setTextFormatting(mxWords, te)

        mxDirection = self.placeInDirection(mxWords, te)
        self.setOffsetOptional(te, mxDirection, setSound=False)
        self.xmlRoot.append(mxDirection)
        return mxDirection

    def wrapObjectInAttributes(self, objectToWrap, methodToMx):
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
            return

        mxAttributes = Element('attributes')

        mxObj = methodToMx(objectToWrap)
        mxAttributes.append(mxObj)

        self.xmlRoot.append(mxAttributes)

        return mxAttributes

    # -----------------------------
    # note helpers...

    def lyricToXml(self, ly):
        '''
        Translate a music21 :class:`~music21.note.Lyric` object
        to a <lyric> tag.

        Lyrics have attribute list %justify, %position, %placement, %color, %print-object
        '''
        mxLyric = Element('lyric')
        _setTagTextFromAttribute(ly, mxLyric, 'syllabic')
        _setTagTextFromAttribute(ly, mxLyric, 'text', forceEmpty=True)
        # TODO: elision
        # TODO: more syllabic
        # TODO: more text
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
        music21.musicxml.m21ToXml.MusicXMLExportException: partial beam defined
            without a proper direction set (set to None)

        >>> a.type = 'crazy'
        >>> b = MEX.beamToXml(a)
        Traceback (most recent call last):
        music21.musicxml.m21ToXml.MusicXMLExportException: unexpected beam type encountered (crazy)
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
                'unexpected beam type encountered (%s)' % beamObject.type
            )

        mxBeam.set('number', str(beamObject.number))
        # BeamObject has no .id -- fix?
        # _synchronizeIds(mxBeam, beamObject)

        # not to be done: repeater (deprecated)
        self.setColor(mxBeam, beamObject)
        self.setStyleAttributes(mxBeam, beamObject, 'fan')

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
            if 'Repeat' in barline.classes:
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

        if self.rbSpanners:  # and self.rbSpanners[0].isFirst(m)???
            mxEnding = Element('ending')
            if position == 'left':
                endingType = 'start'
            else:
                endingType = 'stop'
            numberList = self.rbSpanners[0].getNumberList()
            numberStr = str(numberList[0])
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

        if 'Measure' in m.classes:
            if m.keySignature is not None:
                mxAttributes.append(self.keySignatureToXml(m.keySignature))
            if m.timeSignature is not None:
                mxAttributes.append(self.timeSignatureToXml(m.timeSignature))
            smts = list(m.getElementsByClass('SenzaMisuraTimeSignature'))
            if smts:
                mxAttributes.append(self.timeSignatureToXml(smts[0]))

            # TODO: staves (piano staff...)
            # TODO: part-symbol
            # TODO: instruments
            if m.clef is not None:
                mxAttributes.append(self.clefToXml(m.clef))

        found = m.getElementsByClass('StaffLayout')
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

        rests = m.getElementsByClass('Rest')
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

        <staff-type> is not yet supported.

        >>> MEX = musicxml.m21ToXml.MeasureExporter()
        >>> sl = layout.StaffLayout()
        >>> sl.staffLines = 3  # tenor drums?
        >>> sl.hidden = True
        >>> mxDetails = MEX.staffLayoutToXmlStaffDetails(sl)
        >>> MEX.dump(mxDetails)
        <staff-details print-object="no">
              <staff-lines>3</staff-lines>
        </staff-details>
        '''
        mxStaffDetails = Element('staff-details')
        # TODO: staff-type
        if staffLayout.staffLines is not None:
            mxStaffLines = SubElement(mxStaffDetails, 'staff-lines')
            mxStaffLines.text = str(staffLayout.staffLines)

        if staffLayout.hidden is True:
            mxStaffDetails.set('print-object', 'no')
        else:
            mxStaffDetails.set('print-object', 'yes')
        return mxStaffDetails

    def timeSignatureToXml(self, ts):
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
        if 'SenzaMisuraTimeSignature' in ts.classes:
            mxSenzaMisura = SubElement(mxTime, 'senza-misura')
            if ts.text is not None:
                mxSenzaMisura.text = ts.text
            return mxTime

        # always get a flat version to display any subdivisions created
        fList = [(mt.numerator, mt.denominator) for mt in ts.displaySequence.flat._partition]
        if ts.summedNumerator:
            # this will try to reduce any common denominators into
            # a common group
            fList = meter.fractionToSlashMixed(fList)

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

        >>> ksNonTrad = key.KeySignature()
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

        # TODO: attr: number
        self.setPrintStyle(mxClef, clefObj)
        # TODO: attr: print-object
        # TODO: attr: number (staff number)
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
        foundAny = m.getElementsByClass('LayoutBase')
        if not foundAny:
            return

        mxPrint = None
        found = m.getElementsByClass('PageLayout')
        if found:
            pl = found[0]  # assume only one per measure
            mxPrint = self.pageLayoutToXmlPrint(pl)
        found = m.getElementsByClass('SystemLayout')
        if found:
            sl = found[0]  # assume only one per measure
            if mxPrint is None:
                mxPrint = self.systemLayoutToXmlPrint(sl)
            else:
                self.systemLayoutToXmlPrint(sl, mxPrint)
        found = m.getElementsByClass('StaffLayout')
        if found:
            sl = found[0]  # assume only one per measure
            if mxPrint is None:
                mxPrint = self.staffLayoutToXmlPrint(sl)
            else:
                self.staffLayoutToXmlPrint(sl, mxPrint)

        # TODO: measure-layout
        if m.hasStyleInformation and m.style.measureNumbering is not None:
            if mxPrint is None:
                mxPrint = ET.Element('print')
            mxMeasureNumbering = ET.SubElement(mxPrint, 'measure-numbering')
            mxMeasureNumbering.text = m.style.measureNumbering
            mnStyle = m.style.measureNumberingStyle
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
        that is, number, and layoutWidth

        Does not create the <attributes> tag. That's elsewhere...

        '''
        m = self.stream
        if hasattr(m, 'measureNumberWithSuffix'):
            self.xmlRoot.set('number', m.measureNumberWithSuffix())
        # TODO: attr: implicit
        # TODO: attr: non-controlling
        if hasattr(m, 'layoutWidth') and m.layoutWidth is not None:
            _setAttributeFromAttribute(m, self.xmlRoot, 'width', 'layoutWidth')

    def setRbSpanners(self):
        '''
        Makes a set of spanners from repeat brackets
        '''
        self.rbSpanners = self.spannerBundle.getBySpannedElement(
            self.stream).getByClass('RepeatBracket')

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
        if self.parent.stream.atSoundingPitch is True:
            return None

        m = self.stream
        self.measureOffsetStart = m.getOffsetBySite(self.parent.stream)

        instSubStream = self.parent.instrumentStream.getElementsByOffset(
            self.measureOffsetStart,
            self.measureOffsetStart + m.duration.quarterLength,
            includeEndBoundary=False)
        if not instSubStream:
            return None

        instSubObj = instSubStream[0]
        if instSubObj.transposition is None:
            return None
        self.transpositionInterval = instSubObj.transposition
        # do here???
        # self.mxTranspose = self.intervalToMXTranspose()
        return None


# ------------------------------------------------------------------------------
def indent(elem, level=0):
    i = '\n' + level * '  '
    # pylint: disable=len-as-condition
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + '  '
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subEl in elem:
            indent(subEl, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


class Test(unittest.TestCase):

    def getXml(self, obj):
        gex = GeneralObjectExporter()
        bytesOut = gex.parse(obj)
        bytesOutUnicode = bytesOut.decode('utf-8')
        return bytesOutUnicode

    def getET(self, obj):
        SX = ScoreExporter(obj)
        mxScore = SX.parse()
        SX.indent(mxScore)
        return mxScore

    def testBasic(self):
        pass

    def testSpannersWrite(self):
        from music21 import converter
        p = converter.parse("tinynotation: 4/4 c4 d e f g a b c' b a g2")
        listNotes = list(p.recurse().notes)
        c = listNotes[0]
        d = listNotes[1]
        sl1 = spanner.Slur([c, d])
        p.insert(0.0, sl1)
        # p.getElementsByClass('Measure')[0].insert(0.0, sl1)

        f = listNotes[3]
        g = listNotes[4]
        a = listNotes[5]
        sl2 = spanner.Slur([f, g, a])
        p.insert(0.0, sl2)
        # p.getElementsByClass('Measure')[0].insert(0.0, sl2)

        c2 = listNotes[6]
        g2 = listNotes[-1]
        sl3 = spanner.Slur([c2, g2])
        p.insert(0.0, sl3)
        # p.getElementsByClass('Measure')[1].insert(0.0, sl3)
        self.assertEqual(self.getXml(p).count('<slur '), 6)

    def testLowVoiceNumbers(self):
        n = note.Note()
        v1 = stream.Voice([n])
        m = stream.Measure([v1])
        xmlOut = self.getXml(m)
        self.assertIn('<voice>1</voice>', xmlOut)
        n2 = note.Note()
        v2 = stream.Voice([n2])
        m.insert(0, v2)
        xmlOut = self.getXml(m)
        self.assertIn('<voice>1</voice>', xmlOut)
        self.assertIn('<voice>2</voice>', xmlOut)
        v1.id = 234
        xmlOut = self.getXml(m)
        self.assertIn('<voice>234</voice>', xmlOut)
        self.assertIn('<voice>1</voice>', xmlOut)  # is v2 now!
        v2.id = 'hello'
        xmlOut = self.getXml(m)
        self.assertIn('<voice>hello</voice>', xmlOut)

    def testExportNC(self):
        from music21 import harmony

        s = stream.Score()
        p = stream.Part()
        m = stream.Measure()
        m.append(harmony.ChordSymbol('C'))
        m.repeatAppend(note.Note('C'), 4)
        p.append(m)
        m = stream.Measure()
        m.append(harmony.NoChord())
        m.repeatAppend(note.Note('C'), 2)
        m.append(harmony.ChordSymbol('C'))
        m.repeatAppend(note.Note('C'), 2)
        p.append(m)
        s.append(p)

        self.assertEqual(3, self.getXml(s).count(u'<harmony'))
        self.assertEqual(1, self.getXml(s).count(u'<kind '
                                                  u'text="N.C.">none</kind>'))
        self.assertEqual(1, self.getXml(s).count(u'<root-step text="">'))

        s = stream.Score()
        p = stream.Part()
        m = stream.Measure()
        m.append(harmony.NoChord())
        m.repeatAppend(note.Note('C'), 2)
        m.append(harmony.ChordSymbol('C'))
        m.repeatAppend(note.Note('C'), 2)
        p.append(m)
        m = stream.Measure()
        m.append(harmony.NoChord('No Chord'))
        m.repeatAppend(note.Note('C'), 2)
        m.append(harmony.ChordSymbol('C'))
        m.repeatAppend(note.Note('C'), 2)
        p.append(m)
        s.append(p)

        self.assertEqual(1, self.getXml(s).count(u'<kind '
                                                 u'text="N.C.">none</kind>'))
        self.assertEqual(1, self.getXml(s).count(u'<kind '
                                                 u'text="No Chord">none</kind>'))

    def testSetPartsAndRefStreamMeasure(self):
        from music21 import converter
        p = converter.parse("tinynotation: 4/4 c1 d1")
        sx = ScoreExporter(p)  # substreams are measures
        sx.setPartsAndRefStream()
        measuresAtOffsetZero = [m for m in p if m.offset == 0]
        self.assertSequenceEqual(measuresAtOffsetZero, p.elements[:1])

    def testFromScoreNoParts(self):
        s = stream.Score()
        s.append(meter.TimeSignature('1/4'))
        s.append(note.Note())
        s.append(note.Note())
        gex = GeneralObjectExporter(s)
        tree = ET.fromstring(gex.parse().decode('utf-8'))
        # Assert no gaps in stream
        self.assertSequenceEqual(tree.findall('.//forward'), [])

    def testMidiInstrumentNoName(self):
        from music21 import converter, instrument

        i = instrument.Instrument()
        i.midiProgram = 42
        s = converter.parse('tinyNotation: c1')
        s.measure(1).insert(i)
        scex = ScoreExporter(s)

        tree = scex.parse()
        mxScoreInstrument = tree.findall('.//score-instrument')[0]
        mxMidiInstrument = tree.findall('.//midi-instrument')[0]
        self.assertEqual(mxScoreInstrument.get('id'), mxMidiInstrument.get('id'))

    def testMultiDigitEndingsWrite(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        # Relevant barlines:
        # Measure 2, left barline: <ending number="1,2" type="start"/>
        # Measure 2, right barline: <ending number="1,2" type="stop"/>
        # Measure 3, left barline: <ending number="3" type="start"/>
        # Measure 3, right barline: <ending number="3" type="stop"/>
        s = converter.parse(testPrimitive.multiDigitEnding)
        x = self.getET(s)
        endings = x.findall('.//ending')
        self.assertSequenceEqual([e.get('number') for e in endings],
                                ['1,2', '1,2', '3', '3'])

    def testTextExpressionOffset(self):
        '''Transfer element offset after calling getTextExpression().'''
        # https://github.com/cuthbertLab/music21/issues/624
        from music21 import converter, repeat, tempo

        s = converter.parse('tinynotation: 4/4 c1')
        c = repeat.Coda()
        c.useSymbol = False
        f = repeat.Fine()
        mm = tempo.MetronomeMark(text='Langsam')
        s.measure(1).storeAtEnd([c, f, mm])

        tree = self.getET(s)
        for direction in tree.findall('.//direction'):
            self.assertIsNone(direction.find('offset'))


class TestExternal(unittest.TestCase):  # pragma: no cover

    def testBasic(self):
        pass

    def testSimple(self):
        from music21 import corpus  # , converter
        import difflib

        # b = converter.parse(corpus.corpora.CoreCorpus().getWorkList('cpebach')[0],
        #    format='musicxml', forceSource=True)
        b = corpus.parse('cpebach')
        # b.show('text')
        # n = b.flat.notes[0]
        # print(n.expressions)
        # return

        SX = ScoreExporter(b)
        mxScore = SX.parse()

        SX.indent(mxScore)

        sio = io.BytesIO()

        sio.write(SX.xmlHeader())

        et = ElementTree(mxScore)
        et.write(sio, encoding='utf-8', xml_declaration=False)
        v = sio.getvalue()
        sio.close()

        v = v.decode('utf-8')
        # v = v.replace(' />', '/>')  # normalize

        # b2 = converter.parse(v)
        fp = b.write('musicxml')
        print(fp)

        with io.open(fp, encoding='utf-8') as f:
            v2 = f.read()
        differ = list(difflib.ndiff(v.splitlines(), v2.splitlines()))
        for i, l in enumerate(differ):
            if l.startswith('-') or l.startswith('?') or l.startswith('+'):
                if 'id=' in l:
                    continue
                print(l)
                # for j in range(i - 1,i + 1):
                #    print(differ[j])
                # print('------------------')


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)  # , runTest='testSpannersWrite')
