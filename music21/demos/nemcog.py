#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         nemcog.py
# Purpose:      Demonstrations for the New England Music Cognition meeting
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import unittest, doctest
from music21 import *

_MOD = 'demo/nemcog.py'
environLocal = environment.Environment(_MOD)

def timing(show = True):
    thusSaith = corpus.parseWork('handel/hwv56', '1-05')
    #thusSaith.show()

    chordSaith = thusSaith.chordify()
    if show is True:
        chordSaith.show()

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):
        '''nemcog: Test non-showing functions
        '''
        # beethoven examples are commented out for time
        # findPassingTones too
        #sStream = corpus.parseWork('opus133.xml') # load a MusicXML file
        # ex03, ex01, ex02, ex04, ex01Alt, findHighestNotes,ex1_revised
        #for func in [findPotentialPassingTones]:
        for func in [timing]:

            pass
            #func(show=False, op133=sStream)
            #func(show=False)


if __name__ == "__main__":
    import music21
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)

    elif len(sys.argv) > 1:
        t = Test()

#------------------------------------------------------------------------------
# eof

