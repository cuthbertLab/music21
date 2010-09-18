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






def abcToStreamPart(abcHandler, inputM21=None):
    '''Handler conversion of a single Part of a multi-part score. Results are built into the provided inputM21 object or a newly created Stream.
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

    p = stream.Part()

    # first, split into a list of Measures; if there is only metadata and 
    # one measure, that means that no measures are defined
    barHandlers = abcHandler.splitByMeasure()

    # merge leading meta data with each bar that preceedes it
    mergedHandlers = abcModule.mergeLeadingMetaData(barHandlers)

    # if only one merged handler, do not create measures
    if len(mergedHandlers) <= 1: 
        useMeasures = False 
    else:
        useMeasures = True

    # each unit in merged handlers defines possible a Measure (w/ or w/o metadata), trailing meta data, or a single collection of metadata and note data

    barCount = 0
    # merged handler are ABCHandlerBar objects, defining attributes for barlines
    for mh in mergedHandlers:
        # if use measures and the handler has notes; otherwise add to part
        if useMeasures and mh.hasNotes():
            dst = stream.Measure()

            # bar tokens are already extracted form token list and are available
            # as attributes on the handler object
            # may return None for a regular barline
            if mh.leftBarToken != None:
                bLeft = mh.leftBarToken.getBarObject()
                if bLeft != None:
                    dst.leftBarline = bLeft
            if mh.rightBarToken != None:
                bRight = mh.rightBarToken.getBarObject()
                if bRight != None:
                    dst.rightBarline = bRight

            barCount += 1

        else:
            dst = p # store directly in a part instance

        #environLocal.printDebug([mh, 'dst', dst])
        #ql = 0 # might not be zero if there is a pickup
        for t in mh.tokens:    
            if isinstance(t, abcModule.ABCMetadata):
                if t.isMeter():
                    ts = t.getTimeSignatureObject()
                    if ts != None: # can be None
                    # should append at the right position
                        if useMeasures: # assume at start of measures
                            dst.timeSignature = ts
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
                accStatusList = [] # accidental display status list
                for tSub in t.subTokens:
                    # notes are contained as subtokens are already parsed
                    if isinstance(tSub, abcModule.ABCNote):
                        pitchNameList.append(tSub.pitchName)
                        accStatusList.append(tSub.accidentalDisplayStatus)
                c = chord.Chord(pitchNameList)
                c.quarterLength = t.quarterLength
                # adjust accidental display for each contained pitch
                for pIndex in range(len(c.pitches)):
                    if c.pitches[pIndex].accidental == None:
                        continue
                    c.pitches[pIndex].accidental.displayStatus = accStatusList[pIndex]
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

        # append measure to part; in the case of trailing meta data
        # dst may be part, even though useMeasures is True
        if useMeasures and 'Measure' in dst.classes: 
            # check for incomplete bars
            if barCount == 1: # easy case
                # can only do this b/c ts is defined
                if dst.barDurationProportion() < 1.0:
                    dst.padAsAnacrusis()
                    environLocal.printDebug(['incompletely filled Measure found on abc import; interpreting as a anacrusis:', 'padingLeft:', dst.paddingLeft])

            # clefs are not typically defined; need to call bestClef
            # can get clef from some voices definition
            dst.clef = dst.bestClef()
            p.append(dst)

    if useMeasures:
        # call make beams for now; later, import beams
        p.makeBeams()

    s.insert(0, p)
    return s


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

    # get title from large-scale metadata
    match = []
    for t in abcHandler.tokens:    
        if isinstance(t, abcModule.ABCMetadata):
            if t.isTitle():
                md.title = t.data
                match.append('title')
                environLocal.printDebug(['got metadata title', md.title])
            elif t.isComposer():
                md.composer = t.data
                match.append('composer')
        # look for opportunity to break as soon as data is filled
        if len(match) == 2:
            match.sort()
            if match == ['composer', 'title']:
                break

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
        abcToStreamPart(partHandler, s)

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
#             testFiles.williamAndNancy,
#            testFiles.theAleWifesDaughter,
#            testFiles.theBeggerBoy,
#            testFiles.theAleWifesDaughter,
#            testFiles.draughtOfAle,

#            testFiles.testPrimitiveTuplet,
#            testFiles.testPrimitivePolyphonic,

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
        self.assertEqual(len(s.parts[0].flat.notes), 111)
        self.assertEqual(len(s.parts[1].flat.notes), 127)

        # chords are defined in second part here
        self.assertEqual(len(s.parts[1].flat.getElementsByClass('Chord')), 32)

        # check pitches in chords; sharps are applied due to key signature
        match = [p.nameWithOctave for p in s.parts[1].flat.getElementsByClass(
                'Chord')[4].pitches]
        self.assertEqual(match, ['F#4', 'D4', 'B3'])

        match = [p.nameWithOctave for p in s.parts[1].flat.getElementsByClass(
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
        # must flatten b/c  there are measures
        self.assertEqual(len(s.parts[0].flat.notes), 6)
        self.assertEqual(len(s.parts[1].flat.notes), 17)
        self.assertEqual(len(s.parts[2].flat.notes), 6)

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



    def testAnacrusisPadding(self):
        from music21 import abc
        from music21.abc import testFiles

        # 2 quarter pickup in 3/4
        ah = abc.ABCHandler()
        ah.process(testFiles.hectorTheHero)
        s = abcToStream(ah)
        m1 = s.parts[0].getElementsByClass('Measure')[0]

        # ts is 3/4
        self.assertEqual(m1.barDuration.quarterLength, 3.0)
        # filled with two quarter notes
        self.assertEqual(m1.duration.quarterLength, 2.0)
        # notes are shown as being on beat 2 and 3
        self.assertEqual(m1.notes[0]._getMeasureOffset(), 1.0)
        self.assertEqual(m1.notes[0].beat, 2.0)
        self.assertEqual(m1.notes[1]._getMeasureOffset(), 2.0)
        self.assertEqual(m1.notes[1].beat, 3.0)


        # two 16th pickup in 4/4
        ah = abc.ABCHandler()
        ah.process(testFiles.theAleWifesDaughter)
        s = abcToStream(ah)
        m1 = s.parts[0].getElementsByClass('Measure')[0]

        # ts is 3/4
        self.assertEqual(m1.barDuration.quarterLength, 4.0)
        # filled with two 16th
        self.assertEqual(m1.duration.quarterLength, 0.5)
        # notes are shown as being on beat 2 and 3
        self.assertEqual(m1.notes[0]._getMeasureOffset(), 3.5)
        self.assertEqual(m1.notes[0].beat, 4.5)
        self.assertEqual(m1.notes[1]._getMeasureOffset(), 3.75)
        self.assertEqual(m1.notes[1].beat, 4.75)



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
        #t.testBasic()

        t.testAnacrusisPadding()

