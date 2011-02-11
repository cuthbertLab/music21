#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         tie.py
# Purpose:      music21 classes for representing notes
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import unittest


import music21
from music21.musicxml import translate as musicxmlTranslate



#-------------------------------------------------------------------------------
class Tie(object):
    '''Object added to notes that are tied to other notes. The `type` value is one of start, stop, or continue.

    >>> from music21 import *
    >>> note1 = note.Note()
    >>> note1.tie = tie.Tie("start")
    >>> note1.tieStyle = "normal" # or could be dotted or dashed
    >>> note1.tie.type
    'start'
    >>> note1.tie
    <music21.tie.Tie start>

    Differences from MusicXML:
       notes do not need to know if they are tied from a
       previous note.  i.e., you can tie n1 to n2 just with
       a tie start on n1.  However, if you want proper musicXML output
       you need a tie stop on n2
       one tie with "continue" implies tied from and tied to

       optional (to know what notes are next:)
          .to = note()   # not implimented yet, b/c of garbage coll.
          .from = note()

    OMIT_FROM_DOCS
    (question: should notes be able to be tied to multiple notes
    for the case where a single note is tied both voices of a
    two-note-head unison?)
    '''

    def __init__(self, tievalue = 'start'):
        #music21.Music21Object.__init__(self)
        self.type = tievalue

    # investigate using weak-refs for .to and .from

    def _getMX(self):
        '''Return a MusicXML object representation. 
        '''
        return musicxmlTranslate.tieToMx(self)

    def _setMX(self, mxNote):
        '''Load a MusicXML object representation. 
        '''
        musicxmlTranslate.mxToTie(mxNote, self)

    mx = property(_getMX, _setMX)


    def __eq__(self, other):
        '''Equality. Based on attributes (such as pitch, accidental, duration, articulations, and ornaments) that are  not dependent on the wider context of a note (such as offset, beams, stem direction).

        >>> from music21 import *
        >>> t1 = tie.Tie('start')
        >>> t2 = tie.Tie('start')
        >>> t3 = tie.Tie('end')
        >>> t1 == t2
        True
        >>> t2 == t3, t3 == t1
        (False, False)
        >>> t2 == None
        False
        '''
        if other == None or not isinstance(other, Tie):
            return False
        elif self.type == other.type:
            return True
        return False

    def __ne__(self, other):
        '''Inequality. Needed for pitch comparisons.
        '''
        return not self.__eq__(other)

    def __repr__(self):
        return '<music21.tie.Tie %s>' % self.type



class Test(unittest.TestCase):
    
    def runTest(self):
        pass
    
    def testBasic(self):
        pass
    

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof

