#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         ismir2010.py
# Purpose:      ismir2010.py
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import unittest, doctest

import music21
from music21 import humdrum
from music21.note import Note
from music21.meter import TimeSignature
from music21.stream import Measure
from copy import deepcopy

def bergEx01(show=True):
    # berg, violin concerto, measure 64-65, p12
    # triplets should be sextuplets

    humdata = '''
**kern
*M2/4
=1
24r
24g#
24f#
24e
24c#
24f
24r
24dn
24e-
24gn
24e-
24dn
=2
24e-
24f#
24gn
24b-
24an
24gn
24gn
24f#
24an
24cn
24a-
24en
=3
*-
'''

    score = humdrum.parseData(humdata).stream[0]
    if show:
        score.show()
   
    ts = score.getElementsByClass(TimeSignature)[0]
   
# TODO: what is the best way to do this now that 
# this raises a TupletException for being frozen?
#     for thisNote in score.flat.getNotes():
#         thisNote.duration.tuplets[0].setRatio(12, 8)

    for thisMeasure in score.getElementsByClass(Measure):
        thisMeasure.insertAtIndex(0, deepcopy(ts))
        thisMeasure.makeBeams()

    if show:
        score.show()



class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):
        '''Test non-showing functions
        '''
        for func in [bergEx01]:
            func(show=False)

if __name__ == "__main__":
    import music21
    music21.mainTest(Test)


