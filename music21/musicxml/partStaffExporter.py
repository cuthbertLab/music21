# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         musicxml/partStaffExporter.py
# Purpose:      Change music21 PartStaff objects to single musicxml parts
#
# Authors:      Jacob Tyler Walls
#               Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2020-22 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
A mixin to ScoreExporter that includes the capabilities for producing a single
MusicXML `<part>` from multiple music21 `PartStaff` objects.
'''
from __future__ import annotations

import typing as t
import unittest
import warnings
from xml.etree.ElementTree import Element, SubElement, Comment

from music21.common.misc import flattenList
from music21.common.types import M21ObjType
from music21.key import KeySignature
from music21.layout import StaffGroup
from music21.meter import TimeSignature
from music21 import stream

from music21.musicxml import helpers
from music21.musicxml.xmlObjects import MusicXMLExportException, MusicXMLWarning


def addStaffTags(
    measure: Element,
    staffNumber: int,
    tagList: list[str]
):
    '''
    For a <measure> tag `measure`, add a <staff> grandchild to any instance of
    a child tag of a type in `tagList`.

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
                e.measureNumber = m if (m := measure.get('number')) else ''
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
        # starting with v.7, self.groupsToJoin is already set earlier,
        # but check to be safe
        if not self.groupsToJoin:
            # this is done in the non-mixin class.
            # noinspection PyAttributeOutsideInit
            self.groupsToJoin = self.joinableGroups()
        for group in self.groupsToJoin:
            self.addStaffTagsMultiStaffParts(group)
            self.movePartStaffMeasureContents(group)
            self.setEarliestAttributesAndClefsPartStaff(group)
            self.cleanUpSubsequentPartStaffs(group)

    def joinableGroups(self) -> list[StaffGroup]:
        # noinspection PyShadowingNames
        '''
        Returns a list of :class:`~music21.layout.StaffGroup` objects that
        represent :class:`~music21.stream.base.PartStaff` objects that can be
        joined into a single MusicXML `<part>`, so long as there exists a
        `PartExporter` for it in `ScoreExporter.partExporterList`.

        Sets :attr:`~music21.musicxml.m21ToXml.PartExporter.previousPartStaffInGroup`.

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
        >>> SX.scorePreliminaries()
        >>> SX.parsePartlikeScore()  # populate .partExporterList
        >>> SX.joinableGroups()
        [<music21.layout.StaffGroup <... p1a><... p1b><... p1c>>,
         <music21.layout.StaffGroup <... p2a><... p2b>>,
         <music21.layout.StaffGroup <... p6a><... p6b>>]
        '''
        if t.TYPE_CHECKING:
            from music21.musicxml.m21ToXml import XMLExporterBase
            assert isinstance(self, XMLExporterBase)
        staffGroups = list(s.getElementsByClass(StaffGroup)) if (s := self.stream) else []
        joinableGroups: list[StaffGroup] = []
        # Joinable groups must consist of only PartStaffs with Measures
        # and exist in self.stream
        for sg in staffGroups:
            if len(sg) <= 1:
                continue
            if not all(stream.PartStaff in p.classSet for p in sg):
                continue
            if not all(p.getElementsByClass(stream.Measure) for p in sg):
                continue
            try:
                for p in sg:
                    self.getRootForPartStaff(p)
            except MusicXMLExportException:
                continue
            joinableGroups.append(sg)

        # Deduplicate joinable groups (ex: bracket and brace enclose same PartStaffs)
        permutations = set()
        deduplicatedGroups: list[StaffGroup] = []
        for jg in joinableGroups:
            containedParts = tuple(jg)
            if containedParts not in permutations:
                deduplicatedGroups.append(jg)
            permutations.add(containedParts)

        # But forbid overlapping, spaghetti StaffGroups
        joinable_components_list = flattenList(deduplicatedGroups)
        if len(set(joinable_components_list)) != len(joinable_components_list):
            warnings.warn(
                MusicXMLWarning('Got overlapping StaffGroups; will not merge ANY groups.'))
            return []

        # Finally, store a reference to earlier siblings (if any) on PartExporters
        for group in deduplicatedGroups:
            prior_part_staff = None
            for part_staff in group:
                for part_exporter in self.partExporterList:
                    if part_exporter.stream is not part_staff:
                        continue
                    part_exporter.previousPartStaffInGroup = prior_part_staff
                    prior_part_staff = part_staff
                    break

        return deduplicatedGroups

    def addStaffTagsMultiStaffParts(self, group: StaffGroup):
        '''
        Create child <staff> tags under each <note>, <direction>, and <forward> element
        in the <part>s being joined.

        Called by :meth:`joinPartStaffs`.

        >>> from music21.musicxml import testPrimitive
        >>> s = converter.parse(testPrimitive.pianoStaff43a)
        >>> SX = musicxml.m21ToXml.ScoreExporter(s)
        >>> root = SX.parse()
        >>> m1 = root.find('part/measure')
        >>> SX.dump(m1)
        <measure implicit="no" number="1">
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
        '''
        initialPartStaffRoot: Element | None = None
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
                    e.measureNumber = m_num if (m_num := mxMeasure.get('number')) else ''
                    raise e

            if initialPartStaffRoot is None:
                initialPartStaffRoot = thisPartStaffRoot
                continue

    def movePartStaffMeasureContents(self, group: StaffGroup):
        '''
        For every <part> after the first, find the corresponding measure in the initial
        <part> and merge the contents by inserting all contained elements.

        Called by :meth:`joinPartStaffs`

        StaffGroup must be a valid one from
        :meth:`joinableGroups`.
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

    def processSubsequentPartStaff(self,
                                   target: Element,
                                   source: Element,
                                   staffNum: int
                                   ) -> dict[int, list[Element]]:
        '''
        Move elements from subsequent PartStaff's measures into `target`: the <part>
        element representing the initial PartStaff that will soon represent the merged whole.

        Called by
        :meth:`movePartStaffMeasureContents`,
        which is in turn called by
        :meth:`joinPartStaffs`.
        '''
        DIVIDER_COMMENT = '========================= Measure [NNN] =========================='
        PLACEHOLDER = '[NNN]'

        def makeDivider(inner_sourceNumber: int | str) -> Element:
            return Comment(DIVIDER_COMMENT.replace(PLACEHOLDER, str(inner_sourceNumber)))

        sourceMeasures = iter(source.findall('measure'))
        sourceMeasure = None  # Set back to None when disposed of
        insertions: dict[int, list[Element]] = {}

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
            if (sourceNumber is not None
                   and targetNumber is not None
                   and helpers.measureNumberComesBefore(targetNumber, sourceNumber)):
                continue  # sourceMeasure is not None!

            # Or, gap in measure numbers in target: record necessary insertions until gap is closed
            while (sourceNumber is not None
                   and targetNumber is not None
                   and helpers.measureNumberComesBefore(sourceNumber, targetNumber)):
                if i not in insertions:
                    insertions[i] = []
                if t.TYPE_CHECKING:
                    assert isinstance(sourceNumber, str)
                insertions[i] += [makeDivider(sourceNumber), sourceMeasure]
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
            if sourceNumber is None:
                continue

            idx = len(target)
            if idx not in insertions:
                insertions[idx] = []
            if t.TYPE_CHECKING:
                assert isinstance(sourceNumber, str)

            insertions[idx] += [makeDivider(sourceNumber), remaining]
        return insertions

    def setEarliestAttributesAndClefsPartStaff(self, group: StaffGroup):
        '''
        Set the <staff>, <key>, <time>, and <clef> information on the earliest
        measure <attributes> tag in the <part> representing the joined PartStaffs.

        Need the earliest <attributes> tag, which may not exist in the merged <part>
        until moved there by movePartStaffMeasureContents() --
        e.g. RH of piano doesn't appear until m. 40, and earlier music for LH needs
        to be merged first in order to find earliest <attributes>.

        Called by :meth:`joinPartStaffs`

        Multiple keys:

        >>> from music21.musicxml import testPrimitive
        >>> xmlDir = common.getSourceFilePath() / 'musicxml' / 'lilypondTestSuite'
        >>> s = converter.parse(xmlDir / '43b-MultiStaff-DifferentKeys.xml')
        >>> SX = musicxml.m21ToXml.ScoreExporter(s)
        >>> root = SX.parse()
        >>> m1 = root.find('part/measure')
        >>> SX.dump(m1)
        <measure implicit="no" number="1">
          <attributes>
            <divisions>10080</divisions>
            <key number="1">
              <fifths>0</fifths>
            </key>
            <key number="2">
              <fifths>2</fifths>
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

        Multiple meters (not very well supported by MusicXML readers):

        >>> from music21.musicxml import testPrimitive
        >>> s = converter.parse(testPrimitive.pianoStaffPolymeterWithClefOctaveChange)
        >>> SX = musicxml.m21ToXml.ScoreExporter(s)
        >>> root = SX.parse()
        >>> m1 = root.find('part/measure')
        >>> SX.dump(m1)
        <measure implicit="no" number="1">
            <attributes>
            <divisions>10080</divisions>
            <key>
                <fifths>0</fifths>
            </key>
            <time number="1">
                <beats>4</beats>
                <beat-type>4</beat-type>
            </time>
            <time number="2">
                <beats>2</beats>
                <beat-type>2</beat-type>
            </time>
            <staves>2</staves>
            <clef number="1">
                <sign>G</sign>
                <line>2</line>
            </clef>
            <clef number="2">
                <sign>G</sign>
                <line>2</line>
                <clef-octave-change>-1</clef-octave-change>
            </clef>
            </attributes>
        ...
        </measure>
        '''

        def isMultiAttribute(m21Class: type[M21ObjType],
                             comparison: str = '__eq__') -> bool:
            '''
            Return True if any first instance of m21Class in any subsequent staff
            in this StaffGroup does not compare to the first instance of that class
            in the earliest staff where found (not necessarily the first) using `comparison`.
            '''
            initialM21Instance: M21ObjType | None = None
            # noinspection PyShadowingNames
            for ps in group:  # ps okay to reuse.
                if initialM21Instance is None:
                    initialM21Instance = ps.recurse().getElementsByClass(m21Class).first()
                else:
                    firstInstanceSubsequentStaff = ps.recurse().getElementsByClass(m21Class).first()
                    if firstInstanceSubsequentStaff is not None:
                        comparisonWrapper = getattr(firstInstanceSubsequentStaff, comparison)
                        if not comparisonWrapper(initialM21Instance):
                            return True
                        # else, keep looking: 3+ staves
                    # else, keep looking: 3+ staves
            return False

        multiKey: bool = isMultiAttribute(KeySignature)
        multiMeter: bool = isMultiAttribute(TimeSignature, comparison='ratioEqual')

        initialPartStaffRoot: Element | None = None
        mxAttributes: Element | None = None
        for i, ps in enumerate(group):
            staffNumber: int = i + 1  # 1-indexed

            # Initial PartStaff in group: find earliest mxAttributes, set clef #1 and <staves>
            if initialPartStaffRoot is None:
                initialPartStaffRoot = self.getRootForPartStaff(ps)
                mxAttributes = initialPartStaffRoot.find('measure/attributes')
                clef1: Element | None = mxAttributes.find('clef') if mxAttributes else None
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

                if multiKey and mxAttributes is not None:
                    key1 = mxAttributes.find('key')
                    if key1:
                        key1.set('number', '1')
                if multiMeter and mxAttributes is not None:
                    meter1 = mxAttributes.find('time')
                    if meter1:
                        meter1.set('number', '1')

            # Subsequent PartStaffs in group: set additional clefs on mxAttributes
            else:
                thisPartStaffRoot: Element = self.getRootForPartStaff(ps)
                oldClef: Element | None = thisPartStaffRoot.find('measure/attributes/clef')
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
                    newSign.text = (oldClefSign.text
                                    if (oldClefSign := oldClef.find('sign')) is not None
                                    else None)
                    newLine = SubElement(newClef, 'line')
                    newLine.text = (foundLine.text
                                    if (foundLine := oldClef.find('line')) is not None
                                    else '')
                    foundOctave = oldClef.find('clef-octave-change')
                    if foundOctave is not None:
                        newOctave = SubElement(newClef, 'clef-octave-change')
                        newOctave.text = foundOctave.text
                    helpers.insertBeforeElements(
                        mxAttributes,
                        newClef,
                        tagList=['staff-details', 'transpose', 'directive', 'measure-style']
                    )

                if multiMeter:
                    oldMeter: Element | None = thisPartStaffRoot.find(
                        'measure/attributes/time'
                    )
                    if oldMeter:
                        oldMeter.set('number', str(staffNumber))
                        helpers.insertBeforeElements(
                            mxAttributes,
                            oldMeter,
                            tagList=['staves']
                        )
                if multiKey:
                    oldKey: Element | None = thisPartStaffRoot.find('measure/attributes/key')
                    if oldKey:
                        oldKey.set('number', str(staffNumber))
                        helpers.insertBeforeElements(
                            mxAttributes,
                            oldKey,
                            tagList=['time', 'staves']
                        )

    def cleanUpSubsequentPartStaffs(self, group: StaffGroup):
        '''
        Now that the contents of all PartStaffs in `group` have been represented
        by a single :class:`~music21.musicxml.m21ToXml.PartExporter`, remove any
        obsolete `PartExporter` from `self.partExporterList`.

        Called by :meth:`joinPartStaffs`

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
        '''
        for ps in group[1:]:
            partStaffRoot: Element = self.getRootForPartStaff(ps)
            # Remove PartStaff from export list
            # noinspection PyAttributeOutsideInit
            self.partExporterList: list[music21.musicxml.m21ToXml.PartExporter] = [
                pex for pex in self.partExporterList if pex.xmlRoot != partStaffRoot
            ]

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

        for other_voice in otherMeasure.findall('*/voice'):
            otherVoiceText = other_voice.text
            if otherVoiceText is not None:
                maxVoices = max(maxVoices, int(otherVoiceText))

        if maxVoices == 0:
            otherMeasureLackedVoice = True
            for elem in otherMeasure.findall('note'):
                new_voice = Element('voice')
                new_voice.text = '1'
                helpers.insertBeforeElements(
                    elem,
                    new_voice,
                    tagList=[
                        'type', 'dot', 'accidental', 'time-modification',
                        'stem', 'notehead', 'notehead-text', 'staff',
                    ]
                )
            maxVoices = 1

        # Create <backup>
        amountToBackup: int = 0
        for note in otherMeasure.findall('note'):
            if note.find('chord') is not None:
                continue
            dur = note.find('duration')
            if dur is None:
                continue
            backupDurText = dur.text
            if backupDurText is not None:
                amountToBackup += int(backupDurText)
        for dur in otherMeasure.findall('forward/duration'):
            forwardDurText = dur.text
            if forwardDurText is not None:
                amountToBackup += int(forwardDurText)
        for backupDur in otherMeasure.findall('backup/duration'):
            backupDurText = backupDur.text
            if backupDurText is not None:
                amountToBackup -= int(backupDurText)
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
                # Remove existing <barline> with the same direction, if any
                thisBarlineLocation = elem.get('location')
                for existingBarline in otherMeasure.findall('barline'):
                    if existingBarline.get('location') == thisBarlineLocation:
                        otherMeasure.remove(existingBarline)
            if elem.tag == 'note':
                voice = elem.find('voice')
                if voice is not None:
                    if otherMeasureLackedVoice and voice.text:
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
            if partStaff is pex.stream and pex.xmlRoot is not None:
                return pex.xmlRoot

        # now try derivations:
        for pex in self.partExporterList:
            for derived in pex.stream.derivation.chain():
                if derived is partStaff and pex.xmlRoot is not None:
                    return pex.xmlRoot

        # now just match on id:
        for pex in self.partExporterList:
            if partStaff.id == pex.stream.id and pex.xmlRoot is not None:
                return pex.xmlRoot

        for pex in self.partExporterList:
            for derived in pex.stream.derivation.chain():
                if partStaff.id == derived.id and pex.xmlRoot is not None:
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

        # since there are no voices in either PartStaff, the voice number of each note
        # should be the same as the staff number.
        for mxNote in notes:
            self.assertEqual(mxNote.find('voice').text, mxNote.find('staff').text)

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
        # from music21.musicxml.helpers import dump
        # dump(root)
        self.assertEqual(len(measures), 2)
        self.assertEqual(len(notes), 12)

    def testJoinPartStaffsD2(self):
        '''
        Add measures and voices and check for unique voice numbers across the StaffGroup.
        '''
        from music21 import layout
        from music21 import note
        s = stream.Score()
        ps1 = stream.PartStaff()
        m1 = stream.Measure()
        ps1.insert(0, m1)
        v1 = stream.Voice()
        v2 = stream.Voice()
        m1.insert(0, v1)
        m1.insert(0, v2)
        v1.repeatAppend(note.Note('C4'), 4)
        v2.repeatAppend(note.Note('E4'), 4)
        ps1.makeNotation(inPlace=True)  # makeNotation to freeze notation

        ps2 = stream.PartStaff()
        m2 = stream.Measure()
        ps2.insert(0, m2)
        v3 = stream.Voice()
        v4 = stream.Voice()
        m2.insert(0, v3)
        m2.insert(0, v4)
        v3.repeatAppend(note.Note('C3'), 4)
        v4.repeatAppend(note.Note('G3'), 4)
        ps2.makeNotation(inPlace=True)  # makeNotation to freeze notation

        s.insert(0, ps2)
        s.insert(0, ps1)
        s.insert(0, layout.StaffGroup([ps1, ps2]))
        root = self.getET(s)
        measures = root.findall('.//measure')
        notes = root.findall('.//note')
        # from music21.musicxml.helpers import dump
        # dump(root)
        self.assertEqual(len(measures), 1)
        self.assertEqual(len(notes), 16)

        # check those voice and staff numbers
        for mxNote in notes:
            mxPitch = mxNote.find('pitch')
            if mxPitch.find('step').text == 'C' and mxPitch.find('octave').text == '4':
                self.assertEqual(mxNote.find('voice').text, '1')
                self.assertEqual(mxNote.find('staff').text, '1')
            elif mxPitch.find('step').text == 'E' and mxPitch.find('octave').text == '4':
                self.assertEqual(mxNote.find('voice').text, '2')
                self.assertEqual(mxNote.find('staff').text, '1')
            elif mxPitch.find('step').text == 'C' and mxPitch.find('octave').text == '3':
                self.assertEqual(mxNote.find('voice').text, '3')
                self.assertEqual(mxNote.find('staff').text, '2')
            elif mxPitch.find('step').text == 'G' and mxPitch.find('octave').text == '3':
                self.assertEqual(mxNote.find('voice').text, '4')
                self.assertEqual(mxNote.find('staff').text, '2')

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

    def testJoinPartStaffsF(self):
        '''
        Flattening the score will leave StaffGroup spanners with parts no longer in the stream.
        '''
        from music21 import corpus
        from music21 import musicxml
        sch = corpus.parse('schoenberg/opus19', 2)

        # NB: Using ScoreExporter directly is an advanced use case:
        # does not run makeNotation(), so here GeneralObjectExporter is used first
        gex = musicxml.m21ToXml.GeneralObjectExporter()
        with self.assertWarnsRegex(Warning, 'not well-formed'):
            # No part layer. Measure directly under Score.
            obj = gex.fromGeneralObject(sch.flatten())
        SX = musicxml.m21ToXml.ScoreExporter(obj)
        SX.scorePreliminaries()
        SX.parseFlatScore()
        # Previously, an exception was raised by getRootForPartStaff()
        SX.joinPartStaffs()

    def testJoinPartStaffsG(self):
        '''
        A derived score should still have joinable groups.
        '''
        from music21 import corpus
        from music21 import musicxml
        s = corpus.parse('demos/two-parts')

        m1 = s.measure(1)
        self.assertIn('Score', m1.classes)
        SX = musicxml.m21ToXml.ScoreExporter(m1)
        SX.scorePreliminaries()
        SX.parsePartlikeScore()
        self.assertEqual(len(SX.joinableGroups()), 1)

    def testJoinPartStaffsH(self):
        '''
        Overlapping PartStaffs cannot be guaranteed to export correctly,
        so they fall back to the old export paradigm (no joinable groups).
        '''
        from music21 import musicxml

        ps1 = stream.PartStaff(stream.Measure())
        ps2 = stream.PartStaff(stream.Measure())
        ps3 = stream.PartStaff(stream.Measure())
        sg1 = StaffGroup([ps1, ps2])
        sg2 = StaffGroup([ps1, ps3])
        s = stream.Score([ps1, ps2, ps3, sg1, sg2])

        SX = musicxml.m21ToXml.ScoreExporter(s)
        SX.scorePreliminaries()
        with self.assertWarns(MusicXMLWarning):
            SX.parsePartlikeScore()
            self.assertEqual(SX.joinableGroups(), [])

    def testJoinPartStaffsAgain(self):
        '''
        Regression test for side effects on the stream passed to ScoreExporter
        preventing it from being written out again.
        '''
        from music21 import corpus
        from music21.musicxml.m21ToXml import ScoreExporter
        b = corpus.parse('cpebach')
        SX = ScoreExporter(b)
        SX.parse()
        SX.parse()

    def testMeterChanges(self):
        from music21 import layout
        from music21 import meter
        from music21 import note

        ps1 = stream.PartStaff()
        ps2 = stream.PartStaff()
        sg = layout.StaffGroup([ps1, ps2])
        s = stream.Score([ps1, ps2, sg])
        for ps in ps1, ps2:
            ps.insert(0, meter.TimeSignature('3/1'))
            ps.repeatAppend(note.Note(type='whole'), 6)
            ps.makeNotation(inPlace=True)  # makes measures
            ps[stream.Measure][1].insert(meter.TimeSignature('4/1'))

        root = self.getET(s)
        # Just two <attributes> tags, a 3/1 in measure 1 and a 4/1 in measure 2
        self.assertEqual(len(root.findall('part/measure/attributes/time')), 2)

        # Edge cases -- no expectation of correctness, just don't crash
        ps1[stream.Measure].last().number = 0  # was measure 2
        root = self.getET(s)
        self.assertEqual(len(root.findall('part/measure/attributes/time')), 3)

    def testBackupAmount(self):
        '''
        Regression test for chord members causing too-large backup amounts.
        '''
        from music21 import chord
        from music21 import defaults
        from music21 import layout

        ps1 = stream.PartStaff(chord.Chord('C E G'))
        ps2 = stream.PartStaff(chord.Chord('D F A'))
        sg = layout.StaffGroup([ps1, ps2])
        s = stream.Score([sg, ps1, ps2])

        root = self.getET(s)
        self.assertEqual(
            root.findall('part/measure/backup/duration')[0].text,
            str(defaults.divisionsPerQuarter)
        )

    def testForwardRepeatMarks(self):
        '''
        Regression test for losing forward repeat marks.
        '''
        from music21 import bar
        from music21 import layout
        from music21 import note

        measureRH = stream.Measure(
            [bar.Repeat(direction='start'), note.Note(type='whole')])
        measureRH.storeAtEnd(bar.Repeat(direction='end'))
        measureLH = stream.Measure(
            [bar.Repeat(direction='start'), note.Note(type='whole')])
        measureLH.storeAtEnd(bar.Repeat(direction='end'))

        ps1 = stream.PartStaff(measureRH)
        ps2 = stream.PartStaff(measureLH)
        sg = layout.StaffGroup([ps1, ps2])
        s = stream.Score([sg, ps1, ps2])

        root = self.getET(s)
        self.assertEqual(
            [r.get('direction') for r in root.findall('.//repeat')],
            ['forward', 'backward']
        )


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
