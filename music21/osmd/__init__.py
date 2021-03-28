# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:         osmd/__init__.py
# Purpose:      music21 classes for displaying music21 scores in IPython notebooks
#
# Authors:      Sven Hollowell
#
# Copyright:    Copyright © 2018-21 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# -------------------------------------------------------------------------------

__all__ = ['ConverterOpenSheetMusicDisplay']

from music21.osmd.osmd import ConverterOpenSheetMusicDisplay
from music21.converter import registerSubconverter

registerSubconverter(ConverterOpenSheetMusicDisplay)
