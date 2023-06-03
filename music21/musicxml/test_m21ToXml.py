from __future__ import annotations

import copy
import difflib
import fractions
import io
import re
import unittest
from xml.etree.ElementTree import (
    ElementTree, fromstring as et_fromstring
)

from music21 import articulations
from music21 import chord
from music21 import common
from music21 import converter
from music21 import corpus
from music21 import defaults
from music21 import duration
from music21 import dynamics
from music21 import expressions
from music21 import harmony
from music21 import instrument
from music21 import layout
from music21 import meter
from music21 import note
from music21 import repeat
from music21 import spanner
from music21 import stream
from music21 import tempo

from music21.musicxml import helpers
from music21.musicxml import testPrimitive
from music21.musicxml.m21ToXml import (
    GeneralObjectExporter, ScoreExporter,
    MusicXMLWarning, MusicXMLExportException
)

def stripInnerSpaces(txt: str):
    '''
    Collapse all whitespace (say, in some XML) to a single space,
    for ease of comparison.
    '''
    return re.sub(r'\s+', ' ', txt)


class Test(unittest.TestCase):

    def getXml(self, obj):
        gex = GeneralObjectExporter()
        bytesOut = gex.parse(obj)
        bytesOutUnicode = bytesOut.decode('utf-8')
        return bytesOutUnicode

    def getET(self, obj, makeNotation=True):
        '''
        Return a <score-partwise> ElementTree.
        '''
        if makeNotation:
            gex = GeneralObjectExporter()
            obj = gex.fromGeneralObject(obj)

        SX = ScoreExporter(obj)
        SX.makeNotation = makeNotation
        mxScore = SX.parse()
        helpers.indent(mxScore)
        return mxScore

    def testExceptionMessage(self):
        s = stream.Score()
        p = stream.Part()
        p.partName = 'Offstage Trumpet'
        p.insert(note.Note(quarterLength=(4 / 2048)))
        s.insert(p)

        msg = 'In part (Offstage Trumpet), measure (1): '
        msg += 'Cannot convert "2048th" duration to MusicXML (too short).'
        with self.assertRaises(MusicXMLExportException) as error:
            s.write()
        self.assertEqual(str(error.exception), msg)

    def testSpannersWrite(self):
        p = converter.parse("tinynotation: 4/4 c4 d e f g a b c' b a g2")
        listNotes = list(p.recurse().notes)
        c = listNotes[0]
        d = listNotes[1]
        sl1 = spanner.Slur([c, d])
        p.insert(0.0, sl1)

        f = listNotes[3]
        g = listNotes[4]
        a = listNotes[5]
        sl2 = spanner.Slur([f, g, a])
        p.insert(0.0, sl2)

        c2 = listNotes[6]
        g2 = listNotes[-1]
        sl3 = spanner.Slur([c2, g2])
        p.insert(0.0, sl3)
        self.assertEqual(self.getXml(p).count('<slur '), 6)

    def testSpannerAnchors(self):
        score = stream.Score()
        part = stream.Part()
        score.insert(0, part)
        measure = stream.Measure()
        part.insert(0, measure)
        voice = stream.Voice()
        measure.insert(0, voice)

        n = note.Note('C', quarterLength=4)
        sa1 = spanner.SpannerAnchor()
        sa2 = spanner.SpannerAnchor()
        voice.insert(0, n)
        voice.insert(2, sa1)
        voice.insert(4, sa2)
        cresc = dynamics.Crescendo(n, sa1)  # cresc from n to sa1
        dim = dynamics.Diminuendo(sa1, sa2)   # dim from sa1 to sa2
        score.append((cresc, dim))

        xmlOut = self.getXml(score)

        self.assertIn(
            stripInnerSpaces(
                '''<measure implicit="no" number="0">
                       <attributes>
                           <divisions>10080</divisions>
                       </attributes>
                       <note>
                           <pitch>
                               <step>C</step>
                               <octave>4</octave>
                           </pitch>
                           <duration>40320</duration>
                           <type>whole</type>
                       </note>
                       <backup>
                           <duration>40320</duration>
                       </backup>
                       <direction placement="below">
                           <direction-type>
                               <wedge number="1" spread="0" type="crescendo" />
                           </direction-type>
                       </direction>
                       <forward>
                           <duration>20160</duration>
                       </forward>
                       <direction placement="below">
                           <direction-type>
                               <wedge number="2" spread="15" type="diminuendo" />
                           </direction-type>
                       </direction>
                       <direction placement="below">
                           <direction-type>
                               <wedge number="1" spread="15" type="stop" />
                           </direction-type>
                       </direction>
                       <forward>
                           <duration>20160</duration>
                       </forward>
                       <direction placement="below">
                           <direction-type>
                               <wedge number="2" spread="0" type="stop" />
                           </direction-type>
                       </direction>
                   </measure>'''),
            stripInnerSpaces(xmlOut)
        )


    def testSpannersWritePartStaffs(self):
        '''
        Test that spanners are gathered on the PartStaffs that need them.

        Multi-staff instruments are separated on import into distinct PartStaff
        objects, where usually all the spanners will remain on the first object.
        '''
        xmlDir = common.getSourceFilePath() / 'musicxml' / 'lilypondTestSuite'
        s = converter.parse(xmlDir / '43e-Multistaff-ClefDynamics.xml')

        # StaffGroup spanner stored on the score
        self.assertEqual(len(s.spanners), 1)
        self.assertIsInstance(s.spanners[0], layout.StaffGroup)

        # Crescendo in LH actually stored in first PartStaff object
        self.assertEqual(len(s.parts[0].spanners), 1)
        self.assertEqual(len(s.parts[1].spanners), 0)
        self.assertIsInstance(s.parts[0].spanners[0], dynamics.Crescendo)

        # Will it be found by coreGatherMissingSpanners without being inserted?
        s.makeNotation(inPlace=True)
        self.assertEqual(len(s.parts[1].spanners), 0)

        # and written after the backup tag, i.e. on the LH?
        xmlOut = self.getXml(s)
        xmlAfterFirstBackup = xmlOut.split('</backup>\n')[1]

        self.assertIn(
            stripInnerSpaces(
                ''' <direction placement="below">
                        <direction-type>
                            <wedge number="1" spread="0" type="crescendo" />
                        </direction-type>
                        <staff>2</staff>
                    </direction>'''),
            stripInnerSpaces(xmlAfterFirstBackup)
        )

    def testLowVoiceNumbers(self):
        n = note.Note()
        v1 = stream.Voice([n])
        m = stream.Measure([v1])
        # Unnecessary voice is removed by makeNotation
        xmlOut = self.getXml(m)
        self.assertNotIn('<voice>1</voice>', xmlOut)
        n2 = note.Note()
        v2 = stream.Voice([n2])
        m.insert(0, v2)
        xmlOut = self.getXml(m)
        self.assertIn('<voice>1</voice>', xmlOut)
        self.assertIn('<voice>2</voice>', xmlOut)
        v1.id = 234
        xmlOut = self.getXml(m)
        self.assertIn('<voice>234</voice>', xmlOut)
        self.assertIn('<voice>235</voice>', xmlOut)
        v2.id = 'hello'
        xmlOut = self.getXml(m)
        self.assertIn('<voice>hello</voice>', xmlOut)

    def testVoiceNumberOffsetsThreeStaffsInGroup(self):
        n1_1 = note.Note()
        v1_1 = stream.Voice([n1_1])
        m1_1 = stream.Measure([v1_1])
        n1_2 = note.Note()
        v1_2 = stream.Voice([n1_2])
        m1_2 = stream.Measure([v1_2])
        ps1 = stream.PartStaff([m1_1, m1_2])

        n2_1 = note.Note()
        v2_1 = stream.Voice([n2_1])
        m2_1 = stream.Measure([v2_1])
        n2_2 = note.Note()
        v2_2 = stream.Voice([n2_2])
        m2_2 = stream.Measure([v2_2])
        ps2 = stream.PartStaff([m2_1, m2_2])

        n3_1 = note.Note()
        v3_1 = stream.Voice([n3_1])
        m3_1 = stream.Measure([v3_1])
        n3_2 = note.Note()
        v3_2 = stream.Voice([n3_2])
        m3_2 = stream.Measure([v3_2])
        ps3 = stream.PartStaff([m3_1, m3_2])

        s = stream.Score([ps1, ps2, ps3])
        staffGroup = layout.StaffGroup([ps1, ps2, ps3])
        s.insert(0, staffGroup)

        tree = self.getET(s, makeNotation=False)
        # helpers.dump(tree)
        mxNotes = tree.findall('part/measure/note')
        for mxNote in mxNotes:
            voice = mxNote.find('voice')
            staff = mxNote.find('staff')
            # Because there is one voice per staff/measure, voicenum == staffnum
            self.assertEqual(voice.text, staff.text)

    def testCompositeLyrics(self):
        xmlDir = common.getSourceFilePath() / 'musicxml' / 'lilypondTestSuite'
        fp = xmlDir / '61l-Lyrics-Elisions-Syllables.xml'
        s = converter.parse(fp)
        n1 = s[note.NotRest].first()
        xmlOut = self.getXml(n1)
        self.assertIn('<lyric name="1" number="1">', xmlOut)
        self.assertIn('<syllabic>begin</syllabic>', xmlOut)
        self.assertIn('<text>a</text>', xmlOut)

        tree = self.getET(s)
        mxLyrics = tree.findall('part/measure/note/lyric')
        ly0 = mxLyrics[0]
        self.assertEqual(ly0.get('number'), '1')
        self.assertEqual(len(ly0), 2)
        self.assertEqual(ly0[0].tag, 'syllabic')
        self.assertEqual(ly0[1].tag, 'text')
        # contents already checked above

        ly1 = mxLyrics[1]
        self.assertEqual(len(ly1), 5)
        tags = [child.tag for child in ly1]
        self.assertEqual(tags, ['syllabic', 'text', 'elision', 'syllabic', 'text'])
        self.assertEqual(ly1.find('elision').text, ' ')
        self.assertEqual(ly1.findall('syllabic')[0].text, 'middle')
        self.assertEqual(ly1.findall('text')[0].text, 'b')
        self.assertEqual(ly1.findall('syllabic')[1].text, 'middle')
        self.assertEqual(ly1.findall('text')[1].text, 'c')

        ly2 = mxLyrics[2]
        self.assertEqual(len(ly2), 5)
        tags = [child.tag for child in ly2]
        self.assertEqual(tags, ['syllabic', 'text', 'elision', 'syllabic', 'text'])
        self.assertIsNone(ly2.find('elision').text)
        self.assertEqual(ly2.findall('syllabic')[0].text, 'middle')
        self.assertEqual(ly2.findall('text')[0].text, 'd')
        self.assertEqual(ly2.findall('syllabic')[1].text, 'end')
        self.assertEqual(ly2.findall('text')[1].text, 'e')

    def testExportNC(self):
        s = stream.Score()
        p = stream.Part()
        m = stream.Measure()
        m.append(harmony.ChordSymbol('C'))
        m.repeatAppend(note.Note('C'), 4)
        p.append(m)
        m = stream.Measure()
        m.append(harmony.NoChord())
        m.repeatAppend(note.Note('C'), 2)
        m.append(harmony.ChordSymbol('C'))
        m.repeatAppend(note.Note('C'), 2)
        p.append(m)
        s.append(p)

        self.assertEqual(3, self.getXml(s).count('<harmony'))
        self.assertEqual(1, self.getXml(s).count('<kind text="N.C.">none</kind>'))
        self.assertEqual(1, self.getXml(s).count('<root-step text="">'))

        s = stream.Score()
        p = stream.Part()
        m = stream.Measure()
        m.append(harmony.NoChord())
        m.repeatAppend(note.Note('C'), 2)
        m.append(harmony.ChordSymbol('C'))
        m.repeatAppend(note.Note('C'), 2)
        p.append(m)
        m = stream.Measure()
        m.append(harmony.NoChord('No Chord'))
        m.repeatAppend(note.Note('C'), 2)
        m.append(harmony.ChordSymbol('C'))
        m.repeatAppend(note.Note('C'), 2)
        p.append(m)
        s.append(p)

        self.assertEqual(1, self.getXml(s).count('<kind text="N.C.">none</kind>'))
        self.assertEqual(1, self.getXml(s).count('<kind text="No Chord">none</kind>'))

    def testSetPartsAndRefStreamMeasure(self):
        p = converter.parse('tinynotation: 4/4 c1 d1')
        sc = stream.Score([p])
        sx = ScoreExporter(sc)  # substreams are measures
        sx.setPartsAndRefStream()
        measuresAtOffsetZero = [m for m in p if m.offset == 0]
        self.assertSequenceEqual(measuresAtOffsetZero, p.elements[:1])

    def testFromScoreNoParts(self):
        '''
        Badly nested streams should warn but output no gaps.
        '''
        s = stream.Score()
        s.append(meter.TimeSignature('1/4'))
        s.append(note.Note())
        s.append(note.Note())
        gex = GeneralObjectExporter(s)

        with self.assertWarns(MusicXMLWarning) as cm:
            tree = et_fromstring(gex.parse().decode('utf-8'))
        self.assertIn(repr(s).split(' 0x')[0], str(cm.warning))
        self.assertIn(' is not well-formed; see isWellFormedNotation()', str(cm.warning))
        # The original score with its original address should not
        # be found in the message because makeNotation=True makes a copy
        self.assertNotIn(repr(s), str(cm.warning))

        # Assert no gaps in stream
        self.assertSequenceEqual(tree.findall('.//forward'), [])

    def testFromScoreNoMeasures(self):
        s = stream.Score()
        s.append(note.Note())
        scExporter = ScoreExporter(s)
        tree = scExporter.parse()
        # Measures should have been made
        self.assertIsNotNone(tree.find('.//measure'))

    def testFromSoundingPitch(self):
        '''
        A score with mixed sounding and written parts.
        '''
        m = stream.Measure([instrument.Clarinet(), note.Note('C')])
        p1 = stream.Part(m)
        p1.atSoundingPitch = True
        p2 = stream.Part(stream.Measure([instrument.Bassoon(), note.Note()]))
        s = stream.Score([p1, p2])
        self.assertEqual(s.atSoundingPitch, 'unknown')
        gex = GeneralObjectExporter(s)
        root = et_fromstring(gex.parse().decode('utf-8'))
        self.assertEqual(len(root.findall('.//transpose')), 1)
        self.assertEqual(root.find('.//step').text, 'D')

        s.atSoundingPitch = True
        gex = GeneralObjectExporter(s)
        root = et_fromstring(gex.parse().decode('utf-8'))
        self.assertEqual(len(root.findall('.//transpose')), 1)
        self.assertEqual(root.find('.//step').text, 'D')

    def testMultipleInstruments(self):
        '''
        This is a score for two woodwind players both doubling on
        flute and oboe. They both switch to flute and then back to oboe.
        There are six m21 instruments to represent this, but the
        <score-instrument> tags need just four, since no
        musicXML <part> needs two oboes in it, etc., unless
        there is a patch change/MIDI instrument change.
        '''
        p1 = stream.Part([
            stream.Measure([instrument.Oboe(), note.Note(type='whole')]),
            stream.Measure([instrument.Flute(), note.Note(type='whole')]),
            stream.Measure([instrument.Oboe(), note.Note(type='whole')]),
        ])
        p2 = stream.Part([
            stream.Measure([instrument.Oboe(), note.Note(type='whole')]),
            stream.Measure([instrument.Flute(), note.Note(type='whole')]),
            stream.Measure([instrument.Oboe(), note.Note(type='whole')]),
        ])
        s = stream.Score([p1, p2])
        scEx = ScoreExporter(s)
        tree = scEx.parse()
        self.assertEqual(len(tree.findall('.//score-instrument')), 4)
        self.assertEqual(len(tree.findall('.//measure/note/instrument')), 6)
        self.assertEqual(tree.find('.//score-instrument').get('id'),
                         tree.find('.//measure/note/instrument').get('id'))
        self.assertNotEqual(tree.find('.//score-instrument').get('id'),
                            tree.findall('.//measure/note/instrument')[-1].get('id'))

    def testMultipleInstrumentsPiano(self):
        ps1 = stream.PartStaff([
            stream.Measure([instrument.ElectricPiano(), note.Note(type='whole')]),
            stream.Measure([instrument.ElectricOrgan(), note.Note(type='whole')]),
            stream.Measure([instrument.Piano(), note.Note(type='whole')]),
        ])
        ps2 = stream.PartStaff([
            stream.Measure([instrument.Vocalist(), note.Note(type='whole')]),
            stream.Measure([note.Note(type='whole')]),
            stream.Measure([note.Note(type='whole')]),
        ])
        sg = layout.StaffGroup([ps1, ps2])
        s = stream.Score([ps1, ps2, sg])
        scEx = ScoreExporter(s)
        tree = scEx.parse()

        self.assertEqual(
            # allow for non-deterministic ordering: caused by instrument.deduplicate() (?)
            {el.text for el in tree.findall('.//instrument-name')},
            {'Electric Piano', 'Voice', 'Electric Organ', 'Piano'}
        )
        self.assertEqual(len(tree.findall('.//measure/note/instrument')), 6)

    def testExportIdOfMeasure(self):
        ''' Check that id of measure are exported
            as attributes of the <measure> eelement in MusicXML
        '''
        measure = stream.Measure(id='test', number=1)
        measure.append(note.Note(type='whole'))
        s = stream.Score(measure)
        scEx = ScoreExporter(s)
        tree = scEx.parse()

        for measure_xml in tree.findall('.//measure'):
            self.assertTrue('id' in measure_xml.attrib)
            self.assertEqual(measure_xml.get('id'), 'test')

    def testMidiInstrumentNoName(self):
        i = instrument.Instrument()
        i.midiProgram = 42
        s = converter.parse('tinyNotation: c1')
        s.measure(1).insert(i)
        sc = stream.Score(s)
        scExporter = ScoreExporter(sc)

        tree = scExporter.parse()
        mxScoreInstrument = tree.findall('.//score-instrument')[0]
        mxMidiInstrument = tree.findall('.//midi-instrument')[0]
        self.assertEqual(mxScoreInstrument.get('id'), mxMidiInstrument.get('id'))

    def testOrnamentAccidentals(self):
        s = converter.parse(testPrimitive.notations32a)
        x = self.getET(s)
        accidentalMarks = x.findall('.//ornaments/accidental-mark')
        self.assertEqual(
            [accMark.text for accMark in accidentalMarks],
            ['natural', 'sharp', 'three-quarters-flat']
        )

    def testMultiDigitEndingsWrite(self):
        # Relevant barlines:
        # Measure 2, left barline: <ending number="1,2" type="start"/>
        # Measure 2, right barline: <ending number="1,2" type="stop"/>
        # Measure 3, left barline: <ending number="3" type="start"/>
        # Measure 3, right barline: <ending number="3" type="stop"/>
        s = converter.parse(testPrimitive.multiDigitEnding)
        x = self.getET(s)
        endings = x.findall('.//ending')
        self.assertEqual([e.get('number') for e in endings], ['1,2', '1,2', '3', '3'])

        # Check templates also
        template = s.template()
        template.makeNotation(inPlace=True)  # not essential, but since getET() skips this
        x = self.getET(template)
        endings = x.findall('.//ending')
        self.assertEqual([e.get('number') for e in endings], ['1,2', '1,2', '3', '3'])

        # m21 represents lack of bracket numbers as 0; musicxml uses ''
        s.parts[0].getElementsByClass(spanner.RepeatBracket).first().number = 0
        x = self.getET(s)
        endings = x.findall('.//ending')
        self.assertEqual([e.get('number') for e in endings], ['', '', '3', '3'])

    def testMultiMeasureEndingsWrite(self):
        # Relevant barlines:
        # Measure 1, left barline: no ending
        # Measure 1, right barline: no ending
        # Measure 2, left barline: <ending number="1" type="start"/>
        # Measure 2, right barline: no ending
        # Measure 3, left barline: no ending
        # Measure 3, right barline: no ending
        # Measure 4, left barline: no ending
        # Measure 4, right barline: <ending number="1" type="stop"/>
        # Measure 5, left barline: <ending number="2" type="start"/>
        # Measure 5, right barline: no ending
        # Measure 6, left barline: no ending
        # Measure 6, right barline: no ending
        # Measure 7, left barline: no ending
        # Measure 7, right barline: <ending number="2" type="stop"/>
        # Measure 8, left barline: no ending
        # Measure 8, right barline: no ending
        s = converter.parse(testPrimitive.multiMeasureEnding)
        x = self.getET(s)
        endings = x.findall('.//ending')
        self.assertEqual([e.get('number') for e in endings], ['1', '1', '2', '2'])

        expectedEndings = {
            # key = measure number, value = list(leftEndingType, rightEndingType)
            '1': [None, None],     # measure before the endings
            '2': ['start', None],  # first measure of ending 1
            '3': [None, None],     # second measure of ending 1
            '4': [None, 'stop'],   # last measure of ending 1
            '5': ['start', None],  # first measure of ending 2
            '6': [None, None],     # second measure of ending 2
            '7': [None, 'stop'],   # last measure of ending 2
            '8': [None, None]      # measure after the endings
        }
        measures = x.findall('.//measure')
        self.assertEqual(len(measures), 8)
        for measure in measures:
            measNumber = measure.get('number')
            with self.subTest(measureNumber=measNumber):
                expectLeftBarline = bool(expectedEndings[measNumber][0] is not None)
                expectRightBarline = bool(expectedEndings[measNumber][1] is not None)

                gotLeftBarline = False
                gotRightBarline = False
                barlines = measure.findall('.//barline')
                for i, barline in enumerate(barlines):
                    if barline.get('location') == 'left':
                        gotLeftBarline = True
                        leftEndingType = None
                        leftEnding = barline.find('ending')
                        if leftEnding is not None:
                            leftEndingType = leftEnding.get('type')
                        self.assertEqual(leftEndingType, expectedEndings[measNumber][0])
                    elif barline.get('location') == 'right':
                        gotRightBarline = True
                        rightEndingType = None
                        rightEnding = barline.find('ending')
                        if rightEnding is not None:
                            rightEndingType = rightEnding.get('type')
                        self.assertEqual(rightEndingType, expectedEndings[measNumber][1])

                if expectLeftBarline:
                    self.assertTrue(gotLeftBarline)
                if expectRightBarline:
                    self.assertTrue(gotRightBarline)

    def testTextExpressionOffset(self):
        '''
        Transfer element offset after calling getTextExpression().
        '''
        # https://github.com/cuthbertLab/music21/issues/624
        s = converter.parse('tinynotation: 4/4 c1')
        c = repeat.Coda()
        c.useSymbol = False
        f = repeat.Fine()
        mm = tempo.MetronomeMark(text='Langsam')
        mm.placement = 'above'
        s.measure(1).storeAtEnd([c, f, mm])

        tree = self.getET(s)
        for direction in tree.findall('.//direction'):
            self.assertIsNone(direction.find('offset'))

        # Also check position
        mxDirection = tree.find('part/measure/direction')
        self.assertEqual(mxDirection.get('placement'), 'above')

    def testFullMeasureRest(self):
        s = converter.parse('tinynotation: 9/8 r1')
        r = s[note.Rest].first()
        r.quarterLength = 4.5
        self.assertEqual(r.fullMeasure, 'auto')
        tree = self.getET(s)
        # Previously, this 4.5QL rest with a duration.type 'complex'
        # was split on export into 4.0QL and 0.5QL
        self.assertEqual(len(tree.findall('.//rest')), 1)
        rest = tree.find('.//rest')
        self.assertEqual(rest.get('measure'), 'yes')
        self.assertIsNone(tree.find('.//note/type'))

    def testArticulationSpecialCases(self):
        n = note.Note()
        a = articulations.StringIndication()
        n.articulations.append(a)
        h = articulations.HammerOn()
        # Appending a spanner such as HammerOn to the articulations
        # array is contrary to the documentation and contrary to the
        # behavior of the musicxml importer, but we're testing it here
        # anyway to just ensure that *IF* a user decides to do this themselves,
        # we don't create a superfluous <other-technical> tag on export.
        n.articulations.append(h)

        # Legal values for StringIndication begin at 1
        self.assertEqual(a.number, 0)
        # Use GEX to go through wellformed object conversion
        gex = GeneralObjectExporter(n)
        tree = et_fromstring(gex.parse().decode('utf-8'))
        self.assertIsNone(tree.find('.//string'))
        self.assertIsNone(tree.find('.//other-technical'))

    def testMeasurePadding(self):
        s = stream.Score([converter.parse('tinyNotation: 4/4 c4')])
        s[stream.Measure].first().paddingLeft = 2.0
        s[stream.Measure].first().paddingRight = 1.0
        # workaround until getET() helper starts calling fromGeneralObject
        s = GeneralObjectExporter().fromGeneralObject(s)
        tree = self.getET(s)
        self.assertEqual(len(tree.findall('.//rest')), 0)
        s[stream.Measure].first().paddingLeft = 1.0
        # workaround until getET() helper starts calling fromGeneralObject
        s = GeneralObjectExporter().fromGeneralObject(s)
        tree = self.getET(s)
        self.assertEqual(len(tree.findall('.//rest')), 1)

    def test_instrumentDoesNotCreateForward(self):
        '''
        Instrument tags were causing forward motion in some cases.
        From Chapter 14, Key Signatures

        This is a transposed score.  Instruments were being extended in duration
        in the toSoundingPitch and not having their durations restored afterwards
        leading to Instrument objects being split if the duration was complex
        '''
        alto = corpus.parse('bach/bwv57.8').parts['#Alto']
        alto.measure(7).timeSignature = meter.TimeSignature('6/8')
        newAlto = alto.flatten().getElementsNotOfClass(meter.TimeSignature).stream()
        newAlto.insert(0, meter.TimeSignature('2/4'))
        newAlto.makeMeasures(inPlace=True)
        newAltoFixed = newAlto.makeNotation()
        tree = self.getET(newAltoFixed)
        self.assertTrue(tree.findall('.//note'))
        self.assertFalse(tree.findall('.//forward'))

    def testOutOfBoundsExpressionDoesNotCreateForward(self):
        '''
        A metronome mark at an offset exceeding the bar duration was causing
        <forward> tags, i.e. hidden rests. Prefer <offset> instead.
        '''
        m = stream.Measure()
        m.append(meter.TimeSignature('1/4'))
        m.append(note.Rest())
        m.insert(2, tempo.MetronomeMark('slow', 40))
        p = stream.Part([m])
        s = stream.Score([p])

        tree = self.getET(s, makeNotation=False)
        self.assertFalse(tree.findall('.//forward'))
        self.assertEqual(
            int(tree.findall('.//direction/offset')[0].text),
            defaults.divisionsPerQuarter)

    def testArpeggios(self):
        expectedResults = (
            'arpeggiate',
            'arpeggiate',
            'arpeggiate',
            'arpeggiate up',
            'arpeggiate up',
            'arpeggiate up',
            'arpeggiate',
            'arpeggiate',
            'arpeggiate',
            'arpeggiate down',
            'arpeggiate down',
            'arpeggiate down',
            'arpeggiate',
            'arpeggiate',
            'arpeggiate',
            'non-arpeggiate bottom',
            '',
            'non-arpeggiate top',
            'arpeggiate',
            'arpeggiate',
            'arpeggiate',
        )
        s = converter.parse(testPrimitive.arpeggio32d)
        x = self.getET(s)
        # helpers.dump(x)
        mxPart = x.find('part')
        mxMeasure = mxPart.find('measure')
        for i, mxNote in enumerate(mxMeasure.findall('note')):
            with self.subTest(note_index=i):
                nonArp = None
                arp = None
                notations = mxNote.find('notations')
                if notations is not None:
                    nonArp = notations.find('non-arpeggiate')
                    arp = notations.find('arpeggiate')
                if expectedResults[i].startswith('non-arpeggiate'):
                    self.assertIsNotNone(nonArp)
                    nonArpType = nonArp.get('type')
                    for whichEnd in ('top', 'bottom'):
                        if expectedResults[i].endswith(whichEnd):
                            self.assertEqual(nonArpType, whichEnd)
                    continue
                if expectedResults[i].startswith('arpeggiate'):
                    self.assertIsNotNone(arp)
                    arpDirection = arp.get('direction')
                    if expectedResults[i] == 'arpeggiate':
                        self.assertIsNone(arpDirection)
                        continue
                    for direction in ('up', 'down'):
                        if expectedResults[i].endswith(direction):
                            self.assertEqual(arpDirection, direction)
                    continue
                self.assertIsNone(arp)
                self.assertIsNone(nonArp)

    def testArpeggioMarkSpanners(self):
        expectedNumber = (
            #  three-note chord with single-chord arpeggio
            None,
            None,
            None,
            #  three-note chord in a multi-chord (cross-voice) arpeggio (number == 1)
            '1',
            '1',
            '1',
            #  backup and do next voice
            #  three-note chord with single-chord arpeggio
            None,
            None,
            None,
            #  three-note chord in that same multi-chord (cross-voice) arpeggio (number == 1)
            '1',
            '1',
            '1',
        )

        s = converter.parse(testPrimitive.multiStaffArpeggios)
        x = self.getET(s)
        mxPart = x.find('part')
        mxMeasure = mxPart.find('measure')
        for note_index, mxNote in enumerate(mxMeasure.findall('note')):
            with self.subTest(note_index=note_index):
                arp = None
                arpNum = None
                notations = mxNote.find('notations')
                if notations is not None:
                    arp = notations.find('arpeggiate')
                if arp is not None:
                    arpNum = arp.get('number')
                self.assertEqual(arpNum, expectedNumber[note_index])

    def testArpeggioMarkSpannersNonArpeggiate(self):
        c1 = chord.Chord(['C3', 'E3', 'G3'])
        n2 = note.Note('D4')
        am = expressions.ArpeggioMarkSpanner([c1, n2], arpeggioType='non-arpeggio')
        m1 = stream.Measure()
        m1.append(c1)
        p1 = stream.PartStaff([m1])

        m2 = stream.Measure()
        m2.append(n2)
        p2 = stream.PartStaff([m2])

        sl = layout.StaffGroup([p1, p2])

        s = stream.Score([sl, am, p1, p2])
        x = self.getET(s)

        mxPart = x.find('part')
        mxMeasure = mxPart.find('measure')
        for note_index, mxNote in enumerate(mxMeasure.findall('note')):
            with self.subTest(note_index=note_index):
                arp = None
                arpNum = -1
                notations = mxNote.find('notations')
                if notations is not None:
                    arp = notations.find('non-arpeggiate')
                    if note_index in (1, 2) and arp is not None:
                        self.fail(f'{note_index=} should not have non-arpeggiate')
                    if note_index in (0, 3) and arp is None:
                        self.fail(f'{note_index=} should have non-arpeggiate')
                elif note_index in (0, 3):
                    self.fail(f'{note_index=} should have notations')

                if arp is not None:
                    arpNum = arp.get('number')
                    self.assertEqual(arpNum, '1')


    def testExportChordSymbolsWithRealizedDurations(self):

        def realizeDurationsAndAssertTags(mm: stream.Measure, forwardTag=False, offsetTag=False):
            mm = copy.deepcopy(mm)
            harmony.realizeChordSymbolDurations(mm)
            p = stream.Part([mm])
            s = stream.Score([p])
            tree = self.getET(s, makeNotation=False)
            self.assertIs(bool(tree.findall('.//forward')), forwardTag)
            self.assertIs(bool(tree.findall('.//offset')), offsetTag)

        # Two consecutive chord symbols, no rests
        cs1 = harmony.ChordSymbol('C7')
        cs2 = harmony.ChordSymbol('F7')
        m = stream.Measure()
        m.insert(0, cs1)
        m.insert(2, cs2)
        realizeDurationsAndAssertTags(m, forwardTag=True, offsetTag=False)

        # Two consecutive chord symbols, rest coinciding with first one
        r1 = note.Rest(type='half')
        m.insert(0, r1)
        realizeDurationsAndAssertTags(m, forwardTag=False, offsetTag=False)

        # One chord symbol midmeasure, no rests
        m.remove(cs1)
        m.remove(r1)
        realizeDurationsAndAssertTags(m, forwardTag=True, offsetTag=False)

        # One chord symbol midmeasure coinciding with whole note
        n1 = note.Note(type='whole')
        m.insert(0, n1)
        # Need an offset tag to show the -2.0 offset to get from end to midmeasure
        realizeDurationsAndAssertTags(m, forwardTag=False, offsetTag=True)

        # One chord symbol at beginning of measure coinciding with whole note
        m.remove(cs2)
        m.insert(0, cs1)
        realizeDurationsAndAssertTags(m, forwardTag=False, offsetTag=False)

        # One chord symbol at beginning of measure with writeAsChord=True
        # followed by a half note
        cs1.writeAsChord = True
        n1.offset = 2
        n1.quarterLength = 2
        realizeDurationsAndAssertTags(m, forwardTag=False, offsetTag=False)

    def test_inexpressible_hidden_rests_become_forward_tags(self):
        '''
        Express hidden rests with inexpressible durations as <forward> tags.
        '''
        m = stream.Measure()
        # 7 eighths in the space of 4 eighths, imported as 137/480
        # (137/480) * 7 = 1.9979, not 2.0
        # music21 filled gap with an inexpressible 0.0021 rest and couldn't export
        septuplet = note.Note(type='eighth')
        tuplet_obj = duration.Tuplet(7, 4, 'eighth')
        septuplet.duration.appendTuplet(tuplet_obj)
        septuplet.duration.linked = False
        septuplet.quarterLength = fractions.Fraction(137, 480)
        m.repeatAppend(septuplet, 7)
        # leave 0.0021 gap and do the same thing from 2.0 -> 3.9979
        m.repeatInsert(septuplet, [2.0])
        m.repeatAppend(septuplet, 6)
        m.insert(0, meter.TimeSignature('4/4'))
        m.makeRests(inPlace=True, fillGaps=True, hideRests=True, timeRangeFromBarDuration=True)
        self.assertLess(m[note.Rest].first().quarterLength, 0.0025)
        gex = GeneralObjectExporter()
        tree = self.getET(gex.fromGeneralObject(m))
        # Only one <forward> tag to get from 1.9979 -> 2.0
        # No <forward> tag is necessary to finish the incomplete measure (3.9979 -> 4.0)
        self.assertEqual(len(tree.findall('.//forward')), 1)

    def test_roman_musicxml_two_kinds(self):
        from music21.roman import RomanNumeral

        # normal roman numerals take up no time in xml output.
        rn1 = RomanNumeral('I', 'C')
        rn1.duration.type = 'half'
        rn2 = RomanNumeral('V', 'C')
        rn2.duration.type = 'half'

        m = stream.Measure()
        m.insert(0.0, rn1)
        m.insert(2.0, rn2)

        # with writeAsChord=True, they get their own Chord objects and durations.
        self.assertTrue(rn1.writeAsChord)
        xmlOut = GeneralObjectExporter().parse(m).decode('utf-8')
        self.assertNotIn('<forward>', xmlOut)
        self.assertIn('<chord', xmlOut)

        rn1.writeAsChord = False
        rn2.writeAsChord = False
        xmlOut = GeneralObjectExporter().parse(m).decode('utf-8')
        self.assertIn('<numeral', xmlOut)
        self.assertIn('<forward>', xmlOut)
        self.assertNotIn('<chord', xmlOut)
        self.assertNotIn('<offset', xmlOut)
        self.assertNotIn('<rest', xmlOut)

        rn1.duration.quarterLength = 0.0
        rn2.duration.quarterLength = 0.0
        xmlOut = GeneralObjectExporter().parse(m).decode('utf-8')
        self.assertIn('<rest', xmlOut)
        self.assertNotIn('<forward>', xmlOut)



