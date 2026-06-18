# ------------------------------------------------------------------------------
# Name:         musicxml/xmlSoundParser.py
# Purpose:      Translate the <sound> tag to music21
#
# Authors:      Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2016-22 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Functions that convert the <sound> tag to the many music21
objects that this tag might represent.

Pulled out because xmlToM21 is getting way too big. These are plain functions
(not methods/a mixin) that take the owning :class:`MeasureParser` as their first
argument, like the functions in :mod:`~music21.stream.makeNotation`. Only
:func:`xmlSound` is exposed on MeasureParser (as a thin method), so that no
per-measure helper object is created for the common case of a measure with no
<sound> tag.
'''
from __future__ import annotations

import typing as t
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

    Unlike :func:`setSound`, the offset is read from `mp` (it is not passed in),
    so the mark lands at the parser's current position in the measure:

    >>> from music21.musicxml.xmlSoundParser import xmlSound
    >>> from xml.etree.ElementTree import fromstring as EL
    >>> mp = musicxml.xmlToM21.MeasureParser()
    >>> mp.offsetMeasureNote = 2.0
    >>> xmlSound(mp, EL('<sound tempo="120"/>'))
    >>> mm = mp.stream.getElementsByClass(tempo.MetronomeMark).first()
    >>> mm
    <music21.tempo.MetronomeMark Quarter=120 (playback only)>
    >>> mm.offset
    2.0
    '''
    # offset is out of order because we need to know it before direction-type
    offsetDirection = mp.xmlToOffset(mxSound)
    totalOffset = offsetDirection + mp.offsetMeasureNote

    staffKey = mp.getStaffNumber(mxSound)

    setSound(mp,
             mxSound,
             None,
             staffKey,
             totalOffset)


def setSound(
    mp: MeasureParser,
    mxSound: ET.Element,
    mxDir: ET.Element|None,
    staffKey: int,
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

    >>> setSound(mp, EL('<sound tempo="144"/>'), None, 1, 0.0)
    >>> mp.stream.getElementsByClass(tempo.MetronomeMark).first()
    <music21.tempo.MetronomeMark Quarter=144 (playback only)>

    A <sound> without a tempo attribute is (currently) a no-op, so no second
    mark is added:

    >>> setSound(mp, EL('<sound dynamics="70"/>'), None, 1, 0.0)
    >>> len(mp.stream.getElementsByClass(tempo.MetronomeMark))
    1
    '''
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
    if 'tempo' in mxSound.attrib:
        setSoundTempo(mp, mxSound, mxDir, staffKey, totalOffset)


def setSoundTempo(
    mp: MeasureParser,
    mxSound: ET.Element,
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
    >>> setSoundTempo(mp, EL('<sound tempo="90"/>'), None, 1, 0.0)
    >>> mm = mp.stream.getElementsByClass(tempo.MetronomeMark).first()
    >>> mm
    <music21.tempo.MetronomeMark Quarter=90 (playback only)>
    >>> mm.numberSounding
    90
    >>> mm.number is None
    True

    A tempo of zero is skipped (with a warning) and nothing is inserted, so the
    count stays at the one mark from above:

    >>> import warnings
    >>> with warnings.catch_warnings():
    ...     warnings.simplefilter('ignore')
    ...     setSoundTempo(mp, EL('<sound tempo="0"/>'), None, 1, 0.0)
    >>> len(mp.stream.getElementsByClass(tempo.MetronomeMark))
    1
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


if __name__ == '__main__':
    import music21
    music21.mainTest()  # doctests only
