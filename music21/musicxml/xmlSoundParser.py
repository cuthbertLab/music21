# -*- coding: utf-8 -*-
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
Functions that convert <sound> tag to the many music21
objects that this tag might represent.

Pulled out because xmlToM21 is getting way too big.
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


class SoundTagMixin:
    '''
    This Mixin is applied to MeasureParser -- it is moved
    out from there because there is still a lot to write
    here and xmlToM21.py is getting too big.
    '''
    def xmlSound(self, mxSound: ET.Element) -> None:
        '''
        Convert a <sound> tag to one or more relevant objects
        (presently just MetronomeMark),
        and add it or them to the core and staffReference.
        '''
        if t.TYPE_CHECKING:
            assert isinstance(self, MeasureParser) and isinstance(self, SoundTagMixin)

        # offset is out of order because we need to know it before direction-type
        offsetDirection = self.xmlToOffset(mxSound)
        totalOffset = offsetDirection + self.offsetMeasureNote

        staffKey = self.getStaffNumber(mxSound)

        self.setSound(mxSound,
                      None,
                      staffKey,
                      totalOffset)

    def setSound(
        self,
        mxSound: ET.Element,
        mxDir: ET.Element|None,
        staffKey: int,
        totalOffset: float
    ) -> None:
        '''
        Takes a <sound> tag and creates objects from it.
        Presently only handles <sound tempo='x'> events and inserts them as MetronomeMarks.
        If the <sound> tag is a child of a <direction> tag, the direction information
        is used to set the placement of the MetronomeMark.
        '''
        if t.TYPE_CHECKING:
            assert isinstance(self, MeasureParser) and isinstance(self, SoundTagMixin)
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
            self.setSoundTempo(mxSound, mxDir, staffKey, totalOffset)


    def setSoundTempo(
        self,
        mxSound: ET.Element,
        mxDir: ET.Element|None,
        staffKey: int,
        totalOffset: float
    ) -> None:
        '''
        Add a metronome mark from the tempo attribute of a <sound> tag.
        '''
        if t.TYPE_CHECKING:
            assert isinstance(self, MeasureParser) and isinstance(self, SoundTagMixin)

        qpm = common.numToIntOrFloat(float(mxSound.get('tempo', 0)))
        if qpm == 0:
            warnings.warn('0 qpm tempo tag found, skipping.')
            return
        mm = tempo.MetronomeMark(referent=duration.Duration(type='quarter'),
                                 number=None,
                                 numberSounding=qpm,
                                 )
        helpers.synchronizeIdsToM21(mxSound, mm)
        self.setPrintObject(mxSound, mm)
        self.setPosition(mxSound, mm)
        if mxDir is not None:
            helpers.setM21AttributeFromAttribute(
                mm, mxDir, 'placement', 'placement'
            )
            self.setEditorial(mxDir, mm)
        self.insertCoreAndRef(totalOffset, staffKey, mm)


if __name__ == '__main__':
    import music21
    music21.mainTest()  # doctests only
