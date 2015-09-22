# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         search/__init__.py
# Purpose:      music21 classes for searching within files
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2011-2013 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Methods and Classes useful in searching within scores.

For searching a group of scores see the search functions within
:ref:`moduleCorpus` .

'''


### __init__.py ######
__all__ = ['base', 'lyrics', 'segment']

from music21.search import base
from music21.search import lyrics
from music21.search import segment

# __init__ can wildcard import base; it's how it is designed.
from music21.search.base import * # pylint: disable=wildcard-import

