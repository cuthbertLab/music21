# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         test.test_base.py
# Purpose:      music21 tests for Music21Objects etc.
#
# Authors:      Michael Scott Asato Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2008-2023 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
from __future__ import annotations

import copy
import unittest

from music21 import bar
from music21 import base
from music21.base import Music21Object, ElementWrapper
from music21 import clef
from music21.common.enums import ElementSearch, OffsetSpecial
from music21 import converter
from music21 import corpus
from music21 import dynamics
from music21 import editorial
from music21 import exceptions21
from music21 import key
from music21 import meter
from music21 import note
from music21 import scale
from music21.sites import SitesException
from music21 import spanner
from music21 import stream
from music21 import tempo

# -----------------------------------------------------------------------------
class TestMock(Music21Object):
    pass


class Test(unittest.TestCase):

    def testM21ObjRepr(self):
        a = base.Music21Object()
        address = hex(id(a))
        self.assertEqual(repr(a), f'<music21.base.Music21Object object at {address}>')

    def testObjectCreation(self):
        a = TestMock()
        a.groups.append('hello')
        a.id = 'hi'
        a.offset = 2.0
        self.assertEqual(a.offset, 2.0)

    def testElementEquality(self):
        n = note.Note('F-')
        a = ElementWrapper(n)
        a.offset = 3.0
        c = ElementWrapper(n)
        c.offset = 2.0
        self.assertEqual(a, c)
        self.assertIsNot(a, c)
        b = ElementWrapper(note.Note('G'))
        self.assertNotEqual(a, b)

    def testNoteCreation(self):
        n = note.Note('A')
        n.offset = 1.0  # duration.Duration('quarter')
        n.groups.append('flute')

        b = copy.deepcopy(n)
        b.offset = 2.0  # duration.Duration('half')

        self.assertFalse(n is b)
        n.pitch.accidental = '-'
        self.assertEqual(b.name, 'A')
        self.assertEqual(n.offset, 1.0)
        self.assertEqual(b.offset, 2.0)
        n.groups[0] = 'bassoon'
        self.assertFalse('flute' in n.groups)
        self.assertTrue('flute' in b.groups)

    def testOffsets(self):
        a = ElementWrapper(note.Note('A#'))
        a.offset = 23.0
        self.assertEqual(a.offset, 23.0)

    def testObjectsAndElements(self):
        note1 = note.Note('B-')
        note1.duration.type = 'whole'
        stream1 = stream.Stream()
        stream1.append(note1)
        unused_subStream = stream1.notes

    def testM21BaseDeepcopy(self):
        '''
        Test copying
        '''
        a = Music21Object()
        a.id = 'test'
        b = copy.deepcopy(a)
        self.assertIsNot(a, b)
        self.assertEqual(a, b)
        self.assertEqual(b.id, 'test')

    def testM21BaseSites(self):
        '''
        Basic testing of M21 base object sites
        '''
        a = base.Music21Object()
        b = stream.Stream()

        # storing a single offset does not add a Sites entry
        a.offset = 30
        # all offsets are store in locations
        self.assertEqual(len(a.sites), 1)
        self.assertEqual(a._naiveOffset, 30.0)
        self.assertEqual(a.offset, 30.0)

        # assigning a activeSite directly  # v2.1. no longer allowed if not in site
        def assignActiveSite(aa, bb):
            aa.activeSite = bb

        self.assertRaises(SitesException, assignActiveSite, a, b)
        # now we have two offsets in locations
        b.insert(a)
        self.assertEqual(len(a.sites), 2)
        self.assertEqual(a.activeSite, b)

        a.offset = 40
        # still have activeSite
        self.assertEqual(a.activeSite, b)
        # now the offset returns the value for the current activeSite
        # b.setElementOffset(a, 40.0)
        self.assertEqual(a.offset, 40.0)

        # assigning a activeSite to None
        a.activeSite = None
        # properly returns original offset
        self.assertEqual(a.offset, 30.0)
        # we still have two locations stored
        self.assertEqual(len(a.sites), 2)
        self.assertEqual(a.getOffsetBySite(b), 40.0)

    def testM21BaseLocationsCopy(self):
        '''
        Basic testing of M21 base object
        '''
        a = stream.Stream()
        a.id = 'a obj'
        b = base.Music21Object()
        b.id = 'b obj'

        b.id = 'test'
        a.insert(0, b)
        c = copy.deepcopy(b)
        c.id = 'c obj'

        # have two locations: None, and that set by assigning activeSite
        self.assertEqual(len(b.sites), 2)
        dummy = c.sites
        # c is in 1 site, None, because it is a copy of b
        self.assertEqual(len(c.sites), 1)

    def testM21BaseLocationsCopyB(self):
        # the active site of a deepcopy should not be the same?
        # self.assertEqual(post[-1].activeSite, a)
        a = stream.Stream()
        b = base.Music21Object()
        b.id = 'test'
        a.insert(30, b)
        b.activeSite = a

        d = stream.Stream()
        self.assertEqual(b.activeSite, a)
        self.assertEqual(len(b.sites), 2)
        c = copy.deepcopy(b)
        self.assertIs(c.activeSite, None)
        d.insert(20, c)
        self.assertEqual(len(c.sites), 2)

        # this works because the activeSite is being set on the object
        # the copied activeSite has been deepcopied, and cannot now be accessed
        # this fails! post[-1].getOffsetBySite(a)

    def testSitesSearch(self):
        n1 = note.Note('A')
        n2 = note.Note('B')

        s1 = stream.Stream(id='s1')
        s1.insert(10, n1)
        s1.insert(100, n2)

        c1 = clef.TrebleClef()
        c2 = clef.BassClef()

        s2 = stream.Stream(id='s2')
        s2.insert(0, c1)
        s2.insert(100, c2)
        s2.insert(10, s1)  # placing s1 here should result in c2 being before n2

        self.assertEqual(s1.getOffsetBySite(s2), 10)
        # make sure in the context of s1 things are as we expect
        self.assertEqual(s2.flatten().getElementAtOrBefore(0), c1)
        self.assertEqual(s2.flatten().getElementAtOrBefore(100), c2)
        self.assertEqual(s2.flatten().getElementAtOrBefore(20), n1)
        self.assertEqual(s2.flatten().getElementAtOrBefore(110), n2)

        # note: we cannot do this
        #    self.assertEqual(s2.flatten().getOffsetBySite(n2), 110)
        # we can do this:
        self.assertEqual(n2.getOffsetBySite(s2.flatten()), 110)

        # this seems more idiomatic
        self.assertEqual(s2.flatten().elementOffset(n2), 110)

        # both notes can find the treble clef in the activeSite stream
        post = n1.getContextByClass(clef.TrebleClef)
        self.assertIsInstance(post, clef.TrebleClef)

        post = n2.getContextByClass(clef.TrebleClef)
        self.assertIsInstance(post, clef.TrebleClef)

        # n1 cannot find a bass clef because it is before the bass clef
        post = n1.getContextByClass(clef.BassClef)
        self.assertEqual(post, None)

        # n2 can find a bass clef, due to its shifted position in s2
        post = n2.getContextByClass(clef.BassClef)
        self.assertIsInstance(post, clef.BassClef)

    def testSitesMeasures(self):
        '''
        Can a measure determine the last Clef used?
        '''
        a = corpus.parse('bach/bwv324.xml')
        measures = a.parts[0].getElementsByClass(stream.Measure).stream()  # measures of first part

        # the activeSite of measures[1] is set to the new output stream
        self.assertEqual(measures[1].activeSite, measures)
        # the source Part should still be a context of this measure
        self.assertIn(a.parts[0], measures[1].sites)

        # from the first measure, we can get the clef by using
        # getElementsByClass
        post = measures[0].getElementsByClass(clef.Clef)
        self.assertIsInstance(post[0], clef.TrebleClef)

        # make sure we can find offset in a flat representation
        self.assertRaises(SitesException, a.parts[0].flatten().elementOffset, a.parts[0][3])

        # for the second measure
        post = a.parts[0][3].getContextByClass(clef.Clef)
        self.assertIsInstance(post, clef.TrebleClef)

        # for the second measure accessed from measures
        # we can get the clef, now that getContextByClass uses semiFlat
        post = measures[3].getContextByClass(clef.Clef)
        self.assertIsInstance(post, clef.TrebleClef)

        # add the measure to a new stream
        newStream = stream.Stream()
        newStream.insert(0, measures[3])
        # all previous locations are still available as a context
        self.assertTrue(newStream in measures[3].sites)
        self.assertTrue(measures in measures[3].sites)
        self.assertTrue(a.parts[0] in measures[3].sites)
        # we can still access the clef through this measure on this
        # new stream
        post = newStream[0].getContextByClass(clef.Clef)
        self.assertTrue(isinstance(post, clef.TrebleClef), post)

    def testSitesClef(self):
        sOuter = stream.Stream()
        sOuter.id = 'sOuter'
        sInner = stream.Stream()
        sInner.id = 'sInner'

        n = note.Note()
        sInner.append(n)
        sOuter.append(sInner)

        # append clef to outer stream
        altoClef = clef.AltoClef()
        altoClef.priority = -1
        sOuter.insert(0, altoClef)
        pre = sOuter.getElementAtOrBefore(0, [clef.Clef])
        self.assertTrue(isinstance(pre, clef.AltoClef), pre)

        # we should be able to find a clef from the lower-level stream
        post = sInner.getContextByClass(clef.Clef)
        self.assertTrue(isinstance(post, clef.AltoClef), post)

    def testBeatAccess(self):
        '''
        Test getting beat data from various Music21Objects.
        '''
        s = corpus.parse('bach/bwv66.6.xml')
        p1 = s.parts['#Soprano']

        # this does not work; cannot get these values from Measures
        #    self.assertEqual(p1.getElementsByClass(stream.Measure)[3].beat, 3)

        # clef/ks can get its beat; these objects are in a pickup,
        # and this give their bar offset relative to the bar
        eClef = p1.flatten().getElementsByClass(clef.Clef).first()
        self.assertEqual(eClef.beat, 4.0)
        self.assertEqual(eClef.beatDuration.quarterLength, 1.0)
        self.assertEqual(eClef.beatStrength, 0.25)

        eKS = p1.flatten().getElementsByClass(key.KeySignature).first()
        self.assertEqual(eKS.beat, 4.0)
        self.assertEqual(eKS.beatDuration.quarterLength, 1.0)
        self.assertEqual(eKS.beatStrength, 0.25)

        # ts can get beatStrength, beatDuration
        eTS = p1.flatten().getElementsByClass(meter.TimeSignature).first()
        self.assertEqual(eTS.beatDuration.quarterLength, 1.0)
        self.assertEqual(eTS.beatStrength, 0.25)

        # compare offsets found with items positioned in Measures
        # as the first bar is a pickup, the measure offset here is returned
        # with padding (resulting in 3)
        post = []
        for n in p1.flatten().notesAndRests:
            post.append(n._getMeasureOffset())
        self.assertEqual(post, [3.0, 3.5, 0.0, 1.0, 2.0, 3.0, 0.0,
                                1.0, 2.0, 3.0, 0.0, 0.5, 1.0, 2.0,
                                3.0, 0.0, 1.0, 2.0, 3.0, 0.0, 1.0,
                                2.0, 3.0, 0.0, 1.0, 2.0, 3.0, 0.0,
                                1.0, 2.0, 0.0, 2.0, 3.0, 0.0, 1.0, 1.5, 2.0])

        # compare derived beat string
        post = []
        for n in p1.flatten().notesAndRests:
            post.append(n.beatStr)
        self.assertEqual(post, ['4', '4 1/2', '1', '2', '3', '4', '1',
                                '2', '3', '4', '1', '1 1/2', '2', '3',
                                '4', '1', '2', '3', '4', '1', '2', '3',
                                '4', '1', '2', '3', '4', '1', '2', '3',
                                '1', '3', '4', '1', '2', '2 1/2', '3'])

        # for stream and Stream subclass, overridden methods not yet
        # specialized
        # _getMeasureOffset gets the offset within the activeSite
        # this shows that measure offsets are accommodating pickup
        post = []
        for m in p1.getElementsByClass(stream.Measure):
            post.append(m._getMeasureOffset())
        self.assertEqual(post, [0.0, 1.0, 5.0, 9.0, 13.0, 17.0, 21.0, 25.0, 29.0, 33.0])

        # all other methods define None
        post = []
        for n in p1.getElementsByClass(stream.Measure):
            post.append(n.beat)
        self.assertEqual(post, [None, None, None, None, None, None, None, None, None, None])

        post = []
        for n in p1.getElementsByClass(stream.Measure):
            post.append(n.beatStr)
        self.assertEqual(post, [None, None, None, None, None, None, None, None, None, None])

        post = []
        for n in p1.getElementsByClass(stream.Measure):
            post.append(n.beatDuration)
        self.assertEqual(post, [None, None, None, None, None, None, None, None, None, None])

    def testGetBeatStrengthA(self):
        n = note.Note('g')
        n.quarterLength = 1
        s = stream.Stream()
        s.insert(0, meter.TimeSignature('4/4'))
        s.repeatAppend(n, 8)
        # match = []
        self.assertEqual([e.beatStrength for e in s.notes],
                         [1.0, 0.25, 0.5, 0.25, 1.0, 0.25, 0.5, 0.25])

        n = note.Note('E--3', type='quarter')
        s = stream.Stream()
        s.insert(0.0, meter.TimeSignature('2/2'))
        s.repeatAppend(n, 12)
        match = [s.notes[i].beatStrength for i in range(12)]
        self.assertEqual([1.0, 0.25, 0.5, 0.25, 1.0, 0.25, 0.5, 0.25, 1.0, 0.25, 0.5, 0.25], match)

    def testMeasureNumberAccess(self):
        '''
        Test getting measure number data from various Music21Objects.
        '''
        s = corpus.parse('bach/bwv66.6.xml')
        p1 = s.parts['#Soprano']
        for classStr in ['Clef', 'KeySignature', 'TimeSignature']:
            self.assertEqual(p1.flatten().getElementsByClass(
                classStr)[0].measureNumber, 0)

        match = []
        for n in p1.flatten().notesAndRests:
            match.append(n.measureNumber)
        self.assertEqual(match, [0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 3,
                                 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7,
                                 8, 8, 8, 9, 9, 9, 9])

        # create a note and put it in different measures
        m1 = stream.Measure()
        m1.number = 3
        m2 = stream.Measure()
        m2.number = 74
        n = note.Note()
        self.assertEqual(n.measureNumber, None)  # not in a Measure
        m1.append(n)
        self.assertEqual(n.measureNumber, 3)
        m2.append(n)
        self.assertEqual(n.measureNumber, 74)

    def testPickupMeasuresBuilt(self):
        s = stream.Score()

        m1 = stream.Measure()
        m1.timeSignature = meter.TimeSignature('4/4')
        n1 = note.Note('d2')
        n1.quarterLength = 1.0
        m1.append(n1)
        # barDuration is based only on TS
        self.assertEqual(m1.barDuration.quarterLength, 4.0)
        # duration shows the highest offset in the bar
        self.assertEqual(m1.duration.quarterLength, 1.0)
        # presently, the offset of the added note is zero
        self.assertEqual(n1.getOffsetBySite(m1), 0.0)
        # the _getMeasureOffset method is called by all methods that evaluate
        # beat position; this takes padding into account
        self.assertEqual(n1._getMeasureOffset(), 0.0)
        self.assertEqual(n1.beat, 1.0)

        # the Measure.padAsAnacrusis() method looks at the barDuration and,
        # if the Measure is incomplete, assumes it is an anacrusis and adds
        # the appropriate padding
        m1.padAsAnacrusis()
        # app values are the same except _getMeasureOffset()
        self.assertEqual(m1.barDuration.quarterLength, 4.0)
        self.assertEqual(m1.duration.quarterLength, 1.0)
        self.assertEqual(n1.getOffsetBySite(m1), 0.0)
        # lowest offset inside of Measure still returns 0
        self.assertEqual(m1.lowestOffset, 0.0)
        # these values are now different
        self.assertEqual(n1._getMeasureOffset(), 3.0)
        self.assertEqual(n1.beat, 4.0)

        # appending this measure to the Score
        s.append(m1)
        # score duration is correct: 1
        self.assertEqual(s.duration.quarterLength, 1.0)
        # lowest offset is that of the first bar
        self.assertEqual(s.lowestOffset, 0.0)
        self.assertEqual(s.highestTime, 1.0)

        m2 = stream.Measure()
        n2 = note.Note('e2')
        n2.quarterLength = 4.0
        m2.append(n2)
        # based on contents
        self.assertEqual(m2.duration.quarterLength, 4.0)
        # we cannot get a bar duration b/c we have not associated a ts
        try:
            m2.barDuration.quarterLength
        except exceptions21.StreamException:
            pass

        # append to Score
        s.append(m2)
        # m2 can now find a time signature by looking to activeSite stream
        self.assertEqual(m2.duration.quarterLength, 4.0)
        # highest time of score takes into account new measure
        self.assertEqual(s.highestTime, 5.0)
        # offset are contiguous when accessed in a flat form
        self.assertEqual([n.offset for n in s.flatten().notesAndRests], [0.0, 1.0])

        m3 = stream.Measure()
        n3 = note.Note('f#2')
        n3.quarterLength = 3.0
        m3.append(n3)

        # add to stream
        s.append(m3)
        # m3 can now find a time signature by looking to activeSite stream
        self.assertEqual(m2.duration.quarterLength, 4.0)
        # highest time of score takes into account new measure
        self.assertEqual(s.highestTime, 8.0)
        # offset are contiguous when accessed in a flat form
        self.assertEqual([n.offset for n in s.flatten().notesAndRests], [0.0, 1.0, 5.0])

    def testPickupMeasuresImported(self):
        self.maxDiff = None
        s = corpus.parse('bach/bwv103.6')

        p = s.parts['#soprano']
        m1 = p.getElementsByClass(stream.Measure).first()

        self.assertEqual([n.offset for n in m1.notesAndRests], [0.0, 0.5])
        self.assertEqual(m1.paddingLeft, 3.0)

        offsets = [n.offset for n in p.flatten().notesAndRests]
        # offsets for flat representation have proper spacing
        self.assertEqual(offsets,
                         [0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0,
                          9.0, 10.0, 11.0, 12.0, 12.5, 13.0, 15.0, 16.0, 17.0,
                          18.0, 18.5, 18.75, 19.0, 19.5, 20.0, 21.0, 22.0, 23.0, 24.0,
                          25.0, 26.0, 27.0, 28.0, 29.0, 31.0, 32.0, 32.5, 33.0, 34.0,
                          35.0, 36.0, 37.0, 38.0, 39.0, 40.0, 41.0, 42.0,
                          43.0, 44.0, 44.5, 45.0, 47.0])

    def testHighestTime(self):
        s = stream.Stream()
        n1 = note.Note()
        n1.quarterLength = 30
        n2 = note.Note()
        n2.quarterLength = 20

        b1 = bar.Barline()
        s.append(n1)
        self.assertEqual(s.highestTime, 30.0)
        # noinspection PyTypeChecker
        s.coreSetElementOffset(b1, OffsetSpecial.AT_END, addElement=True)

        self.assertEqual(b1.getOffsetBySite(s), 30.0)

        s.append(n2)
        self.assertEqual(s.highestTime, 50.0)
        self.assertEqual(b1.getOffsetBySite(s), 50.0)

    def testRecurseByClass(self):
        s1 = stream.Stream()
        s2 = stream.Stream()
        s3 = stream.Stream()

        n1 = note.Note('C')
        n2 = note.Note('D')
        n3 = note.Note('E')
        c1 = clef.TrebleClef()
        c2 = clef.BassClef()
        c3 = clef.PercussionClef()

        s1.append(c1)
        s1.append(n1)

        s2.append(c2)
        s2.append(n2)

        s3.append(c3)
        s3.append(n3)

        # only get n1 here, as that is only level available
        self.assertEqual(s1.recurse().getElementsByClass(note.Note).first(), n1)
        self.assertEqual(s2.recurse().getElementsByClass(note.Note).first(), n2)
        self.assertEqual(s1[clef.Clef].first(), c1)
        self.assertEqual(s2[clef.Clef].first(), c2)

        # attach s2 to s1
        s2.append(s1)
        # stream 1 gets both notes
        self.assertEqual(list(s2.recurse().getElementsByClass(note.Note)), [n2, n1])

    def testSetEditorial(self):
        b2 = Music21Object()
        self.assertIsNone(b2._editorial)
        b2_ed = b2.editorial
        self.assertIsInstance(b2_ed, editorial.Editorial)
        self.assertIsNotNone(b2._editorial)

    def testStoreLastDeepCopyOf(self):
        n1 = note.Note()
        n2 = copy.deepcopy(n1)
        self.assertEqual(id(n2.derivation.origin), id(n1))

    def testHasElement(self):
        n1 = note.Note()
        s1 = stream.Stream()
        s1.append(n1)
        s2 = copy.deepcopy(s1)
        n2 = s2[0]  # this is a new instance; not the same as n1
        self.assertFalse(s2.hasElement(n1))
        self.assertTrue(s2.hasElement(n2))

        self.assertFalse(s1 in n2.sites)
        self.assertTrue(s2 in n2.sites)

    def testGetContextByClassA(self):
        p = stream.Part()
        m1 = stream.Measure()
        m1.repeatAppend(note.Note(quarterLength=1), 4)
        m2 = copy.deepcopy(m1)
        mm1 = tempo.MetronomeMark(number=50, referent=0.25)
        m1.insert(0, mm1)
        mm2 = tempo.MetronomeMark(number=150, referent=0.5)
        m2.insert(0, mm2)
        p.append([m1, m2])
        # p.show('t')
        # if done with default args, we get the same object, as we are using
        # getElementAtOrBefore
        self.assertEqual(str(mm2.getContextByClass(tempo.MetronomeMark)),
                         '<music21.tempo.MetronomeMark Eighth=150>')
        # if we provide the getElementMethod parameter, we can use
        # getElementBeforeOffset
        self.assertEqual(
            str(
                mm2.getContextByClass(
                    'MetronomeMark',
                    getElementMethod=ElementSearch.BEFORE_OFFSET
                )
            ),
            '<music21.tempo.MetronomeMark lento 16th=50>')

    def testElementWrapperOffsetAccess(self):
        class Mock:
            pass

        s = stream.Stream()
        s.append(meter.TimeSignature('fast 6/8'))
        storage = []
        for i in range(2):
            mock = Mock()
            el = base.ElementWrapper(mock)
            storage.append(el)
            s.insert(i, el)

        for ew in storage:
            self.assertTrue(s.hasElement(ew))

        match = [e.getOffsetBySite(s) for e in storage]
        self.assertEqual(match, [0.0, 1.0])

        self.assertEqual(s.elementOffset(storage[0]), 0.0)
        self.assertEqual(s.elementOffset(storage[1]), 1.0)

    def testGetActiveSiteTimeSignature(self):
        class Wave_read:
            def getnchannels(self):
                return 2

        s = stream.Stream()
        s.append(meter.TimeSignature('fast 6/8'))
        # s.show('t')
        storage = []
        for i in range(6):
            soundFile = Wave_read()
            # el = music21.Music21Object()
            el = base.ElementWrapper(soundFile)
            storage.append(el)
            self.assertEqual(el.obj, soundFile)
            s.insert(i, el)

        for ew in storage:
            self.assertTrue(s.hasElement(ew))

        matchOffset = []
        matchBeatStrength = []
        matchAudioChannels = []

        for j in s.getElementsByClass(base.ElementWrapper):
            matchOffset.append(j.offset)
            matchBeatStrength.append(j.beatStrength)
            matchAudioChannels.append(j.getnchannels())
        self.assertEqual(matchOffset, [0.0, 1.0, 2.0, 3.0, 4.0, 5.0])
        self.assertEqual(matchBeatStrength, [1.0, 0.25, 0.25, 1.0, 0.25, 0.25])
        self.assertEqual(matchAudioChannels, [2, 2, 2, 2, 2, 2])

    def testGetMeasureOffsetOrMeterModulusOffsetA(self):
        # test getting metric position in a Stream with a TS
        s = stream.Stream()
        s.repeatAppend(note.Note(), 12)
        s.insert(0, meter.TimeSignature('3/4'))

        match = [n.beat for n in s.notes]
        self.assertEqual(match, [1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 1.0, 2.0, 3.0])

        match = [n.beatStr for n in s.notes]
        self.assertEqual(match, ['1', '2', '3', '1', '2', '3', '1', '2', '3', '1', '2', '3'])

        match = [n.beatDuration.quarterLength for n in s.notes]
        self.assertEqual(match, [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])

        match = [n.beatStrength for n in s.notes]
        self.assertEqual(match, [1.0, 0.5, 0.5, 1.0, 0.5, 0.5, 1.0, 0.5, 0.5, 1.0, 0.5, 0.5])

    def testGetMeasureOffsetOrMeterModulusOffsetB(self):
        s = stream.Stream()
        s.repeatAppend(note.Note(), 12)
        s.insert(0.0, meter.TimeSignature('3/4'))
        s.insert(3.0, meter.TimeSignature('4/4'))
        s.insert(7.0, meter.TimeSignature('2/4'))

        match = [n.beat for n in s.notes]
        self.assertEqual(match, [1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 4.0, 1.0, 2.0, 1.0, 2.0, 1.0])

        match = [n.beatStr for n in s.notes]
        self.assertEqual(match, ['1', '2', '3', '1', '2', '3', '4', '1', '2', '1', '2', '1'])

        match = [n.beatStrength for n in s.notes]
        self.assertEqual(match, [1.0, 0.5, 0.5, 1.0, 0.25, 0.5, 0.25, 1.0, 0.5, 1.0, 0.5, 1.0])

    def testSecondsPropertyA(self):
        s = stream.Stream()
        s.repeatAppend(note.Note(), 12)
        s.insert(0, tempo.MetronomeMark(number=120))

        self.assertEqual([n.seconds for n in s.notes],
                         [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5])

        # changing tempo mid-stream
        s.insert(6, tempo.MetronomeMark(number=240))
        self.assertEqual([n.seconds for n in s.notes],
                         [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25])

        # adding notes based on seconds
        s2 = stream.Stream()
        s2.insert(0, tempo.MetronomeMark(number=120))
        s2.append(note.Note())
        s2.notes.first().seconds = 2.0
        self.assertEqual(s2.notes.first().quarterLength, 4.0)
        self.assertEqual(s2.duration.quarterLength, 4.0)

        s2.append(note.Note('C4', type='half'))
        s2.notes[1].seconds = 0.5
        self.assertEqual(s2.notes[1].quarterLength, 1.0)
        self.assertEqual(s2.duration.quarterLength, 5.0)

        s2.append(tempo.MetronomeMark(number=30))
        s2.append(note.Note())
        s2.notes[2].seconds = 0.5
        self.assertEqual(s2.notes[2].quarterLength, 0.25)
        self.assertEqual(s2.duration.quarterLength, 5.25)

    def testGetContextByClass2015(self):
        p = converter.parse('tinynotation: 3/4 C4 D E 2/4 F G A B 1/4 c')
        b = p.measure(3).notes[-1]
        c = b.getContextByClass('Note', getElementMethod=ElementSearch.AFTER_OFFSET)
        self.assertEqual(c.name, 'C')

        m = p.measure(1)
        self.assertIsNotNone(
            m.getContextByClass(clef.Clef, getElementMethod=ElementSearch.ALL)
        )

    def testGetContextByClassB(self):
        s = stream.Score()

        p1 = stream.Part()
        m1 = stream.Measure()
        m1.repeatAppend(note.Note(), 3)
        m1.timeSignature = meter.TimeSignature('3/4')
        m2 = stream.Measure()
        m2.repeatAppend(note.Note(), 3)
        p1.append(m1)
        p1.append(m2)

        p2 = stream.Part()
        m3 = stream.Measure()
        m3.timeSignature = meter.TimeSignature('3/4')
        m3.repeatAppend(note.Note(), 3)
        m4 = stream.Measure()
        m4.repeatAppend(note.Note(), 3)
        p2.append(m3)
        p2.append(m4)

        s.insert(0, p1)
        s.insert(0, p2)

        p3 = stream.Part()
        m5 = stream.Measure()
        m5.timeSignature = meter.TimeSignature('3/4')
        m5.repeatAppend(note.Note(), 3)
        m6 = stream.Measure()
        m6.repeatAppend(note.Note(), 3)
        p3.append(m5)
        p3.append(m6)

        p4 = stream.Part()
        m7 = stream.Measure()
        m7.timeSignature = meter.TimeSignature('3/4')
        m7.repeatAppend(note.Note(), 3)
        m8 = stream.Measure()
        m8.repeatAppend(note.Note(), 3)
        p4.append(m7)
        p4.append(m8)

        s.insert(0, p3)
        s.insert(0, p4)

        # self.targetMeasures = m4
        # n1 = m2[-1]  # last element is a note
        n2 = m4[-1]  # last element is a note

        # self.assertEqual(str(n1.getContextByClass(meter.TimeSignature)),
        #    '<music21.meter.TimeSignature 3/4>')
        self.assertEqual(str(n2.getContextByClass(meter.TimeSignature)),
                         '<music21.meter.TimeSignature 3/4>')

    def testNextA(self):
        s = stream.Stream()
        sc = scale.MajorScale()
        notes = []
        for i in sc.pitches:
            n = note.Note()
            s.append(n)
            notes.append(n)  # keep for reference and testing

        self.assertEqual(notes[0], s[0])  # leave as get index query.
        s0Next = s[0].next()
        self.assertEqual(notes[1], s0Next)
        self.assertEqual(notes[0], s[1].previous())

        self.assertEqual(id(notes[5]), id(s[4].next()))
        self.assertEqual(id(notes[3]), id(s[4].previous()))

        # if a note has more than one site, what happens
        self.assertEqual(notes[6], s.notes[5].next())
        self.assertEqual(notes[7], s.notes[6].next())

    def testNextB(self):
        m1 = stream.Measure()
        m1.number = 1
        n1 = note.Note('C')
        m1.append(n1)

        m2 = stream.Measure()
        m2.number = 2
        n2 = note.Note('D')
        m2.append(n2)

        # n1 cannot be connected to n2 as no common site
        n1next = n1.next()
        self.assertEqual(n1next, None)

        p1 = stream.Part()
        p1.append(m1)
        p1.append(m2)
        n1next = n1.next()
        self.assertEqual(n1next, m2)
        self.assertEqual(n1.next(note.Note), n2)

    def testNextC(self):
        s = corpus.parse('bwv66.6')

        # getting time signature and key sig
        p1 = s.parts[0]
        nLast = p1.flatten().notes[-1]
        self.assertEqual(str(nLast.previous(meter.TimeSignature)),
                         '<music21.meter.TimeSignature 4/4>')
        self.assertEqual(str(nLast.previous(key.KeySignature)),
                         'f# minor')

        # iterating at the Measure level, showing usage of flattenLocalSites
        measures = p1.getElementsByClass(stream.Measure).stream()
        m3 = measures[3]
        m3prev = m3.previous()
        self.assertEqual(m3prev, measures[2][-1])
        m3Prev2 = measures[3].previous().previous()
        self.assertEqual(m3Prev2, measures[2][-2])
        self.assertTrue(m3Prev2.expressions)  # fermata

        m3n = measures[3].next()
        self.assertEqual(m3n, measures[3][0])  # same as next line
        self.assertEqual(measures[3].next('Note'), measures[3].notes[0])
        self.assertEqual(m3n.next(), measures[3][1])

        m3nm = m3.next('Measure')
        m3nn = m3nm.next('Measure')
        self.assertEqual(m3nn, measures[5])
        m3nnn = m3nn.next('Measure')
        self.assertEqual(m3nnn, measures[6])

        self.assertEqual(measures[3].previous('Measure').previous('Measure'), measures[1])
        m0viaPrev = measures[3].previous('Measure').previous('Measure').previous('Measure')
        self.assertEqual(m0viaPrev, measures[0])

        m0viaPrev.activeSite = s.parts[0]  # otherwise there are no instruments...
        sopranoInst = m0viaPrev.previous()
        self.assertEqual(str(sopranoInst), 'P1: Soprano: Instrument 1')

        # set active site back to measure stream...
        self.assertEqual(str(measures[0].previous()), str(p1))

    def testActiveSiteCopyingA(self):
        n1 = note.Note()
        s1 = stream.Stream()
        s1.append(n1)
        self.assertEqual(n1.activeSite, s1)

        n2 = copy.deepcopy(n1)
        self.assertIs(n2._activeSite, None)
        self.assertIs(n2.derivation.origin.activeSite, s1)

    def testSpannerSites(self):
        n1 = note.Note('C4')
        n2 = note.Note('D4')
        sp1 = spanner.Slur(n1, n2)
        ss = n1.getSpannerSites()
        self.assertEqual(ss, [sp1])

        # test same for inherited classes and multiple sites, in order...
        sp2 = dynamics.Crescendo(n2, n1)
        # can return in arbitrary order esp. if speed is fast...
        # TODO: use Ordered Dict.
        self.assertEqual(set(n2.getSpannerSites()), {sp1, sp2})

        # Optionally a class name or list of class names can be
        # specified and only Spanners of that class will be returned

        sp3 = dynamics.Diminuendo(n1, n2)
        self.assertEqual(n2.getSpannerSites('Diminuendo'), [sp3])

        # A larger class name can be used to get all subclasses:

        self.assertEqual(set(n2.getSpannerSites('DynamicWedge')), {sp2, sp3})
        self.assertEqual(set(n2.getSpannerSites(['Slur', 'Diminuendo'])), {sp1, sp3})

        # The order spanners are returned is generally the order that they were
        # added, but that is not guaranteed, so for safety's sake, use set comparisons:

        self.assertEqual(set(n2.getSpannerSites(['Slur', 'Diminuendo'])), {sp3, sp1})

    def testContextSitesA(self):
        self.maxDiff = None
        c = corpus.parse('bwv66.6')
        c.id = 'bach'
        n = c[2][4][2]
        self.assertEqual(repr(n), '<music21.note.Note G#>')
        siteList = []
        for y in n.contextSites():
            yTup = (y.site, y.offset, y.recurseType)
            siteList.append(repr(yTup))
        self.assertEqual(
            siteList,
            ['(<music21.stream.Measure 3 offset=9.0>, 0.5, <RecursionType.ELEMENTS_FIRST>)',
             '(<music21.stream.Part Alto>, 9.5, <RecursionType.FLATTEN>)',
             '(<music21.stream.Score bach>, 9.5, <RecursionType.ELEMENTS_ONLY>)']
        )

        m = c[2][4]
        self.assertEqual(repr(m), '<music21.stream.Measure 3 offset=9.0>')

        siteList = []
        for y in m.contextSites():
            yTup = (y.site, y.offset, y.recurseType)
            siteList.append(repr(yTup))
        self.assertEqual(
            siteList,
            ['(<music21.stream.Measure 3 offset=9.0>, 0.0, <RecursionType.ELEMENTS_FIRST>)',
             '(<music21.stream.Part Alto>, 9.0, <RecursionType.FLATTEN>)',
             '(<music21.stream.Score bach>, 9.0, <RecursionType.ELEMENTS_ONLY>)']
        )

        m2 = copy.deepcopy(m)
        m2.number = 3333
        siteList = []
        for y in m2.contextSites():
            yTup = (y.site, y.offset, y.recurseType)
            siteList.append(repr(yTup))
        self.assertEqual(
            siteList,
            ['(<music21.stream.Measure 3333 offset=0.0>, 0.0, <RecursionType.ELEMENTS_FIRST>)',
             '(<music21.stream.Measure 3 offset=9.0>, 0.0, <RecursionType.ELEMENTS_FIRST>)',
             '(<music21.stream.Part Alto>, 9.0, <RecursionType.FLATTEN>)',
             '(<music21.stream.Score bach>, 9.0, <RecursionType.ELEMENTS_ONLY>)']
        )
        siteList = []

        cParts = c.parts.stream()  # need this otherwise it could possibly be garbage collected.
        cParts.id = 'partStream'  # to make it easier to see below, will be cached...
        pTemp = cParts[1]
        m3 = pTemp.measure(3)
        self.assertIs(m, m3)
        for y in m3.contextSites():
            yTup = (y.site, y.offset, y.recurseType)
            siteList.append(repr(yTup))

        self.assertEqual(
            siteList,
            ['(<music21.stream.Measure 3 offset=9.0>, 0.0, <RecursionType.ELEMENTS_FIRST>)',
             '(<music21.stream.Part Alto>, 9.0, <RecursionType.FLATTEN>)',
             '(<music21.stream.Score partStream>, 9.0, <RecursionType.ELEMENTS_ONLY>)',
             '(<music21.stream.Score bach>, 9.0, <RecursionType.ELEMENTS_ONLY>)']
        )

    def testContextSitesB(self):
        p1 = stream.Part()
        p1.id = 'p1'
        m1 = stream.Measure()
        m1.number = 1
        n = note.Note()
        m1.append(n)
        p1.append(m1)
        siteList = []
        for y in n.contextSites():
            siteList.append(repr(y.site))
        self.assertEqual(siteList, ['<music21.stream.Measure 1 offset=0.0>',
                                    '<music21.stream.Part p1>'])
        p2 = stream.Part()
        p2.id = 'p2'
        m2 = stream.Measure()
        m2.number = 2
        m2.append(n)
        p2.append(m2)

        siteList = []
        for y in n.contextSites():
            siteList.append(repr(y.site))
        self.assertEqual(siteList, ['<music21.stream.Measure 2 offset=0.0>',
                                    '<music21.stream.Part p2>',
                                    '<music21.stream.Measure 1 offset=0.0>',
                                    '<music21.stream.Part p1>'])

        siteList = []
        for y in n.contextSites(sortByCreationTime=True):
            siteList.append(repr(y.site))
        self.assertEqual(siteList, ['<music21.stream.Measure 2 offset=0.0>',
                                    '<music21.stream.Part p2>',
                                    '<music21.stream.Measure 1 offset=0.0>',
                                    '<music21.stream.Part p1>'])

        siteList = []
        for y in n.contextSites(sortByCreationTime='reverse'):
            siteList.append(repr(y.site))
        self.assertEqual(siteList, ['<music21.stream.Measure 1 offset=0.0>',
                                    '<music21.stream.Part p1>',
                                    '<music21.stream.Measure 2 offset=0.0>',
                                    '<music21.stream.Part p2>'])

    def testContextSitesVoices(self):
        v1_n1 = note.Note('D')
        v2_n1 = note.Note('E')
        v1 = stream.Voice()
        v1.insert(0, v1_n1)
        v2 = stream.Voice()
        v2.insert(1, v2_n1)
        _ = stream.Measure([v1, v2])
        self.assertIs(v1_n1.activeSite, v1)
        # This was finding the E in voice 2
        self.assertIsNone(v1_n1.next(note.GeneralNote, activeSiteOnly=True))

    def testContextSitesDerivations(self):
        m = stream.Measure([note.Note(), note.Note()])
        mCopy = m.makeNotation()
        mCopy.remove(mCopy.notes.last())
        self.assertIsNone(mCopy.notes.first().next(activeSiteOnly=True))

    def testContextInconsistentArguments(self):
        obj = Music21Object()
        with self.assertRaises(ValueError):
            obj.getContextByClass(
                ElementWrapper,
                priorityTargetOnly=True,
                followDerivation=True
            )

