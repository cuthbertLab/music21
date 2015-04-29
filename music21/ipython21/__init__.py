# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         ipython21/__init__.py
# Purpose:      music21 iPython Notebook support
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2013-15 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

__all__ = ['ipExtension', 'objects']

from music21.ipython21 import ipExtension
from music21.ipython21 import objects
from music21.ipython21.ipExtension import load_ipython_extension
