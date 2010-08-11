#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         phasing.py
# Purpose:      Modeling musical phasing structures in MusicXML
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import copy
import unittest

import music21
from music21 import *

def pitchedPhase(cycles=None, show=False):
    '''
    >>> from music21.composition import phasing
    '''

    sSrc = converter.parse("""E16 F# B c# d F# E c# B F# d c# 
                              E16 F# B c# d F# E c# B F# d c#""", '12/16')
    sPost = stream.Score()
    sPost.insert(0, stream.Part())
    sPost.insert(0, stream.Part())

    increment = 0.0625
    if cycles == None:
        cycles = int(round(1/increment)) + 1

    for i in range(cycles):
        sPost.parts[0].append(copy.deepcopy(sSrc))
        sMod = copy.deepcopy(sSrc)
        # increment last note
        sMod.notes[-1].quarterLength += increment
        sMod.transpose(12, inPlace=True)
        sPost.parts[1].append(sMod)


    if show:
        sPost.show('midi')
        sPost.show()
    else: # get musicxml
        post = sPost.musicxml


#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
   
    def runTest(self):
        pass
   

    def testBasic(self):
        # run a reduced version
        pitchedPhase(4, show=False)


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)

    elif len(sys.argv) > 1:
        t = Test()
        t.pitchedPhase(show=True)




