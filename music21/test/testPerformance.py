# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         testPerformance.py
# Purpose:      Tests keep track of long-term performance targets
#
# Authors:      Christopher Ariza
#
# Copyright:    Copyright © 2009-2011 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
This module defines a number of performance test.
 Results for these performances are stored and dated,
 and used to track long-term performance changes.

This file is not run with the standard test battery presently.
'''


import unittest

import music21
from music21 import common, corpus
from music21.musicxml.m21ToXml import GeneralObjectExporter as GEX

from music21 import environment
_MOD = 'test.testPerformance'
environLocal = environment.Environment(_MOD)

# ------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runStreamIterationByIterator(self):
        '''Stream iteration by iterator
        '''
        from music21 import note, stream
        # create a stream with 750 notes, 250 rests
        s = stream.Stream()
        for i in range(1000):
            n = note.Note()
            s.append(n)
        for i in range(500):
            r = note.Rest()
            s.append(r)

        for i in range(100):
            for j in s:  # this will create an iterator instances
                pass

    def runStreamIterationByElements(self):
        '''Stream iteration by .elements access
        '''
        from music21 import note, stream
        # create a stream with 750 notes, 250 rests
        s = stream.Stream()
        for i in range(1000):
            n = note.Note()
            s.append(n)
        for i in range(500):
            r = note.Rest()
            s.append(r)

        for i in range(100):
            for j in s.elements:  # this will create an iterator instances
                pass

    def runGetElementsByClassType(self):
        '''Getting elements by class type
        '''
        from music21 import note, stream

        # create a stream with 750 notes, 250 rests
        s = stream.Stream()
        for i in range(1000):
            n = note.Note()
            s.append(n)
        for i in range(500):
            r = note.Rest()
            s.append(r)

        for i in range(2):
            post = s.flat.getElementsByClass([note.Rest, note.Note])
            self.assertEqual(len(post), 1500)

    def runGetElementsByClassString(self):
        '''Getting elements by string
        '''
        from music21 import note, stream

        # create a stream with 750 notes, 250 rests
        s = stream.Stream()
        for i in range(1000):
            n = note.Note()
            s.append(n)
        for i in range(500):
            r = note.Rest()
            s.append(r)

        for i in range(2):
            post = s.flat.getElementsByClass(['Rest', 'Note'])
            self.assertEqual(len(post), 1500)

    def runParseBeethoven(self):
        '''Loading file: beethoven/opus59no2/movement3
        '''
        junk = corpus.parse('beethoven/opus59no2/movement3', forceSource=True)

    def runMusicxmlOutPartsBeethoven(self):
        '''Loading file and rendering musicxml output for each part: beethoven/opus59no2/movement3
        '''
        x = corpus.parse('beethoven/opus59no2/movement3', forceSource=True)
        # problem: doing each part is much faster than the whole score
        for p in x.parts:
            junk = GEX().parse(p)

    def runMusicxmlOutScoreBeethoven(self):
        '''
        Loading file and rendering musicxml output of complete score: beethoven/opus59no2/movement3
        '''
        x = corpus.parse('beethoven/opus59no2/movement3', forceSource=True)
        # problem: doing each part is much faster than the whole score
        junk = GEX().parse(x)

    def runParseHaydn(self):
        '''Loading file: haydn/opus74no1/movement3
        '''
        junk = corpus.parse('haydn/opus74no1/movement3', forceSource=True)

    def runParseSchumann(self):
        '''Loading file: schumann/opus41no1/movement2
        '''
        junk = corpus.parse('schumann/opus41no1/movement2', forceSource=True)

    def runParseLuca(self):
        '''
        Loading file: luca/gloria
        '''
        junk = corpus.parse('luca/gloria', forceSource=True)

    def runMusicxmlOutLuca(self):
        '''
        Loading file and rendering musicxml output: luca/gloria
        '''
        x = corpus.parse('luca/gloria', forceSource=True)
        junk = GEX().parse(x)

    def runCreateTimeSignatures(self):
        '''Creating 500 TimeSignature objects
        '''
        from music21 import meter
        tsStr = ['4/4', '4/4', '4/4', '3/4', '3/4', '2/4', '2/4', '2/2',
                 '2/2', '3/8', '6/8', '9/8', '5/4', '12/8']

        for i in range(500):
            meter.TimeSignature(tsStr[i % len(tsStr)])

    def runCreateDurations(self):
        '''
        Creating 10000 Duration objects
        '''
        from music21 import duration
        qlList = [4, 2, 1, 0.5, 1 / 3, 0.25, 0.125]

        for i in range(10000):
            ql = qlList[i % len(qlList)]
            d = duration.Duration()
            d.quarterLength = ql
            junk = d.quarterLength

    def runCreatePitches(self):
        '''
        Creating 50000 Pitch objects
        '''
        from music21 import pitch
        pList = [1.5, 5, 20.333333, 8, 2.5, 'A#', 'b`', 'c6#~']

        for i in range(50000):
            inputPName = pList[i % len(pList)]
            p = pitch.Pitch(inputPName)
            p.transpose('p5', inPlace=True)

    def runParseABC(self):
        '''Creating loading a large multiple work abc file (han1)
        '''
        dummy = corpus.parse('essenFolksong/han1')

    def runGetElementsByContext(self):
        '''Test getting elements by context from a Stream
        '''
        s = corpus.parse('bwv66.6')
        # create a few secondary streams to add more sites
        unused_flat = s.flat
        unused_notes = s.flat.notes

        for p in s.parts:
            for m in p.getElementsByClass('Measure'):
                if m.number == 0:
                    continue
                post = m.getContextByClass('Clef')
                assert post is not None
                post = m.getContextByClass('TimeSignature')
                assert post is not None
                post = m.getContextByClass('KeySignature')
                assert post is not None

                for n in m.notesAndRests:
                    post = n.getContextByClass('Clef')
                    assert post is not None
                    post = n.getContextByClass('TimeSignature')
                    assert post is not None
                    post = n.getContextByClass('KeySignature')
                    assert post is not None

    def runGetElementsByPrevious(self):
        '''Test getting elements by using the previous method
        '''
        s = corpus.parse('bwv66.6')
        # create a few secondary streams to add more sites
        unused_flat = s.flat
        unused_notes = s.flat.notes

        for p in s.parts:
            for m in p.getElementsByClass('Measure'):
                if m.number == 0:
                    continue
                post = m.previous('Clef')
                assert post is not None
                post = m.previous('TimeSignature')
                assert post is not None
                post = m.previous('KeySignature')
                assert post is not None

                for n in m.notesAndRests:
                    post = n.getContextByClass('Clef')
                    assert post is not None
                    post = n.getContextByClass('TimeSignature')
                    assert post is not None
                    post = n.getContextByClass('KeySignature')
                    assert post is not None

    def runParseMonteverdiRNText(self):
        '''Loading file: beethoven/opus59no2/movement3
        '''
        unused = corpus.parse('monteverdi/madrigal.5.3.rntxt', forceSource=True)

    # --------------------------------------------------------------------------
    def testTimingTolerance(self):
        '''
        Test the performance of methods defined above,
        comparing the resulting time to the time obtained in past runs.

        This should not produce errors as such, but is used to provide reference
        if overall performance has changed.
        '''
        # provide work and expected min/max in seconds
        for testMethod, best in [

            (self.runGetElementsByPrevious,
                {
                    '2011.11.29': 4.69,
                }),

            (self.runGetElementsByContext,
                {
                    '2010.11.10': 7.3888170,
                    '2010.11.11': 3.96121883392,
                }),


            #
            #
            #
            # #             (self.runParseABC,
            # #                 {
            # #                  '2010.10.20': 38.6760668755,
            # #                  '2010.10.21': 35.4297668934,
            # #                 }),
            #
            #
            #             (self.runCreateDurations,
            #                 {
            #                  '2010.10.07': 0.201117992401,
            #
            #                 }),
            #
            #             (self.runCreateTimeSignatures,
            #                 {
            #                  '2010.10.07': 2.88308691978,
            #                  '2010.10.08': 1.40892004967 ,
            #
            #                 }),
            #
            #
            #             (self.runStreamIterationByIterator,
            #                 {'2010.09.20': 2.2524,
            #                  '2010.10.07': 1.8214,
            #                 }),
            #
            #             (self.runStreamIterationByElements,
            #                 {'2010.09.20': 0.8317,
            #                 }),
            #
            #
            #             (self.runGetElementsByClassType,
            #                 {'2010.09.20': 3.28,
            #                 }),
            #
            #             (self.runGetElementsByClassString,
            #                 {'2010.09.20': 3.22,
            #                 }),
            #
            #             (self.runParseBeethoven,
            #                 {'2009.12.14': 7.42,
            #                  '2009.12.15': 6.686,
            #                  '2010.06.24': 7.475,
            #                  '2010.07.08': 3.562,
            #                 }),
            #
            #             (self.runMusicxmlOutPartsBeethoven,
            #                 {'2010.09.20': 7.706,
            #                 }),
            #
            #             (self.runMusicxmlOutScoreBeethoven,
            #                 {'2010.09.20': 33.273,
            #                  '2010.10.07': 11.9290,
            #                 }),


            #
            #             (self.runCreatePitches,
            #                 {'2011.04.12': 31.071,
            #                 }),


            #             (self.runParseHaydn,
            #                 {'2009.12.14': 4.08,
            #                  '2009.12.15': 3.531,
            #                  '2010.06.24': 3.932,
            #                  '2010.07.08': 1.935,
            #                 }),
            #             (self.runParseSchumann,
            #                 {'2009.12.14': 5.88,
            #                  '2009.12.15': 5.126,
            #                  '2010.06.24': 5.799,
            #                  '2010.07.08': 2.761,
            #                 }),
            #             (self.runParseLuca,
            #                 {'2009.12.14': 3.174,
            #                  '2009.12.15': 2.954,
            #                  '2010.06.24': 3.063,
            #                  '2010.07.08': 1.508,
            #                 }),
            #
            #             (self.runMusicxmlOutLuca,
            #                 {'2010.09.20': 8.372,
            #                  '2010.10.07': 4.5613,
            #                 }),
            #

            #             (self.runParseMonteverdiRNText,
            #                 {'2011.02.27': 6.411,
            #                  '2011.02.28': 2.944,
            #                 }),

        ]:  # end of long for loop

            t = common.Timer()
            t.start()
            # call the test
            testMethod()
            t.stop()
            dur = t()
            items = list(best.items())
            items.sort()
            items.reverse()
            environLocal.printDebug(['\n\ntiming tolerance for:',
                                     str(testMethod.__doc__.strip()),
                                     '\nthis run:', dur, '\nbest runs:',
                                     [f'{x}: {y}' for x, y in items], '\n'
                                     ]
                                    )
            # self.assertEqual(True, dur <= max)  # performance test


if __name__ == '__main__':
    import sys

    if len(sys.argv) == 1:  # normal conditions
        # sys.arg test options will be used in mainTest()
        music21.mainTest(Test)


