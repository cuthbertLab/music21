from __future__ import annotations

import fractions
import typing as t
import unittest
import xml.etree.ElementTree as ET

from music21 import articulations
from music21 import bar
from music21 import chord
from music21 import common
from music21 import defaults
from music21 import duration
from music21 import dynamics
from music21 import expressions
from music21 import harmony
from music21 import instrument
from music21 import key
from music21 import layout
from music21 import meter
from music21 import note
from music21 import pitch
from music21 import repeat
from music21 import spanner
from music21 import stream
from music21 import tempo
from music21 import text

from music21.musicxml.xmlToM21 import (
    MusicXMLImporter, MusicXMLImportException, MusicXMLWarning,
    MeasureParser, PartParser,
)

class Test(unittest.TestCase):
    def testParseSimple(self):
        MI = MusicXMLImporter()
        MI.xmlText = r'''<score-timewise />'''
        self.assertRaises(MusicXMLImportException, MI.parseXMLText)

    def EL(self, elText):
        return ET.fromstring(elText)

    def pitchOut(self, listIn):
        '''
        make it so that the tests that look for the old-style pitch.Pitch
        representation still work.
        '''
        out = '['
        for p in listIn:
            out += str(p) + ', '
        out = out[0:len(out) - 2]
        out += ']'
        return out

    def testExceptionMessage(self):
        mxScorePart = self.EL('<score-part><part-name>Elec.</part-name></score-part>')
        mxPart = self.EL('<part><measure><note><type>thirty-tooth</type></note></measure></part>')

        PP = PartParser(mxPart=mxPart, mxScorePart=mxScorePart)
        PP.partId = '1'

        msg = 'In part (Elec.), measure (0): found unknown MusicXML type: thirty-tooth'
        with self.assertRaises(MusicXMLImportException) as error:
            PP.parse()
        self.assertEqual(str(error.exception), msg)

    def testBarRepeatConversion(self):
        from music21 import corpus
        # a = converter.parse(testPrimitive.simpleRepeat45a)
        # this is a good example with repeats
        s = corpus.parse('k80/movement3')
        for p in s.parts:
            post = p[bar.Repeat]
            self.assertEqual(len(post), 6)

        # a = corpus.parse('opus41no1/movement3')
        # s.show()

    def testVoices(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.voiceDouble)
        m1 = s.parts[0].getElementsByClass(stream.Measure).first()
        self.assertTrue(m1.hasVoices())

        self.assertEqual([v.id for v in m1.voices], ['1', '2'])

        self.assertEqual([e.offset for e in m1.voices[0]], [0.0, 1.0, 2.0, 3.0])
        self.assertEqual([e.offset for e in m1.voices['1']], [0.0, 1.0, 2.0, 3.0])

        self.assertEqual([e.offset for e in m1.voices[1]], [0.0, 2.0, 2.5, 3.0, 3.5])
        self.assertEqual([e.offset for e in m1.voices['2']], [0.0, 2.0, 2.5, 3.0, 3.5])
        # s.show()

    def testSlurInputA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.spannersSlurs33c)
        # have 5 spanners
        self.assertEqual(len(s[spanner.Spanner]), 5)

        # can get the same from a recurse search
        self.assertEqual(len(s.recurse().getElementsByClass(spanner.Spanner)), 5)

        # s.show('t')
        # s.show()

    def testMultipleStavesPerPartA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.pianoStaff43a)
        self.assertEqual(len(s.parts), 2)
        # s.show()
        self.assertEqual(len(s.parts[0][note.Note]), 1)
        self.assertEqual(len(s.parts[1][note.Note]), 1)

        self.assertIsInstance(s.parts[0], stream.PartStaff)
        self.assertIsInstance(s.parts[1], stream.PartStaff)

        # make sure both staves get identical key signatures, but not the same object
        keySigs = s[key.KeySignature]
        self.assertEqual(len(keySigs), 2)
        self.assertEqual(keySigs[0], keySigs[1])
        self.assertIsNot(keySigs[0], keySigs[1])

    def testMultipleStavesPerPartB(self):
        from music21 import converter
        from music21.musicxml import testFiles

        s = converter.parse(testFiles.moussorgskyPromenade)
        self.assertEqual(len(s.parts), 2)

        self.assertEqual(len(s.parts[0][note.Note]), 19)
        # only chords in the second part
        self.assertEqual(len(s.parts[1][note.Note]), 0)

        self.assertEqual(len(s.parts[0][chord.Chord]), 11)
        self.assertEqual(len(s.parts[1][chord.Chord]), 11)

        # s.show()

    def testMultipleStavesPerPartC(self):
        from music21 import corpus
        s = corpus.parse('schoenberg/opus19/movement2')
        self.assertEqual(len(s.parts), 2)
        self.assertEqual(len(s.getElementsByClass(stream.PartStaff)), 2)

        # test that all elements are unique
        setElementIds = set()
        for el in s.recurse():
            setElementIds.add(id(el))
        self.assertEqual(len(setElementIds), len(s.recurse()))


    def testMultipleStavesInPartWithBarline(self):
        from music21 import converter
        from music21.musicxml import testPrimitive
        s = converter.parse(testPrimitive.mixedVoices1a)
        self.assertEqual(len(s.getElementsByClass(stream.PartStaff)), 2)
        self.assertEqual(len(s.recurse().getElementsByClass(bar.Barline)), 2)
        lastMeasure = s.parts[0].getElementsByClass(stream.Measure).last()
        lastElement = lastMeasure.last()
        lastOffset = lastMeasure.elementOffset(lastElement, returnSpecial=True)
        self.assertEqual(lastOffset, 'highestTime')

    def testMultipleStavesInPartWithOttava(self):
        from music21 import converter
        from music21.musicxml import testPrimitive
        s = converter.parse(testPrimitive.pianoStaffWithOttava)
        self.assertEqual(len(s.getElementsByClass(stream.PartStaff)), 2)
        ps0 = s[stream.PartStaff][0]
        self.assertEqual(len(ps0.getElementsByClass(spanner.Ottava)), 1)
        m0 = ps0[stream.Measure][0]
        self.assertEqual(
            [p.nameWithOctave for p in m0.pitches],
            ['E-5', 'E-6', 'D5', 'D6', 'C5', 'C6', 'E-5', 'E-6', 'F5', 'F6', 'E5', 'E6',
             'D5', 'D6', 'F5', 'F6', 'F#5', 'A5', 'G#5', 'B5']
        )
        s.toWrittenPitch(inPlace=True)
        self.assertEqual(
            [p.nameWithOctave for p in m0.pitches],
            ['E-4', 'E-5', 'D4', 'D5', 'C4', 'C5', 'E-4', 'E-5', 'F4', 'F5', 'E4', 'E5',
             'D4', 'D5', 'F4', 'F5', 'F#4', 'A4', 'G#4', 'B4']
        )

    def testSpannersA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.spanners33a)
        # this number will change as more are being imported
        self.assertGreaterEqual(len(s.flatten().spanners), 2)

        # environLocal.printDebug(['pre s.measures(2,3)', 's', s])
        ex = s.measures(2, 3)

        # just the relevant spanners
        self.assertEqual(len(ex.flatten().spanners), 2)
        # ex.show()

        # slurs are on measures 2, 3
        # crescendos are on measures 4, 5
        # wavy lines on measures 6, 7
        # brackets etc. on measures 10-14
        # glissando on measure 16
        # slide on measure 18 (= music21 Glissando)

    def testTextExpressionsA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.textExpressions)
        # s.show()
        self.assertEqual(len(s[expressions.TextExpression]), 3)

        p1 = s.parts[0]
        m1 = p1.getElementsByClass(stream.Measure)[0]
        self.assertEqual(len(m1.getElementsByClass(expressions.TextExpression)), 0)
        # all in measure 2
        m2 = p1.getElementsByClass(stream.Measure)[1]
        self.assertEqual(len(m2.getElementsByClass(expressions.TextExpression)), 3)

        teStream = m2.getElementsByClass(expressions.TextExpression)
        self.assertEqual([te.offset for te in teStream], [1.0, 1.5, 4.0])

        # s.show()

    def testTextExpressionsC(self):
        from music21 import corpus
        s = corpus.parse('bwv66.6')
        p = s.parts[0]
        for m in p.getElementsByClass(stream.Measure):
            for n in m.flatten().notes:
                if n.pitch.name in ['B']:
                    msg = f'{n.pitch.nameWithOctave}\n{n.duration.quarterLength}'
                    te = expressions.TextExpression(msg)
                    te.style.fontSize = 14
                    te.style.fontWeight = 'bold'
                    te.style.justify = 'center'
                    te.style.enclosure = 'rectangle'
                    te.style.absoluteY = -80
                    m.insert(n.offset, te)
        # p.show()

    def testTextExpressionsD(self):
        from music21 import corpus
        # test placing text expression in arbitrary locations
        s = corpus.parse('bwv66.6')
        p = s.parts[-1]  # get bass
        for m in p.getElementsByClass(stream.Measure)[1:]:
            for pos in [1.5, 2.5]:
                te = expressions.TextExpression(pos)
                te.style.fontWeight = 'bold'
                te.style.justify = 'center'
                te.style.enclosure = 'rectangle'
                m.insert(pos, te)
        # p.show()

    def testTextExpressionsE(self):
        import random
        s = stream.Stream()
        for i in range(6):
            m = stream.Measure(number=i + 1)
            m.append(layout.SystemLayout(isNew=True))
            m.append(note.Rest(type='whole'))
            s.append(m)
        for m in s.getElementsByClass(stream.Measure):
            offsets = [x * 0.25 for x in range(16)]
            random.shuffle(offsets)
            offsets = offsets[:4]
            for o in offsets:
                te = expressions.TextExpression(o)
                te.style.fontWeight = 'bold'
                te.style.justify = 'center'
                te.style.enclosure = 'rectangle'
                m.insert(o, te)
        # s.show()

    def testImportRepeatExpressionsA(self):
        # test importing from musicxml
        from music21.musicxml import testPrimitive
        from music21 import converter

        # has one segno
        s = converter.parse(testPrimitive.repeatExpressionsA)
        self.assertEqual(len(s[repeat.Segno]), 1)
        self.assertEqual(len(s[repeat.Fine]), 1)
        self.assertEqual(len(s[repeat.DalSegnoAlFine]), 1)

        # has two codas
        s = converter.parse(testPrimitive.repeatExpressionsB)
        self.assertEqual(len(s[repeat.Coda]), 2)
        # has one d.c.al coda
        self.assertEqual(len(s[repeat.DaCapoAlCoda]), 1)

    def testImportRepeatBracketA(self):
        from music21 import corpus
        # has repeats in it; start with single measure
        s = corpus.parse('opus74no1', 3)
        # there are 2 for each part, totaling 8
        self.assertEqual(len(s[spanner.RepeatBracket]), 8)
        # can get for each part as spanners are stored in Part now

        # TODO: need to test getting repeat brackets after measure extraction
        # s.parts[0].show()  # 72 through 77
        sSub = s.parts[0].measures(72, 77)
        # 2 repeat brackets are gathered b/c they are stored at the Part by
        # default
        rbSpanners = sSub.getElementsByClass(spanner.RepeatBracket)
        self.assertEqual(len(rbSpanners), 2)

    def testImportVoicesA(self):
        # testing problematic voice imports

        from music21.musicxml import testPrimitive
        from music21 import converter
        # this 2 part segments was importing multiple voices within
        # a measure, even though there was no data in the second voice
        s = converter.parse(testPrimitive.mixedVoices1a)
        # s.show('text')
        self.assertEqual(len(s.parts), 2)
        # there are voices, but they have been removed
        self.assertEqual(len(s.parts[0].getElementsByClass(
            stream.Measure)[0].voices), 0)

        # s.parts[0].show('t')
        # self.assertEqual(len(s.parts[0].voices), 2)
        s = converter.parse(testPrimitive.mixedVoices1b)
        self.assertEqual(len(s.parts), 2)
        self.assertEqual(len(s.parts[0].getElementsByClass(
            stream.Measure)[0].voices), 0)
        # s.parts[0].show('t')

        # this case, there were 4, but there should be 2
        s = converter.parse(testPrimitive.mixedVoices2)
        self.assertEqual(len(s.parts), 2)
        self.assertEqual(len(s.parts[0].getElementsByClass(
            stream.Measure)[0].voices), 2)
        self.assertEqual(len(s.parts[1].getElementsByClass(
            stream.Measure)[0].voices), 2)

        # s.parts[0].show('t')

        # s = converter.parse(testPrimitive.mixedVoices1b)
        # s = converter.parse(testPrimitive.mixedVoices2)

        # s = converter.parse(testPrimitive.mixedVoices1b)
        # s = converter.parse(testPrimitive.mixedVoices2)

    def testImportMetronomeMarksA(self):
        from music21.musicxml import testPrimitive
        from music21 import converter
        # has metronome marks defined, not with sound tag
        s = converter.parse(testPrimitive.metronomeMarks31c)
        # get all tempo indications
        mms = s[tempo.TempoIndication]
        self.assertGreater(len(mms), 3)

    def testImportMetronomeMarksB(self):
        '''
        Import sound tempo marks as MetronomeMarks but only set numberSounding
        '''
        from music21 import corpus
        s = corpus.parse('bach/bwv69.6.xml')
        self.assertEqual(len(s.flatten()[tempo.MetronomeMark]), 8)
        for p in s.parts:
            mm = p.measure(0)[tempo.MetronomeMark].first()
            self.assertIsNone(mm.number)
            self.assertEqual(mm.numberSounding, 96)
            self.assertEqual(mm.referent, duration.Duration(1.0))

    def testImportMetronomeMarksC(self):
        '''
        Import tempo into only the first PartStaff
        '''
        from music21 import corpus
        s = corpus.parse('demos/two-parts')
        self.assertEqual(len(s.parts.first()[tempo.MetronomeMark]), 1)
        self.assertEqual(len(s.parts.last()[tempo.MetronomeMark]), 0)

    def testImportGraceNotesA(self):
        # test importing from musicxml
        from music21.musicxml import testPrimitive
        from music21 import converter
        unused_s = converter.parse(testPrimitive.graceNotes24a)

        # s.show()

    def testChordalStemDirImport(self):
        # NB: Finale apparently will not display a pitch that is a member of a chord without a stem
        # unless all chord members are without stems.
        # MuseScore 2.0.3 -- last <stem> tag rules.
        from music21.musicxml import m21ToXml
        from music21 import converter

        # this also tests the EXPORTING of stem directions on notes within chords...
        n1 = note.Note('f3')
        n1.notehead = 'diamond'
        n1.stemDirection = 'down'
        n2 = note.Note('c4')
        n2.stemDirection = 'noStem'
        c = chord.Chord([n1, n2])
        c.quarterLength = 2

        GEX = m21ToXml.GeneralObjectExporter()
        xml = GEX.parse(c).decode('utf-8')
        # print(xml.decode('utf-8'))
        # c.show()
        inputStream = converter.parse(xml)
        chordResult = inputStream.flatten().notes[0]
        #         for n in chordResult:
        #             print(n.stemDirection)

        self.assertEqual(chordResult.getStemDirection(chordResult.pitches[0]), 'down')
        self.assertEqual(chordResult.getStemDirection(chordResult.pitches[1]), 'noStem')

    def testStaffGroupsA(self):
        from music21.musicxml import testPrimitive
        from music21 import converter

        s = converter.parse(testPrimitive.staffGroupsNested41d)
        staffGroups = s.getElementsByClass(layout.StaffGroup)
        # staffGroups.show()
        self.assertEqual(len(staffGroups), 2)

        sg1 = staffGroups[0]
        self.assertEqual(sg1.symbol, 'line')
        self.assertTrue(sg1.barTogether)

        sg2 = staffGroups[1]  # Order is right here, was wrong in fromMxObjects
        self.assertEqual(sg2.symbol, 'brace')
        self.assertTrue(sg2.barTogether)

        # TODO: more tests about which parts are there...

    def testStaffGroupsPiano(self):
        from music21.musicxml import testPrimitive
        from music21 import converter

        s = converter.parse(testPrimitive.pianoStaff43a)
        sgs = s.getElementsByClass(layout.StaffGroup)
        self.assertEqual(len(sgs), 1)
        self.assertEqual(sgs[0].symbol, 'brace')
        self.assertIs(sgs[0].barTogether, True)
        self.assertIs(sgs[0].style.hideObjectOnPrint, True)

    def testInstrumentTranspositionA(self):
        from music21.musicxml import testPrimitive
        from music21 import converter

        s = converter.parse(testPrimitive.transposingInstruments72a)
        i1 = s.parts[0].flatten().getElementsByClass(instrument.Instrument).first()
        i2 = s.parts[1].flatten().getElementsByClass(instrument.Instrument).first()
        # unused_i3 = s.parts[2].flatten().getElementsByClass(instrument.Instrument).first()

        self.assertEqual(str(i1.transposition), '<music21.interval.Interval M-2>')
        self.assertEqual(str(i2.transposition), '<music21.interval.Interval M-6>')

    def testInstrumentTranspositionB(self):
        from music21.musicxml import testPrimitive
        from music21 import converter

        s = converter.parse(testPrimitive.transposing01)
        # three parts
        # Oboe -> English Horn -> Oboe
        # Cl Bb -> Cl A -> Cl Bb
        # F-horn in F
        # N.B. names don't change just transpositions.
        # all playing A4 in concert pitch.

        iStream1 = s.parts[0][instrument.Instrument].stream()
        # three instruments; one initial, and then one for each transposition
        self.assertEqual(len(iStream1), 3)
        i1 = iStream1[0]
        self.assertIsInstance(i1, instrument.Oboe)

        # should be 3
        iStream2 = s.parts[1][instrument.Instrument].stream()
        self.assertEqual(len(iStream2), 3)
        i2 = iStream2[0]
        self.assertIsInstance(i2, instrument.Clarinet)

        iStream3 = s.parts[2][instrument.Instrument].stream()
        self.assertEqual(len(iStream3), 1)
        i3 = iStream3[0]
        self.assertIsInstance(i3, instrument.Horn)

        self.assertEqual(str(iStream1[0].transposition), 'None')
        self.assertEqual(str(iStream1[1].transposition), '<music21.interval.Interval P-5>')
        self.assertEqual(str(iStream1[2].transposition), '<music21.interval.Interval P1>')

        self.assertEqual(str(iStream2[0].transposition), '<music21.interval.Interval M-2>')
        self.assertEqual(str(iStream2[1].transposition), '<music21.interval.Interval m3>')

        self.assertEqual(str(i3.transposition), '<music21.interval.Interval P-5>')

        self.assertEqual(self.pitchOut(s.parts[0].flatten().pitches),
                         '[A4, A4, A4, A4, A4, A4, A4, A4, '
                         + 'E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, '
                         + 'A4, A4, A4, A4]')
        self.assertEqual(self.pitchOut(s.parts[1].flatten().pitches),
                         '[B4, B4, B4, B4, '
                         + 'F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, '
                         + 'F#4, F#4, F#4, F#4, F#4, B4, B4, B4, B4, B4, B4]')
        self.assertEqual(self.pitchOut(s.parts[2].flatten().pitches),
                         '[E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, '
                         + 'E5, E5, E5, E5, E5, E5, E5, E5]')

        self.assertFalse(s.parts[0].flatten().atSoundingPitch)

        sSounding = s.toSoundingPitch(inPlace=False)

        # all A4s
        self.assertEqual({p.nameWithOctave for p in sSounding.parts[0].flatten().pitches},
                         {'A4'})
        self.assertEqual({p.nameWithOctave for p in sSounding.parts[1].flatten().pitches},
                         {'A4'})
        self.assertEqual({p.nameWithOctave for p in sSounding.parts[2].flatten().pitches},
                         {'A4'})

        # chordification by default places notes at sounding pitch
        sChords = s.chordify()
        self.assertEqual({p.nameWithOctave for p in sChords.flatten().pitches},
                         {'A4'})
        # sChords.show()

    def testInstrumentTranspositionC(self):
        # generate all transpositions on output
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.transposing01)
        instStream = s[instrument.Instrument]
        # for i in instStream:
        #    print(i.offset, i, i.transposition)
        self.assertEqual(len(instStream), 7)
        # s.show()

    def testHarmonyA(self):
        from music21 import corpus

        s = corpus.parse('leadSheet/berlinAlexandersRagtime.xml')
        self.assertEqual(len(s[harmony.ChordSymbol]), 19)

        match = [h.chordKind for h in s[harmony.ChordSymbol]]
        self.assertEqual(match, ['major', 'dominant-seventh', 'major', 'major', 'major',
                                 'major', 'dominant-seventh', 'major', 'dominant-seventh',
                                 'major', 'dominant-seventh', 'major', 'dominant-seventh',
                                 'major', 'dominant-seventh', 'major', 'dominant-seventh',
                                 'major', 'major'])

        match = [str(h.root()) for h in s[harmony.ChordSymbol]]

        self.assertEqual(match, ['F3', 'C3', 'F3', 'B-2', 'F3', 'C3', 'G2', 'C3', 'C3',
                                 'F3', 'C3', 'F3', 'F2', 'B-2', 'F2', 'F3', 'C3', 'F3', 'C3'])

        match = {str(h.figure) for h in s[harmony.ChordSymbol]}

        self.assertEqual(match, {'F', 'F7', 'B-', 'C7', 'G7', 'C'})

        s = corpus.parse('monteverdi/madrigal.3.12.xml')
        self.assertEqual(len(s[harmony.ChordSymbol]), 10)

        s = corpus.parse('leadSheet/fosterBrownHair.xml')
        self.assertEqual(len(s[harmony.ChordSymbol]), 40)

        # s.show()

    def x_testOrnamentAndTechnical(self):
        from music21 import converter
        beethoven = common.getCorpusFilePath() + '/beethoven/opus133.mxl'
        # TODO: this is way too long... lots of hidden 32nd notes for trills...
        s = converter.parse(beethoven, format='musicxml')
        ex = s.parts[0]
        countTrill = 0
        for n in ex.recurse().notes:
            for e in n.expressions:
                if 'Trill' in e.classes:
                    countTrill += 1
        self.assertEqual(countTrill, 54)

        # TODO: Get a better test... the single harmonic in the viola part,
        # m. 482 is probably a mistake for an open string.
        countTechnical = 0
        for n in s.parts[2].recurse().notes:
            for a in n.articulations:
                if 'TechnicalIndication' in a.classes:
                    countTechnical += 1
        self.assertEqual(countTechnical, 1)

    def testOrnamentC(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        # has many ornaments
        s = converter.parse(testPrimitive.notations32a)

        # s.flatten().show('t')
        num_tremolo_spanners = len(s['TremoloSpanner'])
        self.assertEqual(num_tremolo_spanners, 0)  # no spanned tremolos

        count = 0
        for n in s.recurse().notes:
            for e in n.expressions:
                if 'Tremolo' in e.classes:
                    count += 1
        self.assertEqual(count, 1)  # One single Tremolo

        count = 0
        for n in s.recurse().notes:
            for e in n.expressions:
                if 'Turn' in e.classes:
                    count += 1
        self.assertEqual(count, 5)  # include inverted turn

        count = 0
        for n in s.recurse().notes:
            for e in n.expressions:
                if 'InvertedTurn' in e.classes:
                    count += 1
        self.assertEqual(count, 1)

        upperCount = 0
        lowerCount = 0
        for n in s.recurse().notes:
            for e in n.expressions:
                if 'Turn' in e.classes:
                    if e.upperAccidental is not None:
                        upperCount += 1
                    if e.lowerAccidental is not None:
                        lowerCount += 1
        self.assertEqual(upperCount, 2)
        self.assertEqual(lowerCount, 1)

        count = 0
        for n in s.recurse().notes:
            for e in n.expressions:
                if 'Shake' in e.classes:
                    count += 1
        self.assertEqual(count, 1)

        count = 0
        for n in s.recurse().notes:
            for e in n.expressions:
                if 'Schleifer' in e.classes:
                    count += 1
        self.assertEqual(count, 1)

    def testTextBoxA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.textBoxes01)
        tbs = s[text.TextBox]
        self.assertEqual(len(tbs), 5)

        msg = []
        for tb in tbs:
            msg.append(tb.content)
        self.assertEqual(msg, ['This is a text box!', 'pos 200/300 (lower left)',
                               'pos 1000/300 (lower right)', 'pos 200/1500 (upper left)',
                               'pos 1000/1500 (upper right)'])

    def testImportSlursA(self):
        from music21 import corpus
        # this is a good test as this encoding uses staffs, not parts
        # to encode both parts; this requires special spanner handling
        s = corpus.parse('mozart/k545/movement1_exposition')
        sf = s.flatten()
        slurs = sf.getElementsByClass(spanner.Slur)
        self.assertEqual(len(slurs), 2)

        n1, n2 = s.parts[0].flatten().notes[3], s.parts[0].flatten().notes[5]
        # environLocal.printDebug(['n1', n1, 'id(n1)', id(n1),
        #     slurs[0].getSpannedElementIds(), slurs[0].getSpannedElementIds()])
        self.assertEqual(id(n1), slurs[0].getSpannedElementIds()[0])
        self.assertEqual(id(n2), slurs[0].getSpannedElementIds()[1])

        # environLocal.printDebug(['n2', n2, 'id(n2)', id(n2), slurs[0].getSpannedElementIds()])

    def testImportWedgeA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.spanners33a)
        self.assertEqual(len(s[dynamics.Crescendo]), 1)
        self.assertEqual(len(s[dynamics.Diminuendo]), 1)

    def testImportWedgeB(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        # this produces a single component cresc
        s = converter.parse(testPrimitive.directions31a)
        self.assertEqual(len(s[dynamics.Crescendo]), 2)

    def testBracketImportB(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.spanners33a)
        # s.show()
        self.assertEqual(len(s[spanner.Line]), 6)

    def testTrillExtensionImportA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive
        s = converter.parse(testPrimitive.notations32a)
        # s.show()
        self.assertEqual(len(s[expressions.TrillExtension]), 2)

    def testGlissandoImportA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive
        s = converter.parse(testPrimitive.spanners33a)
        # s.show()
        glisses = list(s[spanner.Glissando])
        self.assertEqual(len(glisses), 2)
        self.assertEqual(glisses[0].slideType, 'chromatic')
        self.assertEqual(glisses[1].slideType, 'continuous')

    def testImportDashes(self):
        # dashes are imported as Lines (as are brackets)
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.spanners33a, format='musicxml')
        self.assertEqual(len(s[spanner.Line]), 6)

    def testImportGraceA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.graceNotes24a)
        # s.show()
        match = [str(p) for p in s.pitches]
        # print(match)
        self.assertEqual(match, ['D5', 'C5', 'E5', 'D5', 'C5', 'D5', 'C5', 'D5',
                                 'C5', 'D5', 'C5', 'E5', 'D5', 'C5', 'D5', 'C5',
                                 'D5', 'C5', 'E5', 'E5', 'F4', 'C5', 'D#5', 'C5',
                                 'D-5', 'A-4', 'C5', 'C5'])

    def testBarException(self):
        MP = MeasureParser()
        mxBarline = self.EL('<barline><bar-style>light-heavy</bar-style></barline>')
        # Raises the BarException
        self.assertRaises(bar.BarException, MP.xmlToRepeat, mxBarline)

        mxBarline = self.EL('<barline><bar-style>light-heavy</bar-style>'
                            + '<repeat direction="backward"/></barline>')

        # all fine now, no exceptions here
        MP.xmlToRepeat(mxBarline)

        # Raising the BarException
        mxBarline = self.EL('<barline><bar-style>wunderbar</bar-style></barline>')
        self.assertRaises(bar.BarException, MP.xmlToRepeat, mxBarline)

    def testChordSymbolException(self):
        MP = MeasureParser()
        mxHarmony = self.EL('<harmony><root><root-step>A</root-step></root>'
        '<degree><degree-value></degree-value><degree-type>add</degree-type></degree></harmony>')
        with self.assertRaisesRegex(MusicXMLImportException, 'degree-value missing'):
            MP.xmlToChordSymbol(mxHarmony)

    def testStaffLayout(self):
        from music21 import corpus
        c = corpus.parse('demos/layoutTest.xml')
        layouts = c.flatten().getElementsByClass(layout.LayoutBase).stream()
        systemLayouts = layouts.getElementsByClass(layout.SystemLayout)
        self.assertEqual(len(systemLayouts), 42)
        staffLayouts = layouts.getElementsByClass(layout.StaffLayout)
        self.assertEqual(len(staffLayouts), 20)
        pageLayouts = layouts.getElementsByClass(layout.PageLayout)
        self.assertEqual(len(pageLayouts), 10)
        scoreLayouts = layouts.getElementsByClass(layout.ScoreLayout)
        self.assertEqual(len(scoreLayouts), 1)

        self.assertEqual(len(layouts), 73)

        sl0 = systemLayouts[0]
        self.assertEqual(sl0.distance, None)
        self.assertEqual(sl0.topDistance, 211.0)
        self.assertEqual(sl0.leftMargin, 70.0)
        self.assertEqual(sl0.rightMargin, 0.0)

        sizes = []
        for s in staffLayouts:
            if s.staffSize is not None:
                sizes.append(s.staffSize)
        self.assertEqual(sizes, [80.0, 120.0, 80.0])

    def testStaffLayoutMore(self):
        from music21 import corpus
        c = corpus.parse('demos/layoutTestMore.xml')
        layouts = c.flatten().getElementsByClass(layout.LayoutBase).stream()
        self.assertEqual(len(layouts), 76)
        systemLayouts = layouts.getElementsByClass(layout.SystemLayout)
        sl0 = systemLayouts[0]
        self.assertEqual(sl0.distance, None)
        self.assertEqual(sl0.topDistance, 211.0)
        self.assertEqual(sl0.leftMargin, 70.0)
        self.assertEqual(sl0.rightMargin, 0.0)

        staffLayouts = layouts.getElementsByClass(layout.StaffLayout)
        sizes = []
        for s in staffLayouts:
            if s.staffSize is not None:
                sizes.append(s.staffSize)
        self.assertEqual(sizes, [80.0, 120.0, 80.0])

    def testCountDynamics(self):
        '''
        good test of both dynamics and a PartStaff...
        '''
        from music21 import corpus
        c = corpus.parse('schoenberg/opus19/movement2.mxl')
        dynAll = c.flatten().getElementsByClass(dynamics.Dynamic)
        self.assertEqual(len(dynAll), 6)
        notesOrChords = (note.Note, chord.Chord)
        allNotesOrChords = c.flatten().getElementsByClass(notesOrChords)
        self.assertEqual(len(allNotesOrChords), 50)
        allChords = c[chord.Chord]
        self.assertEqual(len(allChords), 45)
        pCount = 0
        for cc in allChords:
            pCount += len(cc.pitches)
        self.assertEqual(pCount, 97)

    def testTrillOnOneNote(self):
        from music21 import converter
        thisDir = common.getSourceFilePath() / 'musicxml'
        testFp = thisDir / 'testTrillOnOneNote.xml'
        c = converter.parse(testFp)  # , forceSource=True)

        trillExtension = c.parts[0].getElementsByClass(expressions.TrillExtension).first()
        fSharpTrill = c.recurse().notes[0]
        # print(trillExtension.placement)
        self.assertEqual(fSharpTrill.name, 'F#')
        self.assertIs(trillExtension[0], fSharpTrill)
        self.assertIs(trillExtension[-1], fSharpTrill)

    def testLucaGloriaSpanners(self):
        '''
        lots of lines, including overlapping here; testing that
        a line attached to a rest is still there.  Formerly was a problem.

        Many more tests could be done on this piece...
        '''
        from music21 import corpus
        c = corpus.parse('luca/gloria')
        r = c.parts[1].measure(99).getElementsByClass(note.Rest).first()
        bracketAttachedToRest = r.getSpannerSites()[0]
        self.assertIn('Line', bracketAttachedToRest.classes)
        self.assertEqual(bracketAttachedToRest.idLocal, '1')

        # c.show()
        # c.parts[1].show('t')

    def testTwoVoicesWithChords(self):
        from music21 import corpus
        c = corpus.parse('demos/voices_with_chords.xml')
        m1 = c.parts[0].measure(1)
        # m1.show('text')
        firstChord = m1.voices.getElementById('2').getElementsByClass(chord.Chord).first()
        self.assertEqual(repr(firstChord), '<music21.chord.Chord G4 B4>')
        self.assertEqual(firstChord.offset, 1.0)

    def testParseTupletStartStop(self):
        '''
        test that three notes with tuplets start, none, stop
        have these types
        '''

        def getNoteByTupletTypeNumber(tupletType=None, number=None):
            mxNBase = '''
            <note>
            <pitch>
              <step>C</step>
              <octave>4</octave>
            </pitch>
            <duration>56</duration>
            <voice>1</voice>
            <type>quarter</type>
            <time-modification>
              <actual-notes>3</actual-notes>
              <normal-notes>2</normal-notes>
            </time-modification>
            '''
            mxNEnd = '</note>'
            if tupletType is None:
                return mxNBase + mxNEnd

            if number is None:
                mxNMiddle = f'<notations><tuplet type="{tupletType}" /></notations>'
            else:
                mxNMiddle = (
                    f'<notations><tuplet number="{number}" type="{tupletType}" /></notations>'
                )
            return mxNBase + mxNMiddle + mxNEnd

        n0 = getNoteByTupletTypeNumber('start', 1)
        n1 = getNoteByTupletTypeNumber()
        n2 = getNoteByTupletTypeNumber('stop', 1)

        MP = MeasureParser()
        tupTypes = ('start', None, 'stop')
        for i, n in enumerate([n0, n1, n2]):
            mxNote = ET.fromstring(n)
            # mxNotations = mxNote.find('notations')
            # mxTuplets = mxNotations.findall('tuplet')
            tuplets = MP.xmlToTuplets(mxNote)
            self.assertEqual(len(tuplets), 1)
            self.assertEqual(tuplets[0].type, tupTypes[i])

        # without number....
        n0 = getNoteByTupletTypeNumber('start')
        n1 = getNoteByTupletTypeNumber()
        n2 = getNoteByTupletTypeNumber('stop')

        MP = MeasureParser()
        tupTypes = ('start', None, 'stop')
        for i, n in enumerate([n0, n1, n2]):
            mxNote = ET.fromstring(n)
            # mxNotations = mxNote.find('notations')
            # mxTuplets = mxNotations.findall('tuplet')
            tuplets = MP.xmlToTuplets(mxNote)
            self.assertEqual(len(tuplets), 1)
            self.assertEqual(tuplets[0].type, tupTypes[i])

    def testComplexTupletNote(self):
        '''
        test that a note with nested tuplets gets converted properly.
        '''
        mxN = f'''
        <note default-x="347">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>{defaults.divisionsPerQuarter * 0.5 * (2/3) * (2/3)}</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>9</actual-notes>
          <normal-notes>4</normal-notes>
        </time-modification>
        <stem default-y="-55">down</stem>
        <beam number="1">begin</beam>
        <notations>
          <tuplet bracket="yes" number="1" placement="below" type="start">
            <tuplet-actual>
              <tuplet-number>3</tuplet-number>
              <tuplet-type>eighth</tuplet-type>
            </tuplet-actual>
            <tuplet-normal>
              <tuplet-number>2</tuplet-number>
              <tuplet-type>eighth</tuplet-type>
            </tuplet-normal>
          </tuplet>
          <tuplet number="2" placement="below" type="start">
            <tuplet-actual>
              <tuplet-number>3</tuplet-number>
              <tuplet-type>eighth</tuplet-type>
            </tuplet-actual>
            <tuplet-normal>
              <tuplet-number>2</tuplet-number>
              <tuplet-type>eighth</tuplet-type>
            </tuplet-normal>
          </tuplet>
        </notations>
      </note>
        '''
        MP = MeasureParser()
        mxNote = ET.fromstring(mxN)
        # mxNotations = mxNote.find('notations')
        # mxTuplets = mxNotations.findall('tuplet')
        tuplets = MP.xmlToTuplets(mxNote)
        self.assertEqual(len(tuplets), 2)
        MP.xmlToNote(mxNote)
        n = MP.nLast
        self.assertEqual(len(n.duration.tuplets), 2)
        expected_tuplet_repr = ('(<music21.duration.Tuplet 3/2/eighth>, '
                                + '<music21.duration.Tuplet 3/2/eighth>)')
        self.assertEqual(repr(n.duration.tuplets),
                         expected_tuplet_repr)
        self.assertEqual(n.duration.quarterLength, fractions.Fraction(2, 9))

    def testNestedTuplets(self):
        from music21 import corpus
        c = corpus.parse('demos/nested_tuplet_finale_test2.xml')
        nList = list(c.recurse().notes)
        self.assertEqual(repr(nList[0].duration.tuplets),
                         '(<music21.duration.Tuplet 3/2/eighth>,)')
        expected_tuplet_repr_1_to_6 = ('(<music21.duration.Tuplet 3/2/eighth>, '
                                       + '<music21.duration.Tuplet 5/2/eighth>)')
        for i in range(1, 6):
            self.assertEqual(repr(nList[i].duration.tuplets),
                             expected_tuplet_repr_1_to_6)
        self.assertEqual(repr(nList[6].duration.tuplets), '()')
        expected_tuplet_repr_7_to_12 = ('(<music21.duration.Tuplet 5/4/16th>, '
                                        + '<music21.duration.Tuplet 3/2/eighth>)')
        for i in range(7, 12):
            self.assertEqual(repr(nList[i].duration.tuplets),
                             expected_tuplet_repr_7_to_12)
        self.assertEqual(repr(nList[12].duration.tuplets),
                         '(<music21.duration.Tuplet 3/2/eighth>,)')

        tuplet_pairs_per_note = []
        for n in nList[1:6]:
            tuplet_pairs_per_note.append((n.duration.tuplets[0].type, n.duration.tuplets[1].type))
        self.assertEqual(
            # https://github.com/cuthbertLab/music21/issues/1263
            # First element was (None, None)
            tuplet_pairs_per_note,
            [(None, 'start'), (None, None), (None, None), (None, None), ('stop', 'stop')]
        )

    def testImpliedTuplet(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.tupletsImplied)
        # First tuplet group of 3 is silent on bracket and show-number: draw bracket
        # Second tuplet group of 3 is silent on bracket but show-number="none": don't draw bracket
        tuplets = [n.duration.tuplets[0] for n in s.recurse().notes]
        self.assertEqual([tup.bracket for tup in tuplets], [True, True, True, False, False, False])

    def test34MeasureRestWithoutTag(self):
        from xml.etree.ElementTree import fromstring as EL

        # 40320 = 4 quarter notes
        scoreMeasure = '<measure><note><rest/><duration>40320</duration></note></measure>'
        mxMeasure = EL(scoreMeasure)
        pp = PartParser()
        pp.lastTimeSignature = meter.TimeSignature('3/4')
        m = pp.xmlMeasureToMeasure(mxMeasure)
        measureRest = m.notesAndRests[0]
        self.assertEqual(measureRest.duration.type, 'half')
        self.assertEqual(measureRest.duration.quarterLength, 3.0)

    def testPickupMeasureRestSchoenberg(self):
        '''
        Staff 2 of piano part 0 of schoenberg opus19.6 has a quarter rest not
        marked as a full measure rest (GOOD) as the last beat of a pickup measure.

        It should NOT become a full measure rest
        '''
        from music21 import corpus
        sch = corpus.parse('schoenberg/opus19/movement6')
        r = sch.parts[1].measure(1).notesAndRests[0]
        self.assertEqual(r.duration.type, 'quarter')
        self.assertEqual(r.fullMeasure, 'auto')

    def testRehearsalMarks(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.directions31a)
        rmIterator = s[expressions.RehearsalMark]
        self.assertEqual(len(rmIterator), 4)
        self.assertEqual(rmIterator[0].content, 'A')
        self.assertEqual(rmIterator[1].content, 'B')
        self.assertEqual(rmIterator[1].style.enclosure, None)
        self.assertEqual(rmIterator[2].content, 'Test')
        self.assertEqual(rmIterator[2].style.enclosure, 'square')

    def testNoChordImport(self):
        from music21 import converter

        thisDir = common.getSourceFilePath() / 'musicxml'
        testFp = thisDir / 'testNC.xml'
        s = converter.parse(testFp)

        self.assertEqual(5, len(s[harmony.ChordSymbol]))
        self.assertEqual(2, len(s[harmony.NoChord]))

        self.assertEqual('augmented-seventh',
                         s[harmony.ChordSymbol][0].chordKind)
        self.assertEqual('none',
                         s[harmony.ChordSymbol][1].chordKind)

        self.assertEqual('random', str(s[harmony.NoChord][
                                       0].chordKindStr))
        self.assertEqual('N.C.', str(s[harmony.NoChord][
                                     1].chordKindStr))

    def testChordAlias(self):
        '''
        m21 name ('dominant-seventh') should be looked up from musicXML aliases
        (such as 'dominant').
        '''
        from xml.etree.ElementTree import fromstring as EL
        mp = MeasureParser()

        elStr = '<harmony><root><root-step>D</root-step><root-alter>-1</root-alter>'
        elStr += '</root><kind>major-minor</kind></harmony>'
        mxHarmony = EL(elStr)
        cs = mp.xmlToChordSymbol(mxHarmony)
        self.assertEqual(cs.chordKind, 'minor-major-seventh')

    def testChordOffset(self):
        from music21 import converter

        thisDir = common.getSourceFilePath() / 'musicxml'
        testFp = thisDir / 'testChordOffset.xml'
        s = converter.parse(testFp)

        offsets = [0.0, 2.0, 0.0, 2.0, 0.0, 2.0]
        for ch, offset in zip(s[harmony.ChordSymbol],
                              offsets):
            self.assertEqual(ch.offset, offset)

    def testChordInversion(self):
        from xml.etree.ElementTree import fromstring as EL
        h = EL('''
        <harmony><root><root-step>C</root-step></root>
        <kind>major</kind><inversion>1</inversion></harmony>''')
        mp = MeasureParser()
        cs = mp.xmlToChordSymbol(h)
        self.assertEqual(cs.inversion(), 1)

    def testLineHeight(self):
        from xml.etree.ElementTree import fromstring as EL
        el1 = EL('<bracket type="start" line-end="down" end-length="12.5" number="1"></bracket>')
        el2 = EL('<bracket type="stop" line-end="down" end-length="12.5" number="1"></bracket>')

        mp = MeasureParser()
        line = mp.xmlDirectionTypeToSpanners(el1)[0]
        mp.xmlDirectionTypeToSpanners(el2)
        self.assertEqual(line.startHeight, 12.5)
        self.assertEqual(line.endHeight, 12.5)

    def testStringIndication(self):
        from music21 import converter

        thisDir = common.getSourceFilePath() / 'musicxml'
        testFp = thisDir / 'testTab.xml'
        score = converter.parse(testFp)
        guitar_part = score.parts[0]
        notes = list(guitar_part.recurse().notes)

        self.assertIsInstance(notes[0].articulations[0], articulations.StringIndication)
        self.assertEqual(notes[0].articulations[0].number, 4)

        self.assertIsInstance(notes[1].articulations[0], articulations.StringIndication)
        self.assertEqual(notes[1].articulations[0].number, 4)

        self.assertIsInstance(notes[2].articulations[0], articulations.StringIndication)
        self.assertEqual(notes[2].articulations[0].number, 1)

        self.assertIsInstance(notes[3].articulations[0], articulations.StringIndication)
        self.assertEqual(notes[3].articulations[0].number, 2)

    def testArticulationsOnChord(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.multipleFingeringsOnChord)
        c = s[chord.Chord].first()
        self.assertEqual(len(c.articulations), 3)

    def testFretIndication(self):
        from music21 import converter

        thisDir = common.getSourceFilePath() / 'musicxml'
        testFp = thisDir / 'testTab.xml'
        score = converter.parse(testFp)
        guitar_part = score.parts[0]
        notes = list(guitar_part.recurse().notes)

        self.assertIsInstance(notes[0].articulations[1], articulations.FretIndication)
        self.assertEqual(notes[0].articulations[1].number, 7)

        self.assertIsInstance(notes[1].articulations[1], articulations.FretIndication)
        self.assertEqual(notes[1].articulations[1].number, 4)

        self.assertIsInstance(notes[2].articulations[1], articulations.FretIndication)
        self.assertEqual(notes[2].articulations[1].number, 0)

        self.assertIsInstance(notes[3].articulations[1], articulations.FretIndication)
        self.assertEqual(notes[3].articulations[1].number, 3)

    def testArpeggioMarks(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.arpeggio32d)
        p = s.parts[0]
        m = p.measure(1)
        gnote_index = 0
        for el in m:
            if isinstance(el, note.GeneralNote):
                # There should be exactly seven GeneralNotes in this measure, all of
                # which should be Chords with an ArpeggioMark.  The ArpeggioMarks, in
                # order, should be 'normal', 'up', 'normal', 'down', 'normal',
                # 'non-arpeggio', and 'normal'.
                # None of the Notes in those Chords should have an ArpeggioMark.
                with self.subTest(gnote_index=gnote_index):
                    self.assertIsInstance(el, chord.Chord)
                    self.assertIsInstance(el.expressions[0], expressions.ArpeggioMark)

                    if gnote_index == 0:
                        self.assertEqual(el.expressions[0].type, 'normal')
                    elif gnote_index == 1:
                        self.assertEqual(el.expressions[0].type, 'up')
                    elif gnote_index == 2:
                        self.assertEqual(el.expressions[0].type, 'normal')
                    elif gnote_index == 3:
                        self.assertEqual(el.expressions[0].type, 'down')
                    elif gnote_index == 4:
                        self.assertEqual(el.expressions[0].type, 'normal')
                    elif gnote_index == 5:
                        self.assertEqual(el.expressions[0].type, 'non-arpeggio')
                    elif gnote_index == 6:
                        self.assertEqual(el.expressions[0].type, 'normal')
                    self.assertFalse(gnote_index > 6)

                    for n in el.notes:
                        for exp in n.expressions:
                            self.assertNotIsInstance(exp, expressions.ArpeggioMark)

                    gnote_index += 1

    def testArpeggioMarkSpanners(self) -> None:
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = t.cast(stream.Score, converter.parse(testPrimitive.multiStaffArpeggios))
        sb = s.spannerBundle.getByClass(expressions.ArpeggioMarkSpanner)
        self.assertIsNotNone(sb)
        sp = sb[0]
        # go find all the chords and check for spanner vs expressions
        chords: list[chord.Chord] = []
        for i, p in enumerate(s.parts):
            # ArpeggioMarkSpanner spans the second chord (index == 1) across both parts
            chords.append(p[chord.Chord][1])

        for spanned, ch in zip(sp, chords):
            self.assertIs(spanned, ch)

    def testHiddenRests(self):
        from music21 import converter
        from music21 import corpus
        from music21.musicxml import testPrimitive

        # Voice 1: Half note, <forward> (quarter), quarter note
        # Voice 2: <forward> (half), quarter note, <forward> (quarter)
        s = converter.parse(testPrimitive.hiddenRests)
        v1, v2 = s.recurse().voices
        self.assertEqual(v1.duration.quarterLength, v2.duration.quarterLength)

        restV1 = v1.getElementsByClass(note.Rest)[0]
        self.assertTrue(restV1.style.hideObjectOnPrint)
        restsV2 = v2.getElementsByClass(note.Rest)
        self.assertEqual([r.style.hideObjectOnPrint for r in restsV2], [True, True])

        # Schoenberg op.19/2
        # previously, last measure of LH duplicated hidden rest belonging to RH
        # causing unnecessary voices
        # https://github.com/cuthbertLab/music21/issues/991
        sch = corpus.parse('schoenberg/opus19', 2)
        rh_last = sch.parts[0][stream.Measure].last()
        lh_last = sch.parts[1][stream.Measure].last()

        hiddenRest = rh_last.voices.last().first()
        self.assertIsInstance(hiddenRest, note.Rest)
        self.assertEqual(hiddenRest.style.hideObjectOnPrint, True)
        self.assertEqual(hiddenRest.quarterLength, 2.0)

        self.assertEqual(len(lh_last.voices), 0)
        self.assertEqual([r.style.hideObjectOnPrint for r in lh_last[note.Rest]], [False] * 3)

    def testHiddenRestImpliedVoice(self):
        '''
        MuseScore expects readers to infer the voice context surrounding
        a <forward> tag.
        '''
        from xml.etree.ElementTree import fromstring as EL
        elStr = '<measure><note><rest/><duration>20160</duration><voice>1</voice></note>'
        elStr += '<backup><duration>20160</duration></backup>'
        elStr += '<note><rest/><duration>10080</duration><voice>non-integer-value</voice></note>'
        elStr += '<forward><duration>10080</duration></forward></measure>'
        mxMeasure = EL(elStr)
        MP = MeasureParser(mxMeasure=mxMeasure)
        MP.parse()

        self.assertEqual(len(MP.stream.voices), 2)
        self.assertEqual(len(MP.stream.voices[0].elements), 1)
        self.assertEqual(len(MP.stream.voices[1].elements), 2)
        self.assertEqual(MP.stream.voices[1].id, 'non-integer-value')

    def testMultiDigitEnding(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        # Relevant barlines:
        # Measure 2, left barline: <ending number="1,2" type="start"/>
        # Measure 2, right barline: <ending number="1,2" type="stop"/>
        # Measure 3, left barline: <ending number="3" type="start"/>
        # Measure 3, right barline: <ending number="3" type="stop"/>
        score = converter.parse(testPrimitive.multiDigitEnding)
        repeatBrackets = score.recurse().getElementsByClass(spanner.RepeatBracket)
        self.assertListEqual(repeatBrackets[0].numberRange, [1, 2])
        self.assertListEqual(repeatBrackets[1].numberRange, [3])

        nonconformingInput = testPrimitive.multiDigitEnding.replace('1,2', 'ad lib.')
        score2 = converter.parse(nonconformingInput)
        repeatBracket = score2.recurse().getElementsByClass(spanner.RepeatBracket).first()
        self.assertListEqual(repeatBracket.numberRange, [1])

    def testChordAlteration(self):
        from music21 import musicxml
        from xml.etree.ElementTree import fromstring as EL
        MP = musicxml.xmlToM21.MeasureParser()
        elStr = (r'''<harmony><root><root-step>C</root-step></root><kind text="7b5">dominant</kind>
        <degree><degree-value>5</degree-value><degree-alter>-1</degree-alter>
        <degree-type>alter</degree-type></degree></harmony>''')
        mxHarmony = EL(elStr)
        cs = MP.xmlToChordSymbol(mxHarmony)
        # Check that we parsed a modification
        self.assertTrue(len(cs.getChordStepModifications()) == 1)
        # And that it affected the correct pitch in the right way
        self.assertTrue(pitch.Pitch('G-3') == cs.pitches[2])

    def testCompositeLyrics(self):
        '''
        Tests multiple lyrics in same note but with same number (not stanza change)
        '''
        from music21 import converter

        xmlDir = common.getSourceFilePath() / 'musicxml' / 'lilypondTestSuite'
        fp = xmlDir / '61l-Lyrics-Elisions-Syllables.xml'
        s = converter.parse(fp)
        notes = list(s.flatten().notes)

        # Check that the second note has one composite lyric
        self.assertEqual(len(notes[1].lyrics), 1)
        ly1 = notes[1].lyrics[0]
        self.assertTrue(ly1.isComposite)
        self.assertEqual(ly1.syllabic, 'composite')
        self.assertEqual(len(ly1.components), 2)
        self.assertEqual(ly1.components[0].text, 'b')
        self.assertEqual(ly1.components[0].syllabic, 'middle')
        self.assertEqual(ly1.components[1].text, 'c')
        self.assertEqual(ly1.components[1].syllabic, 'middle')
        self.assertEqual(ly1.components[1].elisionBefore, ' ')

        # Third note is similar, but begins in the middle and ends at end
        # with empty elision tag.  Just check the rawText
        self.assertEqual(notes[2].name, 'E')  # make sure have right note
        self.assertEqual(len(notes[2].lyrics), 1)
        ly2 = notes[2].lyrics[0]
        self.assertEqual(len(ly2.components), 2)
        self.assertEqual(ly2.components[1].elisionBefore, '')
        self.assertEqual(ly2.rawText, '-de')

        # Check that the fourth note has parsed three separated lyrics (diff syllabic)
        self.assertEqual(notes[3].name, 'F')  # make sure have right note
        self.assertEqual(len(notes[3].lyrics), 1)
        ly3 = notes[3].lyrics[0]
        self.assertEqual(len(ly3.components), 3)
        self.assertEqual(ly3.components[1].elisionBefore, '_')
        self.assertEqual(ly3.components[2].elisionBefore, '~')
        self.assertEqual(ly3.rawText, 'f_g~h')
        self.assertEqual(ly3.components[0].syllabic, 'begin')
        self.assertEqual(ly3.components[1].syllabic, 'middle')
        self.assertEqual(ly3.components[2].syllabic, 'end')
        self.assertEqual(len(s.lyrics(recurse=True)[1][0]), 4)

    def testDirectionPosition(self):
        from music21 import converter
        from music21 import corpus
        from music21.musicxml import testPrimitive, testFiles

        # Dynamic
        s = converter.parse(testFiles.mozartTrioK581Excerpt)
        dyn = s[dynamics.Dynamic].first()
        self.assertEqual(dyn.style.relativeY, 6)

        # Coda/Segno
        s = converter.parse(testPrimitive.repeatExpressionsA)
        seg = s[repeat.Segno].first()
        self.assertEqual(seg.style.relativeX, 10)

        # TextExpression
        s = converter.parse(testPrimitive.textExpressions)
        positionedEls = [el for el in s.recurse() if el.hasStyleInformation
            and el.style.relativeX is not None]
        self.assertEqual(len(positionedEls), 3)
        self.assertEqual(
            list(set(type(el) for el in positionedEls)),
            [expressions.TextExpression]
        )

        # Wedge
        s = corpus.parse('beach')
        positionedEls = [el for el in s.recurse() if el.hasStyleInformation
            and el.style.relativeX is not None]
        self.assertEqual(len(positionedEls), 40)
        self.assertEqual(
            sorted(set(type(el) for el in positionedEls), key=repr),
            [dynamics.Crescendo, dynamics.Diminuendo, dynamics.Dynamic, expressions.TextExpression]
        )
        crescendos = [el for el in positionedEls if 'Crescendo' in el.classes]
        self.assertEqual(crescendos[0].style.relativeX, -6)

        # Metronome
        s = converter.parse(testFiles.tabTest)
        metro = s[tempo.MetronomeMark].first()
        self.assertEqual(metro.style.absoluteY, 40)
        self.assertEqual(metro.placement, 'above')

    def testImportOttava(self):
        from music21 import converter

        xml_dir = common.getSourceFilePath() / 'musicxml' / 'lilypondTestSuite'
        s = converter.parse(xml_dir / '33d-Spanners-OctaveShifts.xml')

        m = s[stream.Measure].first()
        self.assertEqual(
            [p.nameWithOctave for p in m.pitches],
            #      'C7' <---- TODO(bug): not reading <offset>-4</offset>
            ['A4', 'C5', 'A6', 'C3', 'B2', 'A5', 'A5', 'B3', 'C4']
        )
        self.assertEqual(
            [p.nameWithOctave for p in m.pitches],
            [p.nameWithOctave for p in m.toSoundingPitch().flatten().pitches],
        )
        ottava_objs = s[spanner.Ottava]
        self.assertEqual(
            [o.transposing for o in ottava_objs],
            [False, False, False, False]
        )
        self.assertEqual(
            [o.type for o in ottava_objs],
            ['15ma', '15mb', '8va', '8vb']
        )
        self.assertEqual(
            [o.placement for o in ottava_objs],
            ['above', 'below', 'above', 'below']
        )
        self.assertEqual(
            [[p.nameWithOctave for p in o.getSpannedElements()] for o in ottava_objs],
            # TODO(bug): first element should be ['C7', 'A6']
            # not reading <offset>-4</offset>
            [['A6'], ['C3', 'B2'], ['A5', 'A5'], ['B3', 'C4']]
        )

    def testClearingTuplets(self):
        from xml.etree.ElementTree import fromstring as EL

        MP = MeasureParser()
        MP.divisions = 4
        d = duration.Duration(2 / 3)
        self.assertEqual(len(d.tuplets), 1)
        mxNoteNoType = EL('<note><pitch><step>D</step><octave>6</octave></pitch>'
                            '<duration>3</duration></note>')
        MP.xmlToDuration(mxNoteNoType, inputM21=d)
        self.assertEqual(len(d.tuplets), 0)
        self.assertEqual(d.linked, True)

    def testImportUnpitchedPercussion(self):
        from xml.etree.ElementTree import fromstring as EL
        scorePart = '''
        <score-part id="P4"><part-name>Tambourine</part-name>
        <part-abbreviation>Tamb.</part-abbreviation>
        <score-instrument id="P4-I55">
            <instrument-name>Tambourine</instrument-name>
        </score-instrument>
        <midi-instrument id="P4-I55">
           <midi-channel>10</midi-channel>
           <midi-unpitched>55</midi-unpitched>
        </midi-instrument>
        </score-part>
        '''

        PP = PartParser()
        mxScorePart = EL(scorePart)
        tmb = PP.getDefaultInstrument(mxScorePart)
        self.assertIsInstance(tmb, instrument.Tambourine)
        self.assertEqual(tmb.percMapPitch, 54)  # 1-indexed

        # An instrument music21 doesn't have yet (Cabasa):
        scorePart = scorePart.replace('Tambourine', 'Cabasa')
        scorePart = scorePart.replace('Tamb.', 'Cab.')
        scorePart = scorePart.replace('55', '70')  # 1-indexed
        PP = PartParser()
        mxScorePart = EL(scorePart)
        msg = '69 does not map to a valid instrument!'
        with self.assertWarnsRegex(MusicXMLWarning, msg):
            unp = PP.getDefaultInstrument(mxScorePart)
        self.assertIsInstance(unp, instrument.UnpitchedPercussion)
        self.assertEqual(unp.percMapPitch, 69)

    def testImportImplicitMeasureNumber(self):
        from music21 import converter

        xml_dir = common.getSourceFilePath() / 'musicxml' / 'lilypondTestSuite'
        s = converter.parse(xml_dir / '46d-PickupMeasure-ImplicitMeasures.xml')
        m = s[stream.Measure].first()
        self.assertIs(m.showNumber, stream.enums.ShowNumber.NEVER)


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
