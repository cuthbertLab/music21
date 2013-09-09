# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         metadata.py
# Purpose:      music21 classes for representing score and work meta-data
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010, 2012 Michael Scott Cuthbert and the music21
#               Project 
# License:      LGPL, see license.txt
#-------------------------------------------------------------------------------
'''Classes and functions for creating and processing metadata associated with
scores, works, and fragments, such as titles, movements, authors, publishers,
and regions.

The :class:`~music21.metadata.Metadata` object is the main public interface to
metadata components. A Metadata object can be added to a Stream and used to set
common score attributes, such as title and composer. A Metadata object found at
offset zero can be accessed through a Stream's
:attr:`~music21.stream.Stream.metadata` property. 

The following example creates a :class:`~music21.stream.Stream` object, adds a
:class:`~music21.note.Note` object, and configures and adds the
:attr:`~music21.metadata.Metadata.title` and
:attr:`~music21.metadata.Metadata.composer` properties of a Metadata object. 

::

    >>> s = stream.Stream()
    >>> s.append(note.Note())
    >>> s.insert(metadata.Metadata())
    >>> s.metadata.title = 'title'
    >>> s.metadata.composer = 'composer'
    >>> #_DOCS_SHOW s.show()

.. image:: images/moduleMetadata-01.*
    :width: 600

'''

import os
import unittest

from music21.metadata.base import *
from music21.metadata.bundles import *
from music21.metadata.caching import *
from music21.metadata.primitives import *


#-------------------------------------------------------------------------------


from music21 import environment
environLocal = environment.Environment(os.path.basename(__file__))


#-------------------------------------------------------------------------------


#WORK_ID_ABBREVIATIONS = workIdAbbreviationDict.keys()
#WORK_IDS = workIdAbbreviationDict.values()


#-------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass


#-------------------------------------------------------------------------------
            

_DOC_ORDER = ()


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof

