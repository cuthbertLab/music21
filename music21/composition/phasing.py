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
import random

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

    durationToShift = duration.Duration('64th')
    increment = durationToShift.quarterLength
    if cycles == None:
        cycles = int(round(1/increment)) + 1

    for i in range(cycles):
        sPost.parts[0].append(copy.deepcopy(sSrc))
        sMod = copy.deepcopy(sSrc)
        # increment last note
        sMod.notes[-1].quarterLength += increment
        
        randInterval = random.randint(-12,12)
        sMod.transpose(randInterval, inPlace=True)
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
   

    def testBasic(self, cycles=4, show=False):
        # run a reduced version
        pitchedPhase(cycles=cycles, show=show)


if __name__ == "__main__":
    import sys
    t = Test()
    t.testBasic(cycles=None, show=True)


    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)

    elif len(sys.argv) > 1:
        t = Test()
        t.testBasic(cycles=None, show=True)




