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



def abcToStream(abcHandler, inputM21=None):
    '''Given an abcHandler object, build into a multi-part :class:`~music21.stream.Score` with metadata
    
    if the optional parameter inputM21 is given a music21 Stream subclass, it will use that object
    as the outermost object.  However, inner parts will always be made :class:`~music21.stream.Part` objects.
    '''

    from music21 import metadata
    from music21 import stream
    from music21 import note
    from music21 import meter
    from music21 import key
    from music21 import chord

    if inputM21 == None:
        s = stream.Score()
    else:
        s = inputM21

    # meta data can be first
    md = metadata.Metadata()
    s.insert(0, md)

    partHandlers = []
    tokenCollections = abcHandler.splitByVoice()
    if len(tokenCollections) == 1:
        partHandlers.append(tokenCollections[0])
    else:
        # add meta data to each Part
        for i in range(1, len(tokenCollections)):
            # concatenate abc handler instances
            partHandlers.append(tokenCollections[0] + tokenCollections[i])

    # find if this token list defines measures
    # this should probably operate at the level of tunes, not the entire
    # token list

    for partHandler in partHandlers:
        p = stream.Part()
        # TODO
        useMeasures = False #partHandler.definesMeasures()

        #ql = 0 # might not be zero if there is a pickup
        for t in partHandler.tokens:
            if useMeasures:
                pass
#                 if isinstance(t, abcModule.ABCBar):
#                     environLocal.printDebug(['abc bar', t])
            else:
                dst = p # store destination of elements

            if isinstance(t, abcModule.ABCMetadata):
                if t.isTitle():
                    environLocal.printDebug(['got raw abc title', t.data])
                    md.title = t.data
                    environLocal.printDebug(['got metadata title', md.title])
                elif t.isComposer():
                    md.composer = t.data
                elif t.isMeter():
                    ts = t.getTimeSignatureObject()
                    if ts != None: # can be None
                    # should append at the right position
                        if useMeasures: # assume at start of measures
                            dst.timeSignature(ts)
                        else:
                            dst.append(ts)
                elif t.isKey():
                    ks = t.getKeySignatureObject()
                    if useMeasures:  # assume at start of measures
                        dst.keySignature = ks
                    else:
                        dst.append(ks)
    
            # as ABCChord is subclass of ABCNote, handle first
            elif isinstance(t, abcModule.ABCChord):
                # may have more than notes?
                pitchNameList = []
                for tSub in t.subTokens:
                    # notes are contained as subtokens are already parsed
                    if isinstance(tSub, abcModule.ABCNote):
                        pitchNameList.append(tSub.pitchName)
                c = chord.Chord(pitchNameList)
                c.quarterLength = t.quarterLength
                dst.append(c)

                #ql += t.quarterLength
    
            elif isinstance(t, abcModule.ABCNote):
                if t.isRest:
                    n = note.Rest()
                else:
                    n = note.Note(t.pitchName)
                    if n.accidental != None:
                        n.accidental.displayStatus = t.accidentalDisplayStatus

                n.quarterLength = t.quarterLength
                dst.append(n)
    
                #ql += t.quarterLength
    
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
            #testFiles.morrisonsJig,
