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
from music21 import *

def pitchedPhase(show=False):

    sSrc = converter.parse("""E16 F# B c# d F# E c# B F# d c# 
                              E16 F# B c# d F# E c# B F# d c#""", '12/16')
    sPost = stream.Score()
    sPost.insert(0, stream.Part())
    sPost.insert(0, stream.Part())

    increment = 0.0625

    for i in range(int(round(1/increment)) + 1):
        sPost.parts[0].append(copy.deepcopy(sSrc))
        sMod = copy.deepcopy(sSrc)
        # increment last note
        sMod.notes[-1].quarterLength += increment
        sMod.transpose(12, inPlace=True)
        sPost.parts[1].append(sMod)


    if show:
        sPost.show('midi')
        # midi for some reason shows a leading rest
        sPost.show()

    #post = sPost.musicxml


if __name__ == '__main__':

    pitchedPhase(show=True)



