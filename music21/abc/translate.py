#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         abc.translate.py
# Purpose:      Translate ABC and music21 objects
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import music21
import unittest

from music21.abc import base as abcModule


def abcToStream(abcTokenList, inputM21=None):
    '''Given an mxScore, build into this stream
    '''

    from music21 import metadata
    from music21 import stream
    from music21 import note

    if inputM21 == None:
        s = stream.Score()
    else:
        s = inputM21

    md = metadata.Metadata()
    s.insert(0, md)

    p = stream.Part()

    for t in abcTokenList:
        if isinstance(t, abcModule.ABCMetadata):
            pass
        # as ABCChord is subclass of ABCNote, handle first
        elif isinstance(t, abcModule.ABCChord):
            pass
        elif isinstance(t, abcModule.ABCNote):
            n = note.Note(t.pitchName)
            n.quarterLength = t.quarterLength
            p.append(n)

    # add part
    s.insert(0, p)

    return s





#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass

    def testBasic(self):
        from music21 import abc
        from music21.abc import testFiles

        for tf in [
#             testFiles.fyrareprisarn,
#             testFiles.mysteryReel,
#             testFiles.aleIsDear, 
#             testFiles.testPrimitive,
            testFiles.fullRiggedShip,
#            testFiles.kitchGirl,
#             testFiles.williamAndNancy,
            ]:
            af = abc.ABCFile()
            abcTokenList = af.readstr(tf)

            s = abcToStream(abcTokenList)
            #s.show()


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        a = Test()




