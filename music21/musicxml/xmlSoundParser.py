# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         musicxml/xmlSoundParser.py
# Purpose:      Translate the <sound> tag to music21
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2016 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Methods for converting <sound> tag to the many different music21
objects that this tag might represent.

Pulled out because xmlToM21 is getting way too big.
'''
class SoundTagMixin(object):
    pass

    def soundTagParser(self, mxSound):
        '''
        Returns a list of objects that represent the sound tag.
        '''
        soundObjs = []
        # pylint: disable=unused-variable
        tempoNum = mxSound.get('tempo') # @UnusedVariable
        dynamicsNum = mxSound.get('dynamics') # @UnusedVariable
        
        return soundObjs