#            testFiles.hectorTheHero,
#            testFiles.aleIsDear,
#             testFiles.williamAndNancy,
#            testFiles.theAleWifesDaughter,
#            testFiles.theBeggerBoy,
#            testFiles.theAleWifesDaughter,
#            testFiles.testPrimitiveTuplet,

            ]:
            af = abc.ABCFile()
            ah = af.readstr(tf) # return handler
            s = abcToStream(ah)
            s.show()
            #s.show('midi')



    def testGetMetaData(self):

        from music21 import abc
        from music21.abc import testFiles

        for (tf, titleEncoded, meterEncoded, keyEncoded) in [
            (testFiles.fyrareprisarn, 'Fyrareprisarn', '3/4', 'F'), 
            (testFiles.mysteryReel, 'Mystery Reel', 'C|', 'G'), 
            (testFiles.aleIsDear, 'The Ale is Dear', '4/4', 'D', ),
            (testFiles.kitchGirl, 'Kitchen Girl', '4/4', 'D'),
            (testFiles.williamAndNancy, 'William and Nancy', '6/8', 'G'),
            ]:

            af = abc.ABCFile()
            ah = af.readstr(tf) # returns an ABCHandler object
            s = abcToStream(ah)

            self.assertEqual(s.metadata.title, titleEncoded)


    def testChords(self):

        from music21 import abc
        from music21.abc import testFiles


        tf = testFiles.aleIsDear

        af = abc.ABCFile()
        s = abcToStream(af.readstr(tf))

        self.assertEqual(len(s.parts), 2)
        self.assertEqual(len(s.parts[0].notes), 111)
        self.assertEqual(len(s.parts[1].notes), 127)

        # chords are defined in second part here
        self.assertEqual(len(s.parts[1].getElementsByClass('Chord')), 32)

        # check pitches in chords; sharps are applied due to key signature
        match = [p.nameWithOctave for p in s.parts[1].getElementsByClass(
                'Chord')[4].pitches]
        self.assertEqual(match, ['F#4', 'D4', 'B3'])

        match = [p.nameWithOctave for p in s.parts[1].getElementsByClass(
                'Chord')[3].pitches]
        self.assertEqual(match, ['E4', 'C#4', 'A3'])

        #s.show()
        #s.show('midi')



    def testMultiVoice(self):

        from music21 import abc
        from music21.abc import testFiles

        tf = testFiles.testPrimitivePolyphonic

        af = abc.ABCFile()
        s = abcToStream(af.readstr(tf))

        self.assertEqual(len(s.parts), 3)
        self.assertEqual(len(s.parts[0].notes), 6)
        self.assertEqual(len(s.parts[1].notes), 20)
        self.assertEqual(len(s.parts[2].notes), 6)

        #s.show()
        #s.show('midi')


    def testTuplets(self):

        from music21 import abc
        from music21.abc import testFiles

        tf = testFiles.testPrimitiveTuplet
        af = abc.ABCFile()
        s = abcToStream(af.readstr(tf))
        match = []
        # match strings for better comparison
        for n in s.flat.notes:
            match.append(str(n.quarterLength))
        self.assertEqual(match, ['0.333333333333', '0.333333333333', '0.333333333333', '0.2', '0.2', '0.2', '0.2', '0.2', '0.166666666667', '0.166666666667', '0.166666666667', '0.166666666667', '0.166666666667', '0.166666666667', '0.142857142857', '0.142857142857', '0.142857142857', '0.142857142857', '0.142857142857', '0.142857142857', '0.142857142857', '0.666666666667', '0.666666666667', '0.666666666667', '0.666666666667', '0.666666666667', '0.666666666667', '0.0833333333333', '0.0833333333333', '0.0833333333333', '0.0833333333333', '0.0833333333333', '0.0833333333333', '0.0833333333333', '0.0833333333333', '0.0833333333333', '0.0833333333333', '0.0833333333333', '0.0833333333333', '2.0'])


    def testLyrics(self):
        # TODO

        from music21 import abc
        from music21.abc import testFiles

        tf = testFiles.sicutRosa
        af = abc.ABCFile()
        s = abcToStream(af.readstr(tf))
    
        #s.show()

#         self.assertEqual(len(s.parts), 3)
#         self.assertEqual(len(s.parts[0].notes), 6)
#         self.assertEqual(len(s.parts[1].notes), 20)
#         self.assertEqual(len(s.parts[2].notes), 6)
# 
        #s.show()
        #s.show('midi')



if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)

    elif len(sys.argv) > 1:
        t = Test()
        t.testBasic()



