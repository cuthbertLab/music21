# ------------------------------------------------------------------------------
# Name:         musicxml/xmlSoundParser.py
# Purpose:      Translate the <sound> tag to music21
#
# Authors:      Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2016-26 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Functions that convert the <sound> tag to the many music21
objects that this tag might represent.

Pulled out because xmlToM21 got way too big. These are plain functions
(not methods/a mixin) that take the owning :class:`MeasureParser` as their first
argument (like in :mod:`~music21.stream.makeNotation`).
'''
from __future__ import annotations

import typing as t
import unittest
import xml.etree.ElementTree as ET
import warnings

from music21 import common
from music21 import duration
from music21 import tempo

from music21.musicxml import helpers

if t.TYPE_CHECKING:
    from music21.musicxml.xmlToM21 import MeasureParser


def xmlSound(mp: MeasureParser, mxSound: ET.Element) -> None:
    '''
    Convert a <sound> tag to one or more relevant objects
    (presently just MetronomeMark),
    and add it or them to the core and staffReference of the MeasureParser `mp`.

    Reads offset is from `mp` via `.offsetMeasureNote` so the mark lands at the
    current position in the measure.

    Set up everything:

    >>> from music21.musicxml.xmlSoundParser import xmlSound
    >>> from xml.etree.ElementTree import fromstring as EL
    >>> mp = musicxml.xmlToM21.MeasureParser()
    >>> mp.offsetMeasureNote = 2.0
    >>> len(mp.stream[tempo.MetronomeMark])
    0

    Now call the routine.

    >>> xmlSound(mp, EL('<sound tempo="128"/>'))

    Nothing is returned, but the stream inside the MeasureParser now has a metronomeMark
    at the `.offsetMeasureNote` of `mp`.  Because all the routines in this module
    are optimized for speed, we first need to call `coreElementsChanged`
    before querying the stream for each of them (normally the MeasureParser
    does this for us after parsing the entire measure).

    >>> mp.stream.coreElementsChanged()
    >>> mm = mp.stream[tempo.MetronomeMark].first()
    >>> mm
    <music21.tempo.MetronomeMark Quarter=128 (playback only)>
    >>> mm.offset
    2.0

    A <sound> tag may also carry its own <offset> child, which is measured in
    MusicXML *divisions* and shifts the mark relative to the current position.
    `mp.divisions` is the number of divisions per quarter note, so with 8
    divisions per quarter an <offset> of 4 is half a quarter note -- an eighth
    note -- and the mark lands an eighth later than `.offsetMeasureNote`:

    >>> mp = musicxml.xmlToM21.MeasureParser()
    >>> mp.divisions = 8
    >>> mp.offsetMeasureNote = 2.0
    >>> xmlSound(mp, EL('<sound tempo="108"><offset>4</offset></sound>'))
    >>> mp.stream.coreElementsChanged()
    >>> mp.stream[tempo.MetronomeMark].first().offset
    2.5
    '''
    # sound tags can specify an offset that begin at, relative to current position.
    offsetDirection = mp.xmlToOffset(mxSound)
    # we put offsetDirection + mp.offsetMeasureNote to force conversion of Fraction to float
    totalOffset = offsetDirection + mp.offsetMeasureNote

    setSound(mp,
             mxSound=mxSound,
             mxDir=None,
             totalOffset=totalOffset)


def setSound(
    mp: MeasureParser,
    mxSound: ET.Element,
    *,
    mxDir: ET.Element|None,
    totalOffset: float
) -> None:
    '''
    Takes a <sound> tag and creates objects from it on the MeasureParser `mp`.
    Presently only handles <sound tempo='x'> events and inserts them as MetronomeMarks.
    If the <sound> tag is a child of a <direction> tag, the direction information
    is used to set the placement of the MetronomeMark.

    >>> from music21.musicxml.xmlSoundParser import setSound
    >>> from xml.etree.ElementTree import fromstring as EL
    >>> mp = musicxml.xmlToM21.MeasureParser()

    A <sound> with a tempo attribute inserts a MetronomeMark:

    >>> setSound(mp, EL('<sound tempo="144"/>'), mxDir=None, totalOffset=0.0)
    >>> mp.stream.coreElementsChanged()
    >>> mp.stream.getElementsByClass(tempo.MetronomeMark).first()
    <music21.tempo.MetronomeMark Quarter=144 (playback only)>

    A <sound> without a tempo attribute is (currently) a no-op, so no second
    mark is added:

    >>> setSound(mp, EL('<sound dynamics="70"/>'), mxDir=None, totalOffset=0.0)
    >>> mp.stream.coreElementsChanged()
    >>> len(mp.stream[tempo.MetronomeMark])
    1
    '''
    # extract the staffKey once since it will be the same for all the rest.
    staffKey = mp.getStaffNumber(mxSound)
    attrib = mxSound.attrib

    # TODO: coda
    # TODO: dacapo
    # TODO: dalsegno
    # TODO: damper-pedal
    # TODO: divisions
    # TODO: dynamics
    # TODO: fine
    # TODO: forward-repeat
    # TODO: id
    # TODO: pizzicato
    # TODO: segno
    # TODO: soft-pedal
    # TODO: sostenuto-pedal
    # TODO: time-only
    # TODO: tocoda
    # TODO: musicxml4: swing: straight or first/second/swing-type, swing-style
    # TODO: musicxml4: instrument-change: instrument-sound, solo or ensemble or none
    #                                     virtual-instrument
    if 'tempo' in attrib:
        setSoundTempo(mp, mxSound, mxDir=mxDir, staffKey=staffKey, totalOffset=totalOffset)


def setSoundTempo(
    mp: MeasureParser,
    mxSound: ET.Element,
    *,
    mxDir: ET.Element|None,
    staffKey: int,
    totalOffset: float
) -> None:
    '''
    Add a metronome mark from the tempo attribute of a <sound> tag to the
    MeasureParser `mp`.

    >>> from music21.musicxml.xmlSoundParser import setSoundTempo
    >>> from xml.etree.ElementTree import fromstring as EL
    >>> mp = musicxml.xmlToM21.MeasureParser()
    >>> setSoundTempo(mp, EL('<sound tempo="92"/>'), mxDir=None, staffKey=1, totalOffset=0.0)
    >>> mp.stream.coreElementsChanged()
    >>> mm = mp.stream[tempo.MetronomeMark].first()
    >>> mm
    <music21.tempo.MetronomeMark Quarter=92 (playback only)>
    >>> mm.numberSounding
    92
    >>> mm.number is None
    True
    '''
    qpm = common.numToIntOrFloat(float(mxSound.get('tempo', 0)))
    if qpm == 0:
        warnings.warn('0 qpm tempo tag found, skipping.', stacklevel=2)
        return
    mm = tempo.MetronomeMark(referent=duration.Duration(type='quarter'),
                             number=None,
                             numberSounding=qpm,
                             )
    helpers.synchronizeIdsToM21(mxSound, mm)
    mp.setPrintObject(mxSound, mm)
    mp.setPosition(mxSound, mm)
    if mxDir is not None:
        helpers.setM21AttributeFromAttribute(
            mm, mxDir, 'placement', 'placement'
        )
        mp.setEditorial(mxDir, mm)
    mp.insertCoreAndRef(totalOffset, staffKey, mm)


class Test(unittest.TestCase):
    def testSetSoundTempoZeroIsSkipped(self):
        '''
        A <sound> tag with tempo='0' warns and inserts no MetronomeMark.
        '''
        from xml.etree.ElementTree import fromstring as EL
        from music21.musicxml.xmlToM21 import MeasureParser

        mp = MeasureParser()
        with self.assertWarns(UserWarning):
            setSoundTempo(mp, EL('<sound tempo="0"/>'),
                          mxDir=None, staffKey=1, totalOffset=0.0)
            mp.stream.coreElementsChanged()
        self.assertEqual(
            len(mp.stream.getElementsByClass(tempo.MetronomeMark)), 0)

    def testNegativeOffsetShiftsEarlier(self):
        '''
        A negative <offset> child inside a <sound> tag shifts the mark earlier.
        Here, at 8 divisions per quarter, an <offset> of -4 is an eighth note,
        so the mark lands an eighth before `.offsetMeasureNote`.
        '''
        from xml.etree.ElementTree import fromstring as EL
        from music21.musicxml.xmlToM21 import MeasureParser

        mp = MeasureParser()
        mp.divisions = 8
        mp.offsetMeasureNote = 2.0
        xmlSound(mp, EL('<sound tempo="84"><offset>-4</offset></sound>'))
        mp.stream.coreElementsChanged()
        mm = mp.stream[tempo.MetronomeMark].first()
        self.assertEqual(mm.offset, 1.5)


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
