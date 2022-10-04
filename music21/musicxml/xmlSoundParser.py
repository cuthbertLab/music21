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

class SoundTagMixin:
    pass

    def soundTagParser(self, mxSound):
        '''
        Returns a list of objects that represent the sound tag.
        '''
        soundObjs = []
        # pylint: disable=unused-variable
        tempoNum = mxSound.get('tempo')  # @UnusedVariable
        dynamicsNum = mxSound.get('dynamics')  # @UnusedVariable

        # TODO: musicxml4: swing: straight or first/second/swing-type, swing-style
        # TODO: musicxml4: instrument-change: instrument-sound, solo or ensemble or none
        #                                     virtual-instrument

        return soundObjs