# great isolation test, but no asserts for now...
#     def testPreviousA(self):
#         s = corpus.parse('bwv66.6')
#         o = s.parts[0].getElementsByClass(stream.Measure)[2][1]
#         i = 20
#         while o and i:
#             print(o)
#             if isinstance(o, stream.Part):
#                 pass
#             o = o.previous()
#             i -= 1
#

#     def testPreviousB(self):
#         '''
#         fixed a memo problem which could cause .previous() to run forever
#         on flat/derived streams.
#         '''
#         s = corpus.parse('luca/gloria')
#         sf = s.flatten()
#         o = sf[1]
#         # o = s[2]
#         i = 200
#         while o and i:
#             print(o, o.activeSite, o.sortTuple().shortRepr())
#             o = o.previous()
# #            cc = s._cache
# #             for x in cc:
# #                 if x.startswith('elementTree'):
# #                     print(repr(cc[x]))
#             i -= 1

    def testPreviousAfterDeepcopy(self):
        e1 = note.Note('C')
        e2 = note.Note('D')
        s = stream.Stream()
        s.insert(0, e1)
        s.insert(1, e2)
        self.assertIs(e2.previous(), e1)
        self.assertIs(s[1].previous(), e1)
        s2 = copy.deepcopy(s)
        self.assertIs(s2[1].previous(), s2[0])

        e1 = note.Note('C')
        e2 = note.Note('D')

        v = stream.Part()
        m1 = stream.Measure()
        m1.number = 1
        m1.insert(0, e1)
        v.insert(0, m1)
        m2 = stream.Measure()
        m2.insert(0, e2)
        m2.number = 2
        v.append(m2)
        self.assertIs(e2.previous('Note'), e1)
        self.assertIs(v[1][0], e2)
        self.assertIs(v[1][0].previous('Note'), e1)

        w = v.transpose('M3')  # same as deepcopy,
        # but more instructive in debugging since pitches change...
        #    w = copy.deepcopy(v)
        eCopy1 = w[0][0]
        self.assertEqual(eCopy1.pitch.name, 'E')
        eCopy2 = w[1][0]
        self.assertEqual(eCopy2.pitch.name, 'F#')
        prev = eCopy2.previous('Note')
        self.assertIs(prev, eCopy1)

    def testWarnCopyingIds(self):
        '''
        It is not recommended to copy .id values between objects without being
        sure the original .id value is not a memory location.
        '''
        obj = Music21Object()
        obj2 = Music21Object()
        msg = 'Setting an ID that could be mistaken for a memory location '
        msg += f'is discouraged: got {obj.id}'
        with self.assertWarnsRegex(Warning, msg):
            obj2.id = obj.id


# -------------------------------------------
if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
