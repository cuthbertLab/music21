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

from music21 import environment
_MOD = 'abc.translate.py'
environLocal = environment.Environment(_MOD)



def abcToStream(abcTokenList, inputM21=None):
    '''Given an mxScore, build into this stream
    '''

    from music21 import metadata
    from music21 import stream
    from music21 import note
    from music21 import meter

    if inputM21 == None:
        s = stream.Score()
    else:
        s = inputM21

    md = metadata.Metadata()
    s.insert(0, md)

    p = stream.Part()

    #ql = 0 # might not be zero if there is a pickup
    for t in abcTokenList:
        if isinstance(t, abcModule.ABCMetadata):
            if t.isTitle():
                environLocal.printDebug(['got title', t.data])
                md.title = t.data
            if t.isComposer():
                md.composer = t.data
            if t.isMeter():
                n, d, symbol = t.getTimeSignature()
                ts = meter.TimeSignature('%s/%s' % (n,d))
                # should append at the right place
                p.append(ts)

        # as ABCChord is subclass of ABCNote, handle first
        elif isinstance(t, abcModule.ABCChord):
            pass
            #ql += t.quarterLength

        elif isinstance(t, abcModule.ABCNote):
            n = note.Note(t.pitchName)
            n.quarterLength = t.quarterLength
            p.append(n)

            #ql += t.quarterLength

    # add metadata
    s.insert(0, md)
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
#            testFiles.fullRiggedShip,
#            testFiles.kitchGirl,
            testFiles.morrisonsJig,
#             testFiles.williamAndNancy,
            ]:
            af = abc.ABCFile()
            abcTokenList = af.readstr(tf)

            s = abcToStream(abcTokenList)
            s.show('midi')



    def testGetMetaData(self):

        from music21 import abc
        from music21.abc import testFiles

        for (tf, titleEncoded, meterEncoded, keyEncoded) in [
            (testFiles.fyrareprisarn, 'Fyrareprisarn', '3/4', 'F'), 
            (testFiles.mysteryReel, 'Mystery Reel', 'C|', 'G'), 
            (testFiles.aleIsDear, 'Ale is Dear, the', '4/4', 'D', ),
            (testFiles.kitchGirl, 'Kitchen Girl', '4/4', 'D'),
            (testFiles.williamAndNancy, 'William and Nancy', '6/8', 'G'),
            ]:

            af = abc.ABCFile()
            abcTokenList = af.readstr(tf)
            s = abcToStream(abcTokenList)

            self.assertEqual(s.metadata.title, titleEncoded)



if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)

    elif len(sys.argv) > 1:
        t = Test()
        t.testBasic()



