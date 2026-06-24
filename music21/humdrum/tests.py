# ------------------------------------------------------------------------------
# Name:         humdrum/tests.py
# Purpose:      Tests for the humdrum spineParser
#
# Authors:      Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2010-2026 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Tests for :mod:`music21.humdrum.spineParser`.

The tests live in this companion module rather than at the bottom of
spineParser.py because spineParser is large; only the testCopyAndDeepcopy
test stays in spineParser so its `globals()` picks up the parser classes
for the deep-copy round trip.
'''
from __future__ import annotations

import re
import typing as t
import unittest

from music21 import bar
from music21 import common
from music21 import dynamics
from music21 import expressions
from music21 import note
from music21 import roman
from music21 import stream
from music21.humdrum import testFiles
from music21.humdrum.spineParser import (
    GlobalComment,
    GlobalReference,
    HumdrumDataCollection,
    KernSpine,
    SpineComment,
    SpineEvent,
    flavors,
    hdStringToMeasure,
    kernTandemToObject,
)


class Test(unittest.TestCase):
    def testLoadMazurka(self):
        # hf1 = HumdrumFile('d:/web/eclipse/music21misc/mazurka06-2.krn')

        hf1 = HumdrumDataCollection(testFiles.mazurka6)
        hf1.parse()

        # hf1 = HumdrumFile('d:/web/eclipse/music21misc/ojibway.krn')
        # for thisEventCollection in hf1.eventCollections:
        #     ev = thisEventCollection.getSpineEvent(0).contents
        #     if ev is not None:
        #         print(ev)
        #     else:
        #         print('NONE')
        #
        # for mySpine in hf1.spineCollection:
        #     print('\n\n***NEW SPINE: No. ' + str(mySpine.id) + ' parentSpine: '
        #         + str(mySpine.parentSpine) + ' childSpines: ' + str(mySpine.childSpines))
        #     print(mySpine.spineType)
        #     for childSpinesSpine in mySpine.childSpinesSpines():
        #         print(str(childSpinesSpine.id) + ' *** testing spineCollection code ***')
        #     for thisEvent in mySpine:
        #         print(thisEvent.contents)
        spine5 = hf1.spineCollection.getSpineById(5)
        self.assertEqual(spine5.id, 5)
        self.assertEqual(spine5.parentSpine.id, 1)

        spine1 = hf1.spineCollection.getSpineById(1)
        spine1Children = [cs.id for cs in spine1.childSpines]
        self.assertEqual(spine1Children,
                         [5, 6, 9, 10, 13, 14, 23, 24, 27, 28, 31, 32, 35, 36, 39, 40])

        self.assertEqual(spine5.spineType, 'kern')
        self.assertIsInstance(spine5, KernSpine)

    def testSingleNote(self):
        # noinspection SpellCheckingInspection
        a = SpineEvent('40..ccccc##_wtLLK~v/')
        b = a.toNote()
        self.assertEqual(b.pitch.accidental.name, 'double-sharp')
        self.assertEqual(b.duration.dots, 0)
        self.assertEqual(b.duration.tuplets[0].durationNormal.dots, 2)

    def testPartialBeamDirections(self):
        # lowercase `k` is a partial beam to the left, uppercase `K` to the right
        left = SpineEvent('8ccLk').toNote()
        self.assertEqual([(bm.type, bm.direction) for bm in left.beams.beamsList],
                         [('start', None), ('partial', 'left')])
        right = SpineEvent('8ccLK').toNote()
        self.assertEqual([(bm.type, bm.direction) for bm in right.beams.beamsList],
                         [('start', None), ('partial', 'right')])

    def testGraceNoteKeepsWrittenDuration(self):
        '''
        A single `q` is a slashed grace note that keeps its written duration
        '''
        n = SpineEvent('16ccq').toNote()
        self.assertTrue(n.duration.isGrace)
        self.assertEqual(n.duration.type, '16th')
        self.assertTrue(n.duration.slash)

    def testUnslashedGraceNote(self):
        '''
        `qq` or `Q` marks two kinds of unslashed grace note.
        '''
        for contents in ('16ccqq', '16ccQ'):
            n = SpineEvent(contents).toNote()
            self.assertTrue(n.duration.isGrace)
            self.assertEqual(n.duration.type, '16th')
            self.assertFalse(n.duration.slash)

    def testGraceNoteWithoutDurationDefaultsToEighth(self):
        '''
        With no written duration a grace note defaults to an eighth.
        '''
        n = SpineEvent('ccq').toNote()
        self.assertTrue(n.duration.isGrace)
        self.assertEqual(n.duration.type, 'eighth')
        self.assertTrue(n.duration.slash)

    def testGraceNoteFromProcessNoteEvent(self):
        ks = KernSpine()
        ks.setup()
        # noinspection SpellCheckingInspection
        a = ks.processNoteEvent('4Cq')
        self.assertEqual(a.duration.type, 'quarter')
        self.assertEqual(a.duration.slash, True)
        # noinspection SpellCheckingInspection
        a = ks.processNoteEvent('16Cqq')
        self.assertEqual(a.duration.type, '16th')
        self.assertEqual(a.duration.slash, False)

    def testChordFromProcessChordEvent(self):
        ks = KernSpine()
        ks.setup()
        c = ks.processChordEvent('8C 8E')
        self.assertEqual(len(c.notes), 2)
        self.assertEqual(c.notes[0].duration, c.duration)
        c = ks.processChordEvent('8C E')
        self.assertEqual(c.notes[0].duration, c.notes[1].duration)

    def testChordNoteInheritsDefaultDuration(self):
        '''
        A note with no written duration takes the given defaultDurationOrNone
        (the first note's duration in a chord), sharing the same Duration object;
        a note with its own written duration ignores it.
        '''
        ks = KernSpine()
        ks.setup()
        c = ks.processChordEvent('8C E 2G')
        self.assertIs(c.duration, c[0].duration)
        self.assertEqual(c.notes[0].duration.type, 'eighth')
        self.assertIs(c[0].duration, c[1].duration)
        self.assertIsNot(c[0].duration, c[2].duration)
        self.assertEqual(c.notes[2].duration.type, 'half')

    def testPartiallyNotatedChordDurations(self):
        '''
        In a kern chord whose later notes omit a duration (`8C E G`), every note
        takes the first note's duration instead of defaulting to a quarter; a
        chord that notates each duration (`8C 2E 2G`) keeps them.
        '''
        krn = re.sub(r'\s\s\s\s+', '\t', r'''
**kern
*M4/4
=1
8C E G
8C 2E 2G
2r
*-
''')
        hdc = HumdrumDataCollection(krn)
        hdc.parse()
        chords = list(hdc.stream.recurse().getElementsByClass('Chord'))
        self.assertEqual(len(chords), 2)
        partial, fullyNotated = chords
        self.assertEqual([n.duration.type for n in partial],
                         ['eighth', 'eighth', 'eighth'])
        self.assertEqual([n.duration.type for n in fullyNotated],
                         ['eighth', 'half', 'half'])

    def testChordSharesMatchingDurationObjects(self):
        '''
        Chord notes that omit or repeat the first note's duration share its
        Duration object; a note with a different duration keeps its own (e.g. the
        held top voice in `4G 4e 2g`).
        '''
        krn = re.sub(r'\s\s\s\s+', '\t', r'''
**kern
*M4/4
=1
8C 8E 8G
4G 4e 2g
2r
*-
''')
        hdc = HumdrumDataCollection(krn)
        hdc.parse()
        chords = list(hdc.stream.recurse().getElementsByClass('Chord'))
        self.assertEqual(len(chords), 2)
        matched, mixed = chords

        # 8C 8E 8G: all three notes share one Duration object
        matchedDurations = [n.duration for n in matched.notes]
        self.assertEqual(len({id(d) for d in matchedDurations}), 1)

        # 4G 4e 2g: the two quarters share one object, the half is its own
        mixedDurations = [n.duration for n in mixed.notes]
        quarters = [d for d in mixedDurations if d.type == 'quarter']
        halves = [d for d in mixedDurations if d.type == 'half']
        self.assertEqual(len(quarters), 2)
        self.assertEqual(len(halves), 1)
        self.assertEqual(len({id(d) for d in quarters}), 1)

    def testMeasureBoundaries(self):
        m0 = stream.Measure()
        m1 = hdStringToMeasure('=29a;:|:', m0)
        self.assertEqual(m1.number, 29)
        self.assertEqual(m1.numberSuffix, 'a')
        # ':|:' produces an end-Repeat on m0's right and a start-Repeat on m1's left.
        self.assertIsInstance(m0.rightBarline, bar.Repeat)
        self.assertEqual(m0.rightBarline.direction, 'end')
        self.assertEqual(m0.rightBarline.type, 'regular')
        self.assertIsInstance(m0.rightBarline.pause, expressions.Fermata)
        self.assertIsInstance(m1.leftBarline, bar.Repeat)
        self.assertEqual(m1.leftBarline.direction, 'start')
        self.assertEqual(m1.leftBarline.type, 'regular')

    def testMeterBreve(self):
        m = kernTandemToObject('*M3/1')
        self.assertEqual(str(m), '<music21.meter.TimeSignature 3/1>')
        m = kernTandemToObject('*M3/0')
        self.assertEqual(str(m), '<music21.meter.TimeSignature 6/1>')
        m = kernTandemToObject('*M3/00')
        self.assertEqual(str(m), '<music21.meter.TimeSignature 12/1>')
        m = kernTandemToObject('*M3/000')
        self.assertEqual(str(m), '<music21.meter.TimeSignature 24/1>')

    def x_testFakePiece(self):
        '''
        test loading a fake piece with spine paths, lyrics, dynamics, etc.
        '''
        hdc = HumdrumDataCollection(testFiles.fakeTest)
        hdc.parse()
        ms = hdc.stream
        ms.show()

    def testSpineMazurka(self):
        # hf1 = HumdrumFile('d:/web/eclipse/music21misc/mazurka06-2.krn')
        hf1 = HumdrumDataCollection(testFiles.mazurka6)
        # hf1 = HumdrumDataCollection(testFiles.ojibway)
        # hf1 = HumdrumDataCollection(testFiles.schubert)
        # hf1 = HumdrumDataCollection(testFiles.ivesSpring)
        # hf1 = HumdrumDataCollection(testFiles.sousaStars)  # parse errors b/c of graces
        hf1.parse()
        masterStream = hf1.stream
        # for spineX in hf1.spineCollection:
        #     spineX.stream.id = f'spine {spineX.id}'
        #     masterStream.append(spineX.stream)
        # self.assertTrue(common.whitespaceEqual
        #                  (common.stripAddresses(expectedOutput),
        #                   common.stripAddresses(masterStream._reprText())))
        # print(common.stripAddresses(expectedOutput))
        # print(common.stripAddresses(masterStream.recurseRepr()))

        # humdrum type problem: how many G#s start on beat 2 of a measure?
        gSharpCount = 0
        # masterStream.show('text')
        for n in masterStream.recurse():
            if hasattr(n, 'pitch') and n.pitch.name == 'G#':
                if n.beat == 2:  # beat doesn't work :-(
                    gSharpCount += 1
            elif hasattr(n, 'pitches'):
                for p in n.pitches:
                    if p.name == 'G#' and n.beat == 2:
                        gSharpCount += 1
        # masterStream.show()
        self.assertEqual(gSharpCount, 86)
        # masterStream.show()
        # masterStream.show('text')

    def testParseSineNomine(self):
        from music21 import converter
        parserPath = common.getSourceFilePath() / 'humdrum'
        sineNominePath = parserPath / 'Missa_Sine_nomine-Kyrie.krn'
        unused_myScore = converter.parse(sineNominePath)
        # unused_myScore.show('text')

    def testSplitSpines(self):
        hf1 = HumdrumDataCollection(testFiles.splitSpines2)
        hf1.parse()
        masterStream = hf1.stream
        self.assertTrue(masterStream.parts[0].measure(4).hasVoices())
        self.assertFalse(masterStream.parts[0].measure(5).hasVoices())

    def x_testMoveDynamics(self):
        hf1 = HumdrumDataCollection(testFiles.fakeTest)
        hf1.parse()
        # hf1.spineCollection.attachNonKernEvents()
        unused_s = hf1.stream
        # unused_s.show('text')

    def testLyricsInSpine(self):
        from music21 import text
        hf1 = HumdrumDataCollection(testFiles.fakeTest)
        hf1.parse()
        # hf1.spineCollection.attachNonKernEvents()
        s = hf1.stream
        lyrics = text.assembleLyrics(s)
        # noinspection SpellCheckingInspection
        self.assertEqual(lyrics, 'Magijago ickewyan')

    def testSplitSpines2(self):
        '''
        Currently this does not work since a second split on a stream that
        already resulted from a split does not parse properly.  Shows up also
        in strangeWTCOpening, below.
        '''
        hf1 = HumdrumDataCollection(testFiles.splitLots)
        hf1.parse()
        unused_masterStream = hf1.stream

    def testParseStrangeSplit(self):
        hf1 = HumdrumDataCollection(testFiles.strangeWTCOpening)
        unused_masterStream = hf1.stream

    def testSplitAfterBarline(self):
        '''
        2/4 piece: m1 has one half note in a single spine; m2 splits into two
        spines (split indicator immediately *after* the =2 barline) with a half
        note on each, merges back to one spine before =3, and m3 has a single
        half note.
        '''
        krn = re.sub(r'\s\s\s\s+', '\t', r'''
**kern
*M2/4
=1
2c
=2
*^
2d    2e
*v    *v
=3
2f
*-
''')
        hdc = HumdrumDataCollection(krn)
        hdc.parse()
        s = hdc.stream

        self.assertEqual(len(s.parts), 1)
        measures = list(s.parts[0].getElementsByClass(stream.Measure))
        self.assertEqual([m.number for m in measures], [1, 2, 3])
        self.assertEqual([m.duration.quarterLength for m in measures], [2.0, 2.0, 2.0])

        m1, m2, m3 = measures
        self.assertFalse(m1.hasVoices())
        self.assertEqual([n.pitch.name for n in m1.notes], ['C'])

        self.assertTrue(m2.hasVoices())
        self.assertEqual(len(m2.voices), 2)
        self.assertEqual(
            sorted(n.pitch.name for v in m2.voices for n in v.notes),
            ['D', 'E'],
        )

        self.assertFalse(m3.hasVoices())
        self.assertEqual([n.pitch.name for n in m3.notes], ['F'])

    def testSplitBeforeBarline(self):
        '''
        Same shape as testSplitAfterBarline but with the spine split placed
        *before* the =2 barline (the barline therefore appears within both new
        spines).  Humdrum syntax permits this; only adjacency rules constrain
        spine path indicators.
        '''
        krn = re.sub(r'\s\s\s\s+', '\t', r'''
**kern
*M2/4
=1
2c
*^
=2    =2
2d    2e
*v    *v
=3
2f
*-
''')
        hdc = HumdrumDataCollection(krn)
        hdc.parse()
        s = hdc.stream

        self.assertEqual(len(s.parts), 1)
        measures = list(s.parts[0].getElementsByClass(stream.Measure))
        self.assertEqual([m.number for m in measures], [1, 2, 3])
        self.assertEqual([m.duration.quarterLength for m in measures], [2.0, 2.0, 2.0])

        m1, m2, m3 = measures
        self.assertFalse(m1.hasVoices())
        self.assertEqual([n.pitch.name for n in m1.notes], ['C'])

        self.assertTrue(m2.hasVoices())
        self.assertEqual(len(m2.voices), 2)
        self.assertEqual(
            sorted(n.pitch.name for v in m2.voices for n in v.notes),
            ['D', 'E'],
        )

        self.assertFalse(m3.hasVoices())
        self.assertEqual([n.pitch.name for n in m3.notes], ['F'])

    def testSplitMergeImmediateResplit(self):
        '''
        2/4 piece: m1 has one half note in a single spine; m2 splits into two
        spines (half note on each), then merges back to one spine at the end of
        m2; m3 immediately splits again into two spines (half note on each)
        and the piece ends without re-merging.

        Expected layout: one Part with three Measures, each two quarters long;
        m1 has no voices, m2 and m3 each have two voices with one half note
        each.
        '''
        krn = re.sub(r'\s\s\s\s+', '\t', r'''
**kern
*M2/4
=1
2c
=2
*^
2d    2e
*v    *v
=3
*^
2f    2g
*-    *-
''')
        hdc = HumdrumDataCollection(krn)
        hdc.parse()
        s = hdc.stream

        self.assertEqual(len(s.parts), 1)
        measures = list(s.parts[0].getElementsByClass(stream.Measure))
        self.assertEqual([m.number for m in measures], [1, 2, 3])
        self.assertEqual([m.duration.quarterLength for m in measures], [2.0, 2.0, 2.0])

        m1, m2, m3 = measures
        self.assertFalse(m1.hasVoices())
        self.assertEqual([n.pitch.name for n in m1.notes], ['C'])

        self.assertTrue(m2.hasVoices())
        self.assertEqual(len(m2.voices), 2)
        self.assertEqual(
            sorted(n.pitch.name for v in m2.voices for n in v.notes),
            ['D', 'E'],
        )

        self.assertTrue(m3.hasVoices())
        self.assertEqual(len(m3.voices), 2)
        self.assertEqual(
            sorted(n.pitch.name for v in m3.voices for n in v.notes),
            ['F', 'G'],
        )

    def testDynamAttachedAligned(self):
        '''
        ``**dynam`` events on the same line as a kern note attach at that note's
        offset.  Sanity-check companion to testDynamAttachedMisaligned.
        '''
        krn = re.sub(r'\s\s\s\s+', '\t', r'''
**kern    **dynam
*staff1    *staff1
*M4/4     *
=1        =1
2c        f
2d        p
=2        =2
4e        sf
4f        .
4g        .
4a        .
*-        *-
''')
        hdc = HumdrumDataCollection(krn)
        hdc.parse()
        found = [(d.value, float(d.getOffsetInHierarchy(hdc.stream)))
                 for d in hdc.stream.recurse().getElementsByClass(dynamics.Dynamic)]
        self.assertEqual(found, [('f', 0.0), ('p', 2.0), ('sf', 4.0)])

    @unittest.skip('Known pre-existing gap; see TODO in '
                   'SpineCollection.attachNonKernEvents.')
    def testDynamAttachedMisaligned(self):
        '''
        A ``**dynam`` event on a line where the kern column has '.' (no new note
        event) should still attach -- to the stream at the offset of the most
        recently-sounding note.  Currently fails: misaligned dynamics are
        silently dropped.  See TODO in `SpineCollection.attachNonKernEvents`.
        '''
        krn = re.sub(r'\s\s\s\s+', '\t', r'''
**kern    **dynam
*staff1    *staff1
*M4/4     *
=1        =1
2c        f
.         p
2d        .
=2        =2
4e        sf
4f        .
4g        .
4a        .
*-        *-
''')
        hdc = HumdrumDataCollection(krn)
        hdc.parse()
        found = [(d.value, float(d.getOffsetInHierarchy(hdc.stream)))
                 for d in hdc.stream.recurse().getElementsByClass(dynamics.Dynamic)]
        # 'p' occurs while C (offset 0, half note) is sustaining; falls back to
        # the C's offset.
        self.assertEqual(found, [('f', 0.0), ('p', 0.0), ('sf', 4.0)])

    @unittest.skip('Known pre-existing gap; see TODO in '
                   'SpineCollection.attachNonKernEvents.')
    def testHarmAttachedMisaligned(self):
        '''
        A ``**harm`` event on a line where the kern column has '.' should still
        attach -- to the stream at the offset of the most recently-sounding
        note.  Currently fails: misaligned harm events are silently dropped.
        See TODO in `SpineCollection.attachNonKernEvents`.
        '''
        krn = re.sub(r'\s\s\s\s+', '\t', r'''
**kern    **harm
*staff1    *staff1
*M4/4     *
*C:       *C:
=1        =1
2c        I
.         V
2g        .
=2        =2
4f        IV
4g        V
4a        vi
4c        I
*-        *-
''')
        hdc = HumdrumDataCollection(krn)
        hdc.parse()
        found = [(r.figure, float(r.getOffsetInHierarchy(hdc.stream)))
                 for r in hdc.stream.recurse().getElementsByClass(roman.RomanNumeral)]
        # 'V' on the dot line falls back to the C's offset (still sustaining).
        self.assertEqual(
            found,
            [('I', 0.0), ('V', 0.0), ('IV', 4.0), ('V', 5.0), ('vi', 6.0), ('I', 7.0)],
        )

    def testBlankLinesPreserveSplitParse(self):
        '''
        Blank lines should not affect parsing.  Same shape as
        testSplitAfterBarline but with blank lines sprinkled throughout.
        '''
        krn = re.sub(r'\s\s\s\s+', '\t', r'''

**kern
*M2/4

=1
2c

=2
*^

2d    2e
*v    *v

=3

2f
*-
''')
        hdc = HumdrumDataCollection(krn)
        hdc.parse()
        s = hdc.stream

        self.assertEqual(len(s.parts), 1)
        measures = list(s.parts[0].getElementsByClass(stream.Measure))
        self.assertEqual([m.number for m in measures], [1, 2, 3])
        self.assertEqual([m.duration.quarterLength for m in measures], [2.0, 2.0, 2.0])

        m1, m2, m3 = measures
        self.assertEqual([n.pitch.name for n in m1.notes], ['C'])
        self.assertEqual(
            sorted(n.pitch.name for v in m2.voices for n in v.notes),
            ['D', 'E'],
        )
        self.assertEqual([n.pitch.name for n in m3.notes], ['F'])

    def testBlankLinesPreserveDynamAndHarm(self):
        '''
        Blank lines mixed into a kern + dynam + harm piece should not affect
        which events attach where.
        '''
        krn = re.sub(r'\s\s\s\s+', '\t', r'''
**kern    **dynam    **harm
*staff1    *staff1    *staff1
*M4/4     *         *
*C:       *         *C:

=1        =1        =1
2c        f         I

2d        p         V
=2        =2        =2

4e        sf        I
4f        .         IV
4g        .         V
4a        .         vi
*-        *-        *-
''')
        hdc = HumdrumDataCollection(krn)
        hdc.parse()
        s = hdc.stream
        dyn = [(d.value, float(d.getOffsetInHierarchy(s)))
               for d in s.recurse().getElementsByClass(dynamics.Dynamic)]
        harm = [(r.figure, float(r.getOffsetInHierarchy(s)))
                for r in s.recurse().getElementsByClass(roman.RomanNumeral)]
        self.assertEqual(dyn, [('f', 0.0), ('p', 2.0), ('sf', 4.0)])
        self.assertEqual(
            harm,
            [('I', 0.0), ('V', 2.0), ('I', 4.0), ('IV', 5.0), ('V', 6.0), ('vi', 7.0)],
        )

    def testLyricsCorrectlyAligned(self):
        '''
        Verify that each lyric syllable from a ``**text`` spine attaches to the
        kern note on the same line.  Existing testLyricsInSpine only checks
        the assembled lyric string; this checks the per-note mapping.
        '''
        krn = re.sub(r'\s\s\s\s+', '\t', r'''
**kern    **text
*staff1    *staff1
*M4/4     *
=1        =1
4c        Ma
4d        gi
4e        ja
4f        go
*-        *-
''')
        hdc = HumdrumDataCollection(krn)
        hdc.parse()
        notesAndLyrics = [(n.pitch.name, n.lyric)
                          for n in hdc.stream.recurse().notes]
        self.assertEqual(
            notesAndLyrics,
            [('C', 'Ma'), ('D', 'gi'), ('E', 'ja'), ('F', 'go')],
        )

    def testSpineComments(self):
        hf1 = HumdrumDataCollection(testFiles.fakeTest)
        hf1.parse()
        s = hf1.stream  # .show()
        p = s.parts[2]  # last part has a comment
        comments = []
        for c in p[SpineComment]:
            comments.append(c.comment)
        self.assertTrue('spine comment' in comments)
        # s.show('text')

    def testHarmSpineDegrees(self):
        hf1 = HumdrumDataCollection(testFiles.harmScaleDegrees)
        hf1.parse()
        s = hf1.stream
        groundTruth = {
            0.0: ('I in C major', [0, 4, 7], 'C', 'C', 53, False),
            1.0: ('ii in C major', [2, 5, 9], 'D', 'D', 53, False),
            2.0: ('iii in C major', [4, 7, 11], 'E', 'E', 53, False),
            3.0: ('IV in C major', [5, 9, 0], 'F', 'F', 53, False),
            4.0: ('I64 in C major', [7, 0, 4], 'C', 'G', 64, False),
            5.0: ('V in C major', [7, 11, 2], 'G', 'G', 53, False),
            6.0: ('vi in C major', [9, 0, 4], 'A', 'A', 53, False),
            7.0: ('V6 in C major', [11, 2, 7], 'G', 'B', 6, False),
            8.0: ('viio65/i in C major', [2, 5, 8, 11], 'B', 'D', 65, True),
            9.0: ('I in C major', [0, 4, 7], 'C', 'C', 53, False),
            11.0: ('I in C major', [0, 4, 7], 'C', 'C', 53, False),
            12.0: ('i in c minor', [0, 3, 7], 'C', 'C', 53, False),
            13.0: ('iio in c minor', [2, 5, 8], 'D', 'D', 53, False),
            14.0: ('III in c minor', [3, 7, 10], 'E-', 'E-', 53, False),
            15.0: ('N6 in c minor', [5, 8, 1], 'D-', 'F', 6, False),
            16.0: ('i64 in c minor', [7, 0, 3], 'C', 'G', 64, False),
            17.0: ('V in c minor', [7, 11, 2], 'G', 'G', 53, False),
            18.0: ('It6 in c minor', [8, 0, 6], 'F#', 'A-', 6, False),
            20.0: ('V in c minor', [7, 11, 2], 'G', 'G', 53, False),
            21.0: ('Fr43 in c minor', [8, 0, 2, 6], 'D', 'A-', 43, True),
            23.0: ('V in c minor', [7, 11, 2], 'G', 'G', 53, False),
            24.0: ('Ger65 in c minor', [8, 0, 3, 6], 'F#', 'A-', 65, True),
            27.0: ('iv in c minor', [5, 8, 0], 'F', 'F', 53, False),
            30.0: ('V in c minor', [7, 11, 2], 'G', 'G', 53, False),
            32.0: ('V in c minor', [7, 11, 2], 'G', 'G', 53, False),
            33.0: ('I in c minor', [0, 4, 7], 'C', 'C', 53, False)
        }
        for harm in s.flatten().getElementsByClass(roman.RomanNumeral):
            figureAndKey = harm.figureAndKey
            pitchClasses = harm.pitchClasses
            root = harm.root().name
            bass = harm.bass().name
            inversionName = harm.inversionName()
            isSeventh = harm.isSeventh()
            assertTuple = (
                figureAndKey,
                pitchClasses,
                root,
                bass,
                inversionName,
                isSeventh
            )
            self.assertEqual(assertTuple, groundTruth[harm.offset])

    def testHarmSpineSevenths(self):
        hf1 = HumdrumDataCollection(testFiles.harmSevenths)
        hf1.parse()
        s = hf1.stream
        groundTruth = {
            0.0: ('I7 in C major', [0, 4, 7, 11], 'C', 'C', 7, True),
            1.0: ('IV7 in C major', [5, 9, 0, 4], 'F', 'F', 7, True),
            2.0: ('viio7 in C major', [11, 2, 5, 8], 'B', 'B', 7, True),
            3.0: ('iii7 in C major', [4, 7, 11, 2], 'E', 'E', 7, True),
            4.0: ('vi7 in C major', [9, 0, 4, 7], 'A', 'A', 7, True),
            5.0: ('ii7 in C major', [2, 5, 9, 0], 'D', 'D', 7, True),
            6.0: ('V7 in C major', [7, 11, 2, 5], 'G', 'G', 7, True),
            7.0: ('I in C major', [0, 4, 7], 'C', 'C', 53, False),
            12.0: ('i7 in a minor', [9, 0, 4, 7], 'A', 'A', 7, True),
            13.0: ('iv7 in a minor', [2, 5, 9, 0], 'D', 'D', 7, True),
            14.0: ('-VII7 in a minor', [7, 11, 2, 5], 'G', 'G', 7, True),
            15.0: ('III7 in a minor', [0, 4, 7, 11], 'C', 'C', 7, True),
            16.0: ('VI7 in a minor', [5, 9, 0, 4], 'F', 'F', 7, True),
            17.0: ('iio7 in a minor', [11, 2, 5, 8], 'B', 'B', 7, True),
            18.0: ('V7 in a minor', [4, 8, 11, 2], 'E', 'E', 7, True),
            19.0: ('i in a minor', [9, 0, 4], 'A', 'A', 53, False),
            24.0: ('I65 in C major', [4, 7, 11, 0], 'C', 'E', 65, True),
            25.0: ('IV2 in C major', [4, 5, 9, 0], 'F', 'E', 42, True),
            26.0: ('viio65 in C major', [2, 5, 8, 11], 'B', 'D', 65, True),
            27.0: ('iii2 in C major', [2, 4, 7, 11], 'E', 'D', 42, True),
            28.0: ('vi43 in C major', [4, 7, 9, 0], 'A', 'E', 43, True),
            29.0: ('ii7 in C major', [2, 5, 9, 0], 'D', 'D', 7, True),
            30.0: ('V43 in C major', [2, 5, 7, 11], 'G', 'D', 43, True),
            31.0: ('I in C major', [0, 4, 7], 'C', 'C', 53, False),
            36.0: ('i65 in a minor', [0, 4, 7, 9], 'A', 'C', 65, True),
            37.0: ('iv2 in a minor', [0, 2, 5, 9], 'D', 'C', 42, True),
            38.0: ('-VII65 in a minor', [11, 2, 5, 7], 'G', 'B', 65, True),
            39.0: ('III2 in a minor', [11, 0, 4, 7], 'C', 'B', 42, True),
            40.0: ('VI43 in a minor', [0, 4, 5, 9], 'F', 'C', 43, True),
            41.0: ('iio7 in a minor', [11, 2, 5, 8], 'B', 'B', 7, True),
            42.0: ('V43 in a minor', [11, 2, 4, 8], 'E', 'B', 43, True),
            43.0: ('i in a minor', [9, 0, 4], 'A', 'A', 53, False)
        }
        for harm in s.flatten().getElementsByClass(roman.RomanNumeral):
            figureAndKey = harm.figureAndKey
            pitchClasses = harm.pitchClasses
            root = harm.root().name
            bass = harm.bass().name
            inversionName = harm.inversionName()
            isSeventh = harm.isSeventh()
            assertTuple = (
                figureAndKey,
                pitchClasses,
                root,
                bass,
                inversionName,
                isSeventh
            )
            self.assertEqual(assertTuple, groundTruth[harm.offset])

    def testHarmSpineAugmentedSixths(self):
        hf1 = HumdrumDataCollection(testFiles.harmScaleDegrees)
        hf1.parse()
        s = hf1.stream
        groundTruth = {
            # Aug6, Italian, French, German
            0.0: (False, False, False, False),
            1.0: (False, False, False, False),
            2.0: (False, False, False, False),
            3.0: (False, False, False, False),
            4.0: (False, False, False, False),
            5.0: (False, False, False, False),
            6.0: (False, False, False, False),
            7.0: (False, False, False, False),
            8.0: (False, False, False, False),
            9.0: (False, False, False, False),
            11.0: (False, False, False, False),
            12.0: (False, False, False, False),
            13.0: (False, False, False, False),
            14.0: (False, False, False, False),
            15.0: (False, False, False, False),
            16.0: (False, False, False, False),
            17.0: (False, False, False, False),
            18.0: (True, True, False, False),
            20.0: (False, False, False, False),
            21.0: (True, False, True, False),
            23.0: (False, False, False, False),
            24.0: (True, False, False, True),
            27.0: (False, False, False, False),
            30.0: (False, False, False, False),
            32.0: (False, False, False, False),
            33.0: (False, False, False, False)
        }
        for harm in s.flatten().getElementsByClass(roman.RomanNumeral):
            isAugmentedSixth = harm.isAugmentedSixth()
            isItalianAugmentedSixth = harm.isItalianAugmentedSixth()
            isFrenchAugmentedSixth = harm.isFrenchAugmentedSixth()
            isGermanAugmentedSixth = harm.isGermanAugmentedSixth()
            assertTuple = (
                isAugmentedSixth,
                isItalianAugmentedSixth,
                isFrenchAugmentedSixth,
                isGermanAugmentedSixth
            )
            self.assertEqual(assertTuple, groundTruth[harm.offset])

    def testMetadataRetrieved(self):
        from music21 import corpus
        c = corpus.parse('palestrina/agnus_0')
        md = c.metadata
        self.assertIsNotNone(md.composer)
        self.assertIn('Palestrina', md.composer)

    def testGlobalEventsReachStream(self):
        # !! comments become GlobalComment objects in the stream; !!! references
        # become metadata (known codes proper, unknown ones custom) and do not
        # stay in the stream; a blank line is ignored without error.
        src = '\n'.join([
            '!!!COM: Test Composer',
            '!!!OTL: Test Title',
            '!! a global comment here',
            '',  # blank line in the middle
            '**kern',
            '4c',
            '4d',
            '*-',
            '!! comment at the end',
            '!!!XYZ: trailing free-form ref',
        ])
        hdc = HumdrumDataCollection(src)
        hdc.parse()
        s = hdc.stream

        # the leading comment lands at 0.0; the trailing one at the end of the
        # music (the two quarter notes total 2.0), not back at 0.0.
        flat = s.flatten()
        commentInfo = [(gc.comment, gc.offset)
                       for gc in flat.getElementsByClass(GlobalComment)]
        self.assertEqual(
            commentInfo,
            [('a global comment here', 0.0), ('comment at the end', 2.0)])

        # references go to metadata and are removed from the stream entirely.
        self.assertFalse(list(s.recurse().getElementsByClass(GlobalReference)))
        self.assertIsNotNone(s.metadata)
        self.assertEqual(str(s.metadata.composer), 'Test Composer')
        self.assertEqual(str(s.metadata.title), 'Test Title')
        # an unknown code (even trailing) is kept as custom metadata, not lost.
        self.assertEqual(str(s.metadata.getCustom('XYZ')[0]), 'trailing free-form ref')

        # the blank line did not derail parsing
        self.assertEqual(len(s.recurse().notes), 2)

    def testFlavors(self):
        prevFlavor = flavors['JRP']
        try:
            flavors['JRP'] = False
            hdc = HumdrumDataCollection(testFiles.dottedTuplet)
            hdc.parse()
            c = t.cast(stream.Score, hdc.stream)
            flavors['JRP'] = True
            hdc2 = HumdrumDataCollection(testFiles.dottedTuplet)
            hdc2.parse()
            d = t.cast(stream.Score, hdc2.stream)
        finally:
            flavors['JRP'] = prevFlavor
        cn = c[note.Note][1]
        self.assertEqual(cn.duration.fullName, 'Eighth Triplet (1/2 QL)')
        self.assertEqual(cn.duration.dots, 0)
        self.assertEqual(repr(cn.duration.tuplets[0].durationNormal),
                         "DurationTuple(type='eighth', dots=1, quarterLength=0.75)")
        self.assertEqual(cn.duration.tuplets[0].durationNormal.dots, 1)

        dn = d[note.Note][1]
        self.assertEqual(dn.duration.fullName, 'Dotted Eighth Triplet (1/2 QL)')
        self.assertEqual(dn.duration.dots, 1)
        self.assertEqual(repr(dn.duration.tuplets[0].durationNormal),
                         "DurationTuple(type='eighth', dots=0, quarterLength=0.5)")
        self.assertEqual(dn.duration.tuplets[0].durationNormal.dots, 0)


class TestExternal(unittest.TestCase):
    show = True

    def testShowSousa(self):
        hf1 = HumdrumDataCollection(testFiles.sousaStars)
        hf1.parse()
        if self.show:
            hf1.stream.show()


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
