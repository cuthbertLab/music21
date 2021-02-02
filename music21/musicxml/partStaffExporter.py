# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         musicxml/partStaffExporter.py
# Purpose:      Change music21 PartStaff objects to single musicxml parts
#
# Authors:      Jacob Tyler Walls
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2020 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
A mixin to ScoreExporter that includes the capabilities for producing a single
MusicXML `<part>` from multiple music21 PartStaff objects.
'''
from typing import Dict, List, Optional
import unittest
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement

from music21.layout import StaffGroup
from music21 import stream  # for typing
from music21.musicxml import helpers
from music21.musicxml.xmlObjects import MusicXMLExportException

def addStaffTags(measure: Element, staffNumber: int, tagList: Optional[List[str]] = None):
    '''
    For a <measure> tag `measure`, add a <staff> grandchild to any instance of
    a child tag of a type in `tagList`. Raise if a <staff> grandchild already exists.

    >>> from xml.etree.ElementTree import fromstring as El
    >>> from music21.musicxml.partStaffExporter import addStaffTags
    >>> from music21.musicxml.helpers import dump
    >>> elem = El("""
    ...     <measure number="1">
    ...        <note>
    ...          <rest measure="yes" />
    ...          <duration>8</duration>
    ...        </note>
    ...      </measure>"""
    ...     )
    >>> addStaffTags(elem, 2, tagList=['note', 'forward', 'direction', 'harmony'])
    >>> dump(elem)
    <measure number="1">
      <note>
        <rest measure="yes" />
        <duration>8</duration>
        <staff>2</staff>
      </note>
    </measure>

    Raise if a <staff> grandchild is already present:

    >>> addStaffTags(elem, 2, tagList=['note', 'forward', 'direction'])
    Traceback (most recent call last):
    music21.musicxml.xmlObjects.MusicXMLExportException:
        In part (), measure (1): Attempted to create a second <staff> tag

    The function doesn't accept elements other than <measure>:

    >>> addStaffTags(elem.find('note'), 2, tagList=['direction'])
    Traceback (most recent call last):
    music21.musicxml.xmlObjects.MusicXMLExportException:
        addStaffTags() only accepts <measure> tags
    '''
    if measure.tag != 'measure':
        raise MusicXMLExportException('addStaffTags() only accepts <measure> tags')
    for tagName in tagList:
        for tag in measure.findall(tagName):
            if tag.find('staff') is not None:
                e = MusicXMLExportException('Attempted to create a second <staff> tag')
                e.measureNumber = measure.get('number')
                raise e
            mxStaff = Element('staff')
            mxStaff.text = str(staffNumber)
            helpers.insertBeforeElements(tag, mxStaff,
                                                 tagList=['beam', 'notations', 'lyric', 'play',
                                                          'sound'])


class PartStaffExporterMixin:
    def joinPartStaffs(self):
        '''
        Collect <part> elements exported from
        :class:`~music21.stream.PartStaff` objects under a single
        <part> element using <staff> and <voice> subelements.

        Here we load in a simple 2-staff piano piece.  Note that they
        are both elements of the :class:`~music21.stream.PartStaff`
        Stream subclass.

        >>> from music21.musicxml import testPrimitive
        >>> s = converter.parse(testPrimitive.pianoStaff43a)
        >>> s.show('text')
        {0.0} <music21.metadata.Metadata object at 0x107d6a100>
        {0.0} <music21.stream.PartStaff P1-Staff1>
            {0.0} <music21.instrument.Instrument 'P1: MusicXML Part: '>
            {0.0} <music21.stream.Measure 1 offset=0.0>
                {0.0} <music21.clef.TrebleClef>
                {0.0} <music21.key.KeySignature of no sharps or flats>
                {0.0} <music21.meter.TimeSignature 4/4>
                {0.0} <music21.note.Note F>
        {0.0} <music21.stream.PartStaff P1-Staff2>
            {0.0} <music21.instrument.Instrument 'P1: MusicXML Part: '>
            {0.0} <music21.stream.Measure 1 offset=0.0>
                {0.0} <music21.clef.BassClef>
                {0.0} <music21.key.KeySignature of no sharps or flats>
                {0.0} <music21.meter.TimeSignature 4/4>
                {0.0} <music21.note.Note B>
        {0.0} <music21.layout.StaffGroup
                 <music21.stream.PartStaff P1-Staff1><music21.stream.PartStaff P1-Staff2>>

        Now these get joined into a single part in the `parse()` process:

        >>> SX = musicxml.m21ToXml.ScoreExporter(s)
        >>> root = SX.parse()
        >>> parts = root.findall('part')
        >>> len(parts)
        1

        >>> clefs = root.findall('.//clef')
        >>> len(clefs)
        2

        Note that there are exactly two notes (an F and B) in the original score,
        so there are exactly two staff tags in the output.

        >>> staffTags = root.findall('part/measure/note/staff')
        >>> len(staffTags)
        2
        '''
        for group in self.joinableGroups():
            self.addStaffTagsMultiStaffParts(group)
            self.movePartStaffMeasureContents(group)
            self.setEarliestAttributesAndClefsPartStaff(group)
            self.cleanUpSubsequentPartStaffs(group)

    def joinableGroups(self) -> List[StaffGroup]:
        '''
        Returns a list of :class:`~music21.layout.StaffGroup` objects that
        represent PartStaff objects that can be joined together into a single
        MusicXML `<part>`:

        >>> s = stream.Score()

        Group 1: three staves.

        >>> p1a = stream.PartStaff(id='p1a')
        >>> p1a.insert(0, stream.Measure())
        >>> p1b = stream.PartStaff(id='p1b')
        >>> p1b.insert(0, stream.Measure())
        >>> p1c = stream.PartStaff(id='p1c')
        >>> p1c.insert(0, stream.Measure())
        >>> sg1 = layout.StaffGroup([p1a, p1b, p1c])

        Group 2: two staves.

        >>> p2a = stream.PartStaff(id='p2a')
        >>> p2a.insert(0, stream.Measure())
        >>> p2b = stream.PartStaff(id='p2b')
        >>> p2b.insert(0, stream.Measure())
        >>> sg2 = layout.StaffGroup([p2a, p2b])

        Group 3: one staff -- will not be merged.

        >>> p3a = stream.PartStaff(id='p3a')
        >>> p3a.insert(0, stream.Measure())
        >>> sg3 = layout.StaffGroup([p3a])

        Group 4: two staves, but no measures, will not be merged:

        >>> p4a = stream.PartStaff(id='p4a')
        >>> p4b = stream.PartStaff(id='p4b')
        >>> sg4 = layout.StaffGroup([p4a, p4b])

        Group 5: two staves, but no staff group

        >>> p5a = stream.PartStaff(id='p5a')
        >>> p5a.insert(0, stream.Measure())
        >>> p5b = stream.PartStaff(id='p5b')
        >>> p5b.insert(0, stream.Measure())

        Group 6: same as Group 2, just to show that valid groups can come later

        >>> p6a = stream.PartStaff(id='p6a')
        >>> p6a.insert(0, stream.Measure())
        >>> p6b = stream.PartStaff(id='p6b')
        >>> p6b.insert(0, stream.Measure())
        >>> sg6 = layout.StaffGroup([p6a, p6b])

        Group 7: same as Group 6, but with Parts instead of PartStaffs

        >>> p7a = stream.Part(id='p7a')
        >>> p7a.insert(0, stream.Measure())
        >>> p7b = stream.Part(id='p7b')
        >>> p7b.insert(0, stream.Measure())
        >>> sg7 = layout.StaffGroup([p7a, p7b])

        Group 8: encloses same objects as Group 6, just to show it's gracefully ignored

        >>> sg8 = layout.StaffGroup([p6a, p6b])

        >>> for el in (p1a, p1b, p1c, sg1, p2a, p2b, sg2, p3a, sg3,
        ...            p4a, p4b, sg4, p5a, p5b, p6a, p6b, sg6, p7a, p7b, sg7, sg8):
        ...     s.insert(0, el)

        >>> SX = musicxml.m21ToXml.ScoreExporter(s)
        >>> SX.joinableGroups()
        [<music21.layout.StaffGroup <... p1a><... p1b><... p1c>>,
         <music21.layout.StaffGroup <... p2a><... p2b>>,
         <music21.layout.StaffGroup <... p6a><... p6b>>]
        '''
        staffGroups = self.stream.getElementsByClass('StaffGroup')
        joinableGroups: List[StaffGroup] = []
        # Joinable groups must consist of only PartStaffs with Measures
        for sg in staffGroups:
            if len(sg) <= 1:
                continue
            if not all(stream.PartStaff in p.classSet for p in sg):
                continue
            if not all(p.getElementsByClass('Measure') for p in sg):
                continue
            joinableGroups.append(sg)

        # Deduplicate joinable groups (ex: bracket and brace enclose same PartStaffs)
        permutations = set()
        deduplicatedGroups: List[StaffGroup] = []
        for jg in joinableGroups:
            containedParts = tuple(jg)
            if containedParts not in permutations:
                deduplicatedGroups.append(jg)
            permutations.add(containedParts)

        return deduplicatedGroups

    def addStaffTagsMultiStaffParts(self, group: StaffGroup):
        '''
        Create child <staff> tags under each <note>, <direction>, and <forward> element
        in the <part>s being joined.

        Called by :meth:`~music21.musicxml.partStaffExporter.PartStaffExporterMixin.joinPartStaffs`

        >>> from music21.musicxml import testPrimitive
        >>> s = converter.parse(testPrimitive.pianoStaff43a)
        >>> SX = musicxml.m21ToXml.ScoreExporter(s)
        >>> root = SX.parse()
        >>> m1 = root.find('part/measure')
        >>> SX.dump(m1)
        <measure number="1">
        ...
          <note>
            <pitch>
              <step>F</step>
              <octave>4</octave>
            </pitch>
            <duration>40320</duration>
            <voice>1</voice>
            <type>whole</type>
            <staff>1</staff>
          </note>
          <backup>
            <duration>40320</duration>
          </backup>
          <note>
            <pitch>
              <step>B</step>
              <octave>2</octave>
            </pitch>
            <duration>40320</duration>
            <voice>2</voice>
            <type>whole</type>
            <staff>2</staff>
          </note>
        </measure>

        Fails if attempted a second time:

        >>> root = SX.parse()
        Traceback (most recent call last):
        music21.musicxml.xmlObjects.MusicXMLExportException:
            In part (MusicXML Part), measure (1): Attempted to create a second <staff> tag
        '''
        initialPartStaffRoot: Optional[Element] = None
        for i, ps in enumerate(group):
            staffNumber: int = i + 1  # 1-indexed
            thisPartStaffRoot: Element = self.getRootForPartStaff(ps)

            # Create <staff> tags under <note>, <direction>, <forward>, <harmony> tags
            for mxMeasure in thisPartStaffRoot.findall('measure'):
                try:
                    addStaffTags(
                        mxMeasure,
                        staffNumber,
                        tagList=['note', 'direction', 'forward', 'harmony']
                    )
                except MusicXMLExportException as e:
                    e.partName = ps.partName
                    e.measureNumber = mxMeasure.get('number')
                    raise e

            if initialPartStaffRoot is None:
                initialPartStaffRoot = thisPartStaffRoot
                continue

    def movePartStaffMeasureContents(self, group: StaffGroup):
        '''
        For every <part> after the first, find the corresponding measure in the initial
        <part> and merge the contents by inserting all of the contained elements.

        Called by :meth:`~music21.musicxml.partStaffExporter.PartStaffExporterMixin.joinPartStaffs`

        StaffGroup must be a valid one from `joinableGroups()`
        '''

        target = self.getRootForPartStaff(group[0])

        for i, ps in enumerate(group):
            if i == 0:
                continue

            staffNumber: int = i + 1
            source = self.getRootForPartStaff(ps)
            insertions = self.processSubsequentPartStaff(target, source, staffNumber)
            insertionCounter: int = 0
            for originalIdx, elements in insertions.items():
                for element in elements:
                    target.insert(originalIdx + insertionCounter, element)
                    insertionCounter += 1

    def processSubsequentPartStaff(self, target: Element, source: Element, staffNum: int) -> Dict:
        '''
        Move elements from subsequent PartStaff's measures into `target`: the <part>
        element representing the initial PartStaff that will soon represent the merged whole.

        Called by movePartStaffMeasureContents(), which is in turn called by
        :meth:`~music21.musicxml.partStaffExporter.PartStaffExporterMixin.joinPartStaffs`
        '''
        DIVIDER_COMMENT = '========================= Measure [NNN] =========================='
        PLACEHOLDER = '[NNN]'

        sourceMeasures = iter(source.findall('measure'))
        sourceMeasure = None  # Set back to None when disposed of
        insertions = {}

        # Walk through <measures> of the target <part>, compare measure numbers
        for i, targetMeasure in enumerate(target):
            if targetMeasure.tag != 'measure':
                continue
            if sourceMeasure is None:
                try:
                    sourceMeasure = next(sourceMeasures)
                except StopIteration:
                    return insertions  # done processing this PartStaff

            targetNumber = targetMeasure.get('number')
            sourceNumber = sourceMeasure.get('number')

            # 99% of the time we expect identical sets of measure numbers
            # So walking through each should yield the same numbers, whether ints or strings
            if targetNumber == sourceNumber:
                # No gaps found: move all contents
                self.moveMeasureContents(sourceMeasure, targetMeasure, staffNum)
                sourceMeasure = None
                continue

            # Or, gap in measure numbers in the subsequent part: keep iterating through target
            if helpers.measureNumberComesBefore(targetNumber, sourceNumber):
                continue  # sourceMeasure is not None!

            # Or, gap in measure numbers in target: record necessary insertions until gap is closed
            while helpers.measureNumberComesBefore(sourceNumber, targetNumber):
                divider: Element = ET.Comment(DIVIDER_COMMENT.replace(PLACEHOLDER, sourceNumber))
                try:
                    insertions[i] += [divider, sourceMeasure]
                except KeyError:
                    insertions[i] = [divider, sourceMeasure]
                try:
                    sourceMeasure = next(sourceMeasures)
                except StopIteration:
                    return insertions
            raise MusicXMLExportException(
                'joinPartStaffs() was unable to order the measures '
                f'{targetNumber}, {sourceNumber}')  # pragma: no cover

        # Exhaust sourceMeasure and sourceMeasures
        remainingMeasures = list(sourceMeasures)
        if sourceMeasure is not None:
            remainingMeasures.insert(0, sourceMeasure)
        for remaining in remainingMeasures:
            sourceNumber = remaining.get('number')
            divider: Element = ET.Comment(DIVIDER_COMMENT.replace(PLACEHOLDER, sourceNumber))
            try:
                insertions[len(target)] += [divider, remaining]
            except KeyError:
                insertions[len(target)] = [divider, remaining]
        return insertions

    def setEarliestAttributesAndClefsPartStaff(self, group: StaffGroup):
        '''
        Set the <staff> and <clef> information on the earliest measure <attributes> tag
        in the <part> representing the joined PartStaffs.

        Need the earliest <attributes> tag, which may not exist in the merged <part>
        until moved there by movePartStaffMeasureContents() --
        e.g. RH of piano doesn't appear until m. 40, and earlier music for LH needs
        to be merged first in order to find earliest <attributes>.

        Called by :meth:`~music21.musicxml.partStaffExporter.PartStaffExporterMixin.joinPartStaffs`

        >>> from music21.musicxml import testPrimitive
        >>> s = converter.parse(testPrimitive.pianoStaff43a)
        >>> SX = musicxml.m21ToXml.ScoreExporter(s)
        >>> root = SX.parse()
        >>> m1 = root.find('part/measure')
        >>> SX.dump(m1)
        <measure number="1">
          <attributes>
            <divisions>10080</divisions>
            <key>
              <fifths>0</fifths>
              </key>
            <time>
              <beats>4</beats>
              <beat-type>4</beat-type>
            </time>
            <staves>2</staves>
            <clef number="1">
              <sign>G</sign>
              <line>2</line>
            </clef>
            <clef number="2">
              <sign>F</sign>
              <line>4</line>
            </clef>
          </attributes>
        ...
        </measure>
        '''
        initialPartStaffRoot: Optional[Element] = None
        mxAttributes: Optional[Element] = None
        for i, ps in enumerate(group):
            staffNumber: int = i + 1  # 1-indexed

            # Initial PartStaff in group: find earliest mxAttributes, set clef #1 and <staves>
            if initialPartStaffRoot is None:
                initialPartStaffRoot = self.getRootForPartStaff(ps)
                mxAttributes: Element = initialPartStaffRoot.find('measure/attributes')
                clef1: Optional[Element] = mxAttributes.find('clef')
                if clef1 is not None:
                    clef1.set('number', '1')

                mxStaves = Element('staves')
                mxStaves.text = str(len(group))
                helpers.insertBeforeElements(
                    mxAttributes,
                    mxStaves,
                    tagList=['part-symbol', 'instruments', 'clef', 'staff-details',
                                'transpose', 'directive', 'measure-style']
                )

            # Subsequent PartStaffs in group: set additional clefs on mxAttributes
            else:
                thisPartStaffRoot: Element = self.getRootForPartStaff(ps)
                oldClef: Optional[Element] = thisPartStaffRoot.find('measure/attributes/clef')
                if oldClef is not None and mxAttributes is not None:
                    clefsInMxAttributesAlready = mxAttributes.findall('clef')
                    if len(clefsInMxAttributesAlready) >= staffNumber:
                        e = MusicXMLExportException('Attempted to add more clefs than staffs')
                        e.partName = ps.partName
                        raise e

                    # Set initial clef for this staff
                    newClef = Element('clef')
                    newClef.set('number', str(staffNumber))
                    newSign = SubElement(newClef, 'sign')
                    newSign.text = oldClef.find('sign').text
                    newLine = SubElement(newClef, 'line')
                    newLine.text = oldClef.find('line').text
                    helpers.insertBeforeElements(
                        mxAttributes,
                        newClef,
                        tagList=['staff-details', 'transpose', 'directive', 'measure-style']
                    )

    def cleanUpSubsequentPartStaffs(self, group: StaffGroup):
        '''
        Now that the contents of all PartStaffs in `group` have been represented
        by a single :class:`PartExporter`, remove the obsolete `PartExporter`s from
        `self.partExporterList` so that they are not included in the export.

        In addition, remove any obsolete `PartStaff` from the `StaffGroup`
        (in the deepcopied stream used for exporting) to ensure <part-group type="stop" />
        is written.

        Called by :meth:`~music21.musicxml.partStaffExporter.PartStaffExporterMixin.joinPartStaffs`

        >>> from music21.musicxml import testPrimitive
        >>> s = converter.parse(testPrimitive.pianoStaff43a)
        >>> SX = musicxml.m21ToXml.ScoreExporter(s)
        >>> SX.scorePreliminaries()
        >>> SX.parsePartlikeScore()
        >>> len(SX.partExporterList)
        2
        >>> SX.postPartProcess()
        >>> len(SX.partExporterList)
        1
        >>> partGroupStop = SX.xmlRoot.findall('.//part-group')[1]
        >>> SX.dump(partGroupStop)
        <part-group number="1" type="stop" />
        '''
        for ps in group[1:]:
            partStaffRoot: Element = self.getRootForPartStaff(ps)
            # Remove PartStaff from export list
            # noinspection PyAttributeOutsideInit
            self.partExporterList = [pex for pex in self.partExporterList
                                        if pex.xmlRoot != partStaffRoot]
            # Replace PartStaff in StaffGroup -- ensures <part-group number="1" type="stop" />
            group.replaceSpannedElement(ps, group.getFirst())

    @staticmethod
    def moveMeasureContents(measure: Element, otherMeasure: Element, staffNumber: int):
        # noinspection PyShadowingNames
        '''
        Move the child elements of `measure` into `otherMeasure`;
        create voice numbers if needed;
        bump voice numbers if they conflict;
        account for <backup> and <forward> tags;
        skip <print> tags;
        set "number" on midmeasure clef changes;
        replace existing <barline> tags.

        >>> from xml.etree.ElementTree import fromstring as El
        >>> measure = El('<measure><note /></measure>')
        >>> otherMeasure = El('<measure><note /></measure>')
        >>> SX = musicxml.m21ToXml.ScoreExporter
        >>> SX.moveMeasureContents(measure, otherMeasure, 2)
        >>> SX().dump(otherMeasure)
        <measure>
          <note>
            <voice>1</voice>
          </note>
          <note>
            <voice>2</voice>
          </note>
        </measure>

        >>> SX.moveMeasureContents(El('<junk />'), otherMeasure, 2)
        Traceback (most recent call last):
        music21.musicxml.xmlObjects.MusicXMLExportException:
            moveMeasureContents() called on <Element 'junk'...

        Only one <barline> should be exported per merged measure:

        >>> from music21.musicxml import testPrimitive
        >>> s = converter.parse(testPrimitive.mixedVoices1a)
        >>> SX = musicxml.m21ToXml.ScoreExporter(s)
        >>> root = SX.parse()
        >>> root.findall('part/measure/barline')
        [<Element 'barline' at 0x...]
        '''
        if measure.tag != 'measure' or otherMeasure.tag != 'measure':
            raise MusicXMLExportException(
                f'moveMeasureContents() called on {measure} and {otherMeasure} (not measures).')
        maxVoices: int = 0
        otherMeasureLackedVoice: bool = False

        for voice in otherMeasure.findall('*/voice'):
            maxVoices = max(maxVoices, int(voice.text))

        if maxVoices == 0:
            otherMeasureLackedVoice = True
            for elem in otherMeasure.findall('note'):
                voice = Element('voice')
                voice.text = '1'
                helpers.insertBeforeElements(
                    elem,
                    voice,
                    tagList=[
                        'type', 'dot', 'accidental', 'time-modification',
                        'stem', 'notehead', 'notehead-text', 'staff',
                    ]
                )
            maxVoices = 1

        # Create <backup>
        amountToBackup: int = 0
        for dur in otherMeasure.findall('note/duration'):
            amountToBackup += int(dur.text)
        for dur in otherMeasure.findall('forward/duration'):
            amountToBackup += int(dur.text)
        for backupDur in otherMeasure.findall('backup/duration'):
            amountToBackup -= int(backupDur.text)
        if amountToBackup:
            mxBackup = Element('backup')
            mxDuration = SubElement(mxBackup, 'duration')
            mxDuration.text = str(amountToBackup)
            otherMeasure.append(mxBackup)

        # Move elements
        for elem in measure.findall('*'):
            # Skip elements that already exist in otherMeasure
            if elem.tag == 'print':
                continue
            if elem.tag == 'attributes':
                if elem.findall('divisions'):
                    # This is likely the initial mxAttributes
                    continue
                for midMeasureClef in elem.findall('clef'):
                    midMeasureClef.set('number', str(staffNumber))
            if elem.tag == 'barline':
                # Remove existing <barline>, if any
                for existingBarline in otherMeasure.findall('barline'):
                    otherMeasure.remove(existingBarline)
            if elem.tag == 'note':
                voice = elem.find('voice')
                if voice is not None:
                    if otherMeasureLackedVoice:
                        # otherMeasure assigned voice 1; Bump voice number here
                        voice.text = str(int(voice.text) + 1)
                    else:
                        pass  # No need to alter existing voice numbers
                else:
                    voice = Element('voice')
                    voice.text = str(maxVoices + 1)
                    helpers.insertBeforeElements(
                        elem,
                        voice,
                        tagList=[
                            'type', 'dot', 'accidental', 'time-modification',
                            'stem', 'notehead', 'notehead-text', 'staff'
                        ]
                    )
            # Append to otherMeasure
            otherMeasure.append(elem)

    def getRootForPartStaff(self, partStaff: stream.PartStaff) -> Element:
        '''
        Look up the <part> Element being used to represent the music21 `partStaff`.

        >>> from music21.musicxml import testPrimitive
        >>> s = converter.parse(testPrimitive.pianoStaff43a)
        >>> SX = musicxml.m21ToXml.ScoreExporter(s)
        >>> SX.scorePreliminaries()
        >>> SX.parsePartlikeScore()
        >>> SX.getRootForPartStaff(s.parts[0])
        <Element 'part' at 0x...

        >>> other = stream.PartStaff()
        >>> other.id = 'unrelated'
        >>> SX.getRootForPartStaff(other)
        Traceback (most recent call last):
        music21.musicxml.xmlObjects.MusicXMLExportException:
            <music21.stream.PartStaff unrelated> not found in self.partExporterList
        '''
        for pex in self.partExporterList:
            if partStaff is pex.stream:
                return pex.xmlRoot

        # now try derivations:
        for pex in self.partExporterList:
            for derived in pex.stream.derivation.chain():
                if derived is partStaff:
                    return pex.xmlRoot

        # now just match on id:
        for pex in self.partExporterList:
            if partStaff.id == pex.stream.id:
                return pex.xmlRoot

        for pex in self.partExporterList:
            for derived in pex.stream.derivation.chain():
                if partStaff.id == derived.id:
                    return pex.xmlRoot

        raise MusicXMLExportException(
            f'{partStaff} not found in self.partExporterList')


class Test(unittest.TestCase):

    def getXml(self, obj):
        from music21.musicxml.m21ToXml import GeneralObjectExporter

        gex = GeneralObjectExporter()
        bytesOut = gex.parse(obj)
        bytesOutUnicode = bytesOut.decode('utf-8')
        return bytesOutUnicode

    def getET(self, obj):
        from music21.musicxml.m21ToXml import ScoreExporter

        SX = ScoreExporter(obj)
        mxScore = SX.parse()
        helpers.indent(mxScore)
        return mxScore

    def testJoinPartStaffsA(self):
        '''
        Measure 1, staff 2 contains mid-measure treble clef in LH
        '''
        from music21 import corpus
        sch = corpus.parse('schoenberg/opus19', 2)
        root = self.getET(sch)
        # helpers.dump(root)

        m1 = root.find('part/measure')
        clefs = m1.findall('attributes/clef')
        self.assertEqual(len(clefs), 3)
        self.assertEqual(clefs[0].get('number'), '1')
        self.assertEqual(clefs[1].get('number'), '2')
        self.assertEqual(clefs[2].get('number'), '2')
        self.assertEqual(clefs[2].find('sign').text, 'G')

    def testJoinPartStaffsB(self):
        '''
        Gapful first PartStaff, ensure <backup> in second PartStaff correct
        '''
        from music21 import layout
        from music21 import note
        s = stream.Score()
        ps1 = stream.PartStaff()
        ps1.insert(0, note.Note())
        # Gap
        ps1.insert(3, note.Note())
        ps2 = stream.PartStaff()
        ps2.insert(0, note.Note())
        s.append(ps1)
        s.append(ps2)
        s.insert(0, layout.StaffGroup([ps1, ps2]))
        root = self.getET(s)
        notes = root.findall('.//note')
        forward = root.find('.//forward')
        backup = root.find('.//backup')
        amountToBackup = (
            int(notes[0].find('duration').text)
            + int(forward.find('duration').text)
            + int(notes[1].find('duration').text)
        )
        self.assertEqual(int(backup.find('duration').text), amountToBackup)

    def testJoinPartStaffsC(self):
        '''
        First PartStaff longer than second
        '''
        from music21 import layout
        from music21 import note
        s = stream.Score()
        ps1 = stream.PartStaff()
        ps1.repeatAppend(note.Note(), 8)
        ps1.makeNotation(inPlace=True)  # makeNotation to freeze notation
        s.insert(0, ps1)
        ps2 = stream.PartStaff()
        ps2.repeatAppend(note.Note(), 4)
        ps2.makeNotation(inPlace=True)  # makeNotation to freeze notation
        s.insert(0, ps2)
        s.insert(0, layout.StaffGroup([ps1, ps2]))
        root = self.getET(s)
        measures = root.findall('.//measure')
        notes = root.findall('.//note')
        self.assertEqual(len(measures), 2)
        self.assertEqual(len(notes), 12)

    def testJoinPartStaffsD(self):
        '''
        Same example as testJoinPartStaffsC but switch the hands:
        second PartStaff longer than first
        '''
        from music21 import layout
        from music21 import note
        s = stream.Score()
        ps1 = stream.PartStaff()
        ps1.repeatAppend(note.Note(), 8)
        ps1.makeNotation(inPlace=True)  # makeNotation to freeze notation
        ps2 = stream.PartStaff()
        ps2.repeatAppend(note.Note(), 4)
        ps2.makeNotation(inPlace=True)  # makeNotation to freeze notation
        s.insert(0, ps2)
        s.insert(0, ps1)
        s.insert(0, layout.StaffGroup([ps2, ps1]))
        root = self.getET(s)
        measures = root.findall('.//measure')
        notes = root.findall('.//note')
        self.assertEqual(len(measures), 2)
        self.assertEqual(len(notes), 12)

    def testJoinPartStaffsE(self):
        '''
        Measure numbers existing only in certain PartStaffs: don't collapse together
        '''
        from music21 import corpus
        from music21 import layout
        sch = corpus.parse('schoenberg/opus19', 2)

        s = stream.Score()
        ps1 = stream.PartStaff()
        ps2 = stream.PartStaff()
        s.append(ps1)
        s.append(ps2)
        s.insert(0, layout.StaffGroup([ps1, ps2]))
        m1 = sch.parts[0].measure(1)  # RH
        m2 = sch.parts[1].measure(2)  # LH
        m3 = sch.parts[0].measure(3)  # RH
        ps1.append(m1)
        ps1.append(m3)
        ps2.insert(m1.offset, m2)
        root = self.getET(s)
        m1tag, m2tag, m3tag = root.findall('part/measure')
        self.assertEqual({staff.text for staff in m1tag.findall('note/staff')}, {'1'})
        self.assertEqual({staff.text for staff in m2tag.findall('note/staff')}, {'2'})
        self.assertEqual({staff.text for staff in m3tag.findall('note/staff')}, {'1'})



if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