class TestExternal(unittest.TestCase):
    show = True

    def testSimple(self):
        # b = converter.parse(corpus.corpora.CoreCorpus().getWorkList('cpebach')[0],
        #    format='musicxml', forceSource=True)
        b = corpus.parse('cpebach')
        # b.show('text')
        # n = b[note.NotRest].first()
        # print(n.expressions)
        # return

        SX = ScoreExporter(b)
        mxScore = SX.parse()

        helpers.indent(mxScore)

        sio = io.BytesIO()

        sio.write(SX.xmlHeader())

        et = ElementTree(mxScore)
        et.write(sio, encoding='utf-8', xml_declaration=False)
        v = sio.getvalue()
        sio.close()

        v = v.decode('utf-8')
        # v = v.replace(' />', '/>')  # normalize

        # b2 = converter.parse(v)
        fp = b.write('musicxml')
        if self.show:
            print(fp)

        with io.open(fp, encoding='utf-8') as f:
            v2 = f.read()
        differ = list(difflib.ndiff(v.splitlines(), v2.splitlines()))
        for i, l in enumerate(differ):
            if l.startswith('-') or l.startswith('?') or l.startswith('+'):
                if 'id=' in l:
                    continue
                if self.show:
                    print(l)
                    # for j in range(i - 1,i + 1):
                    #    print(differ[j])
                    # print('------------------')
        import os
        os.remove(fp)


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)  # , runTest='testExceptionMessage')
