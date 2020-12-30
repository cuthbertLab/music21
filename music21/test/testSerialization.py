# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         testSerialization.py
# Purpose:      tests for serializing music21 objects
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2012-13 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------


import unittest
import music21  # needed to do fully-qualified isinstance name checking

from music21 import freezeThaw

from music21 import environment
_MOD = 'test.testSerialization'
environLocal = environment.Environment(_MOD)


# ------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def testBasicC(self):
        from music21 import stream, note, converter

        s = stream.Stream()
        n1 = note.Note('d2', quarterLength=2.0)
        s.append(n1)
        s.append(note.Note('g~6', quarterLength=0.25))

        temp = converter.freezeStr(s)
        post = converter.thawStr(temp)
        self.assertEqual(len(post.notes), 2)
        self.assertEqual(str(post.notes[0].pitch), 'D2')

    def testBasicD(self):
        from music21 import stream, note, converter, spanner
        import copy

        s = stream.Stream()
        n1 = note.Note('d2', quarterLength=2.0)
        n2 = note.Note('e2', quarterLength=2.0)
        sp = spanner.Slur(n1, n2)

        s.append(n1)
        s.append(n2)
        s.append(sp)

        # the deepcopy is what creates the bug in the preservation of a weakref

        # temp = converter.freezeStr(s)

        sCopy = copy.deepcopy(s)
        temp = converter.freezeStr(sCopy)

        post = converter.thawStr(temp)
        self.assertEqual(len(post.notes), 2)
        self.assertEqual(str(post.notes[0].pitch), 'D2')
        spPost = post.spanners[0]
        self.assertEqual(spPost.getSpannedElements(), [post.notes[0], post.notes[1]])
        self.assertEqual(spPost.getSpannedElementIds(), [id(post.notes[0]), id(post.notes[1])])

    def testBasicE(self):
        from music21 import corpus, converter
        s = corpus.parse('bwv66.6')

        temp = converter.freezeStr(s, fmt='pickle')
        sPost = converter.thawStr(temp)
        # sPost.show()
        self.assertEqual(len(s.flat.notes), len(sPost.flat.notes))

        self.assertEqual(len(s.parts[0].notes), len(sPost.parts[0].notes))
        # print(s.parts[0].notes)
        # sPost.parts[0].notes

    def testBasicF(self):
        from music21 import stream, note, converter, spanner

        s = stream.Score()
        s.repeatAppend(note.Note('G4'), 5)
        for i, syl in enumerate(['se-', 'ri-', 'al-', 'iz-', 'ing']):
            s.notes[i].addLyric(syl)
        s.append(spanner.Slur(s.notes[0], s.notes[-1]))

        # file writing
        # converter.freeze(s, fmt='pickle', fp='/_scratch/test.p')

        data = converter.freezeStr(s, fmt='pickle')
        sPost = converter.thawStr(data)
        self.assertEqual(len(sPost.notes), 5)
        # sPost.show()

    def testBasicJ(self):
        from music21 import stream, note, converter

        p1 = stream.Part()
        for m in range(3):
            m = stream.Measure()
            for i in range(4):
                m.append(note.Note('C4'))
            p1.append(m)

        p2 = stream.Part()
        for m in range(3):
            m = stream.Measure()
            for i in range(4):
                m.append(note.Note('G4'))
            p2.append(m)

        s = stream.Score()
        s.insert(0, p1)
        s.insert(0, p2)
        # s.show()

        temp = converter.freezeStr(s, fmt='pickle')
        sPost = converter.thawStr(temp)
        self.assertEqual(len(sPost.parts), 2)
        self.assertEqual(len(sPost.parts[0].getElementsByClass('Measure')), 3)
        self.assertEqual(len(sPost.parts[1].getElementsByClass('Measure')), 3)
        self.assertEqual(len(sPost.flat.notes), 24)

    def testBasicI(self):
        from music21 import stream, note, converter

        p1 = stream.Part()
        p1.repeatAppend(note.Note('C4'), 12)
        p1.makeMeasures(inPlace=True)
        p2 = stream.Part()
        p2.repeatAppend(note.Note('G4'), 12)
        p2.makeMeasures(inPlace=True)
        s = stream.Score()
        s.insert(0, p1)
        s.insert(0, p2)
        # s.show()

        temp = converter.freezeStr(s, fmt='pickle')
        sPost = converter.thawStr(temp)
        self.assertEqual(len(sPost.parts), 2)
        self.assertEqual(len(sPost.parts[0].getElementsByClass('Measure')), 3)
        self.assertEqual(len(sPost.parts[1].getElementsByClass('Measure')), 3)
        self.assertEqual(len(sPost.flat.notes), 24)

    def testSpannerSerializationOfNotesNotInPickle(self):
        '''
        test to see if spanners serialize properly if they
        contain notes not in the pickle...
        '''
        from music21 import stream, spanner, converter
        from music21 import note
        n1 = note.Note('D4')
        n2 = note.Note('E4')
        n3 = note.Note('F4')
        slur1 = spanner.Slur([n1, n2])
        s = stream.Part()
        s.insert(0, n3)
        s.insert(0, slur1)
        data = converter.freezeStr(s, fmt='pickle')

        unused_s2 = converter.thawStr(data)
        # s2.show('text')

    def testBigCorpus(self):
        from music21 import corpus, converter
        # import time
        # print(time.time())  # 8.3 sec from pickle; 10.3 sec for forceSource...
        # s = corpus.parse('beethoven/opus133') #, forceSource = True)
        # print(time.time())  # purePython: 33! sec; cPickle: 25 sec
        # data = converter.freezeStr(s, fmt='pickle')
        # print(time.time())  # cPickle: 5.5 sec!
        s = corpus.parse('corelli/opus3no1/1grave')
        sf = freezeThaw.StreamFreezer(s, fastButUnsafe=True)
        data = sf.writeStr()

        # print(time.time())  # purePython: 9 sec; cPickle: 3.8 sec!
        unused_s2 = converter.thawStr(data)
        # print(time.time())
#        s2.show()


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    music21.mainTest(Test)


