import copy
import random
import unittest

from music21 import chord
from music21.chord import Chord
from music21 import converter
from music21 import key
from music21.musicxml import m21ToXml
from music21.musicxml import testPrimitive
from music21 import note
from music21 import pitch
from music21 import scale
from music21 import stream
from music21 import tempo
from music21 import tie
from music21 import volume

# ------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):
    show = True

    def testBasic(self):
        for pitchList in [['g2', 'c4', 'c#6'],
                          ['c', 'd-', 'f#', 'g']]:
            a = Chord(pitchList)
            if self.show:
                a.show()

    def testPostTonalChords(self):
        s = stream.Stream()
        for i in range(30):
            chordRaw = []
            for j in range(random.choice([3, 4, 5, 6, 7, 8])):
                pc = random.choice(list(range(12)))  # py3
                if pc not in chordRaw:
                    chordRaw.append(pc)
            c = Chord(chordRaw)
            c.quarterLength = 4
            c.addLyric(c.forteClass)
            c.addLyric(str(c.primeForm).replace(' ', ''))
            s.append(c)
        if self.show:
            s.show()


class Test(unittest.TestCase):

    def pitchOut(self, listIn):
        '''
        make tests for old-style pitch representation still work.
        '''
        out = '['
        for p in listIn:
            out += str(p) + ', '
        out = out[0:len(out) - 2]
        out += ']'
        return out

    def testMoreCopies(self):
        c1 = chord.Chord(['C4', 'E-4', 'G4'])
        c2 = copy.deepcopy(c1)
        c1.pitches[0].accidental = pitch.Accidental('sharp')
        c1.pitches[1].accidental.set(1)
        self.assertEqual(repr(c1), '<music21.chord.Chord C#4 E#4 G4>')
        self.assertEqual(repr(c2), '<music21.chord.Chord C4 E-4 G4>')

        c1 = chord.Chord(['C#3', 'E4'])
        c2 = copy.deepcopy(c1)
        self.assertIsNot(c1, c2)
        self.assertIsNot(c1.pitches[0], c2.pitches[0])
        self.assertIsNot(c1.pitches[0].accidental, c2.pitches[0].accidental)

        stream1 = stream.Stream()
        stream1.append(c1)
        stream2 = copy.deepcopy(stream1)
        self.assertIsNot(stream1, stream2)
        self.assertIsNot(stream1.notes[0].pitches[0], stream2.notes[0].pitches[0])
        self.assertTrue(stream1.notes[0].pitches[0].accidental is not
                        stream2.notes[0].pitches[0].accidental)

    def testConstruction(self):
        highEFlat = note.Note()
        highEFlat.name = 'E-'
        highEFlat.octave = 5

        a = note.Note()
        b = note.Note()
        self.assertIsInstance(a, note.Note)
        self.assertIsInstance(b, note.Note)

        middleC = note.Note()
        middleC.name = 'C'
        middleC.octave = 4

        lowG = pitch.Pitch()
        lowG.name = 'G'
        lowG.octave = 3

        chord1 = chord.Chord([highEFlat, middleC, lowG])
        self.assertIsNot(chord1.getChordStep(3, testRoot=middleC), False)
        chord1.root(middleC)

        highAFlat = note.Note()
        highAFlat.name = 'A-'
        highAFlat.octave = 5

        chord2 = chord.Chord([middleC, highEFlat, lowG, highAFlat])
        self.assertIsNot(chord1.third, None)
        self.assertIsNot(chord1.fifth, None)
        self.assertEqual(chord1.containsTriad(), True)
        self.assertEqual(chord1.isTriad(), True)
        self.assertEqual(chord2.containsTriad(), True)
        self.assertEqual(chord2.isTriad(), False)

        middleE = note.Note()
        middleE.name = 'E'
        middleE.octave = 4

        chord3 = chord.Chord([middleC, highEFlat, lowG, middleE])
        self.assertEqual(chord3.isTriad(), False)
        self.assertEqual(chord3.containsSeventh(), False)

        middleB = note.Note()
        middleB.name = 'B'
        middleB.octave = 4

        chord4 = chord.Chord([middleC, highEFlat, lowG, middleB])
        self.assertEqual(chord4.containsSeventh(), True)
        self.assertEqual(chord4.isSeventh(), True)

        chord5 = chord.Chord([middleC, highEFlat, lowG, middleE, middleB])
        self.assertEqual(chord5.isSeventh(), False)

        chord6 = chord.Chord([middleC, middleE, lowG])
        self.assertEqual(chord6.isMajorTriad(), True)
        self.assertEqual(chord3.isMajorTriad(), False)

        chord7 = chord.Chord([middleC, highEFlat, lowG])
        self.assertEqual(chord7.isMinorTriad(), True)
        self.assertEqual(chord6.isMinorTriad(), False)
        self.assertEqual(chord4.isMinorTriad(), False)

        lowGFlat = note.Note()
        lowGFlat.name = 'G-'
        lowGFlat.octave = 3
        chord8 = chord.Chord([middleC, highEFlat, lowGFlat])

        self.assertEqual(chord8.isDiminishedTriad(), True)
        self.assertEqual(chord7.isDiminishedTriad(), False)

        middleBFlat = note.Note()
        middleBFlat.name = 'B-'
        middleBFlat.octave = 4

        chord9 = chord.Chord([middleC, middleE, lowG, middleBFlat])

        self.assertEqual(chord9.isDominantSeventh(), True)
        self.assertEqual(chord5.isDominantSeventh(), False)

        middleBDoubleFlat = note.Note()
        middleBDoubleFlat.name = 'B--'
        middleBDoubleFlat.octave = 4

        chord10 = chord.Chord([middleC, highEFlat, lowGFlat, middleBDoubleFlat])
        # chord10.root(middleC)

        self.assertEqual(chord10.isDiminishedSeventh(), True)
        self.assertEqual(chord9.isDiminishedSeventh(), False)

        chord11 = chord.Chord([middleC])

        self.assertEqual(chord11.isTriad(), False)
        self.assertEqual(chord11.isSeventh(), False)

        middleCSharp = note.Note()
        middleCSharp.name = 'C#'
        middleCSharp.octave = 4

        chord12 = chord.Chord([middleC, middleCSharp, lowG, middleE])
        chord12.root(middleC)

        self.assertEqual(chord12.isTriad(), False)
        self.assertEqual(chord12.isDiminishedTriad(), False)

        chord13 = chord.Chord([middleC, middleE, lowG, lowGFlat])

        self.assertIsNot(chord13.getChordStep(5), None)
        self.assertEqual(chord13.hasRepeatedChordStep(5), True)
        self.assertEqual(chord13.hasAnyRepeatedDiatonicNote(), True)
        self.assertIs(chord13.getChordStep(2), None)
        self.assertEqual(chord13.containsTriad(), True)
        self.assertEqual(chord13.isTriad(), False)

        lowGSharp = note.Note()
        lowGSharp.name = 'G#'
        lowGSharp.octave = 3

        chord14 = chord.Chord([middleC, middleE, lowGSharp])

        self.assertEqual(chord14.isAugmentedTriad(), True)
        self.assertEqual(chord6.isAugmentedTriad(), False)

        chord15 = chord.Chord([middleC, highEFlat, lowGFlat, middleBFlat])

        self.assertEqual(chord15.isHalfDiminishedSeventh(), True)
        self.assertEqual(chord12.isHalfDiminishedSeventh(), False)
        self.assertEqual(chord15.bass().name, 'G-')
        self.assertEqual(chord15.inversion(), 2)
        self.assertEqual(chord15.inversionName(), 43)

        lowC = note.Note()
        lowC.name = 'C'
        lowC.octave = 3

        chord16 = chord.Chord([lowC, middleC, highEFlat])

        self.assertEqual(chord16.inversion(), 0)

        chord17 = chord.Chord([lowC, middleC, highEFlat])
        chord17.root(middleC)

        self.assertEqual(chord17.inversion(), 0)

        lowE = note.Note()
        lowE.name = 'E'
        lowE.octave = 3

        chord18 = chord.Chord([middleC, lowE, lowGFlat])

        self.assertEqual(chord18.inversion(), 1)
        self.assertEqual(chord18.inversionName(), 6)

        lowBFlat = note.Note()
        lowBFlat.name = 'B-'
        lowBFlat.octave = 3

        chord19 = chord.Chord([middleC, highEFlat, lowBFlat])
        self.assertEqual(chord19.root().name, middleC.name)
        self.assertEqual(chord19.inversion(), 3)
        self.assertEqual(chord19.inversionName(), 42)
        # self.assertEqual(chord20.inversion(),  4)  # intentionally raises error

        chord20 = chord.Chord([lowC, lowBFlat])
        chord20.root(lowBFlat)

        chord21 = chord.Chord([middleC, highEFlat, lowGFlat])
        self.assertEqual(chord21.root().name, 'C')

        middleF = note.Note()
        middleF.name = 'F'
        middleF.octave = 4

        lowA = note.Note()
        lowA.name = 'A'
        lowA.octave = 3

        chord22 = chord.Chord([middleC, middleF, lowA])
        self.assertEqual(chord22.root().name, 'F')
        self.assertEqual(chord22.inversionName(), 6)

        chord23 = chord.Chord([middleC, middleF, lowA, highEFlat])
        self.assertEqual(chord23.root().name, 'F')

        highC = note.Note()
        highC.name = 'C'
        highC.octave = 4

        highE = note.Note()
        highE.name = 'E'
        highE.octave = 5

        chord24 = chord.Chord([middleC])
        self.assertEqual(chord24.root().name, 'C')

        chord25 = chord.Chord([middleC, highE])
        self.assertEqual(chord25.root().name, 'C')

        middleG = note.Note()
        middleG.name = 'G'
        middleG.octave = 4

        chord26 = chord.Chord([middleC, middleE, middleG])
        self.assertEqual(chord26.root().name, 'C')

        chord27 = chord.Chord([middleC, middleE, middleG, middleBFlat])
        self.assertEqual(chord27.root().name, 'C')

        chord28 = chord.Chord([lowE, lowBFlat, middleG, highC])
        self.assertEqual(chord28.root().name, 'C')

        highD = note.Note()
        highD.name = 'D'
        highD.octave = 5

        highF = note.Note()
        highF.name = 'F'
        highF.octave = 5

        highAFlat = note.Note()
        highAFlat.name = 'A-'
        highAFlat.octave = 5

        chord29 = chord.Chord([middleC, middleE, middleG, middleBFlat, highD])
        self.assertEqual(chord29.root().name, 'C')

        chord30 = chord.Chord([middleC, middleE, middleG, middleBFlat, highD, highF])
        self.assertEqual(chord30.root().name, 'C')

        chord31 = chord.Chord([middleC, middleE, middleG, middleBFlat, highD, highF, highAFlat])
        # Used to raise an error; now should return middleC
        # self.assertRaises(ChordException, chord31.root)
        self.assertEqual(chord31.root().name, middleC.name)

        chord32 = chord.Chord([middleC, middleE, middleG, middleB])
        self.assertEqual(chord32.bass().name, 'C')
        self.assertEqual(chord32.root().name, 'C')
        self.assertEqual(chord32.inversionName(), 7)

        middleFDblFlat = note.Note()
        middleFDblFlat.name = 'F--'

        middleA = note.Note()
        middleA.name = 'A'

        middleASharp = note.Note()
        middleASharp.name = 'A#'

        middleFSharp = note.Note()
        middleFSharp.name = 'F#'

        chord33 = chord.Chord([middleC, middleE, middleG, middleFDblFlat,
                               middleASharp, middleBDoubleFlat, middleFSharp])
        chord33.root(middleC)

        self.assertEqual(chord33.isHalfDiminishedSeventh(), False)
        self.assertEqual(chord33.isDiminishedSeventh(), False)
        self.assertEqual(chord33.isFalseDiminishedSeventh(), False)

        chord34 = chord.Chord([middleC, middleFDblFlat, middleFSharp, middleA])
        self.assertEqual(chord34.isFalseDiminishedSeventh(), True)

        scrambledChord1 = chord.Chord([highAFlat, highF, middleC, middleASharp, middleBDoubleFlat])
        unscrambledChord1 = scrambledChord1.sortAscending()
        self.assertEqual(unscrambledChord1.pitches[0].name, 'C')
        self.assertEqual(unscrambledChord1.pitches[1].name, 'A#')
        self.assertEqual(unscrambledChord1.pitches[2].name, 'B--')
        self.assertEqual(unscrambledChord1.pitches[3].name, 'F')
        self.assertEqual(unscrambledChord1.pitches[4].name, 'A-')

        unscrambledChord2 = scrambledChord1.sortChromaticAscending()
        self.assertEqual(unscrambledChord2.pitches[0].name, 'C')
        self.assertEqual(unscrambledChord2.pitches[1].name, 'B--')
        self.assertEqual(unscrambledChord2.pitches[2].name, 'A#')
        self.assertEqual(unscrambledChord2.pitches[3].name, 'F')
        self.assertEqual(unscrambledChord2.pitches[4].name, 'A-')

        unscrambledChord3 = scrambledChord1.sortFrequencyAscending()
        self.assertEqual(unscrambledChord3.pitches[0].name, 'C')
        self.assertEqual(unscrambledChord3.pitches[1].name, 'B--')
        self.assertEqual(unscrambledChord3.pitches[2].name, 'A#')
        self.assertEqual(unscrambledChord3.pitches[3].name, 'F')
        self.assertEqual(unscrambledChord3.pitches[4].name, 'A-')

    def testEnharmonicSimplification(self):
        eFlat = note.Note(63)
        self.assertEqual(eFlat.pitch.name, 'E-')
        bMajor = chord.Chord([59, 63, 66])
        self.assertEqual([p.name for p in bMajor.pitches], ['B', 'D#', 'F#'])
        self.assertEqual([p.spellingIsInferred for p in bMajor.pitches], [True, True, True])

    def testDurations(self):
        Cq = note.Note('C4')
        Cq.duration.type = 'quarter'

        chord35 = chord.Chord([Cq])
        self.assertEqual(chord35.duration.type, 'quarter')

        Dh = note.Note('D4')
        Dh.duration.type = 'half'

        chord36 = chord.Chord([Cq, Dh])
        self.assertEqual(chord36.duration.type, 'quarter')

        chord37 = chord.Chord([Dh, Cq])
        self.assertEqual(chord37.duration.type, 'half')

        chord38 = chord.Chord([Cq, Dh], type='whole')
        self.assertEqual(chord38.duration.type, 'whole')

    def testShortCuts(self):
        chord1 = Chord(['C#4', 'E4', 'G4'])
        self.assertTrue(chord1.isDiminishedTriad())
        self.assertFalse(chord1.isMajorTriad())

        chord2 = Chord(['C4'])
        self.assertFalse(chord2.isMajorTriad())

    def testClosedPosition(self):
        chord1 = chord.Chord(['C#4', 'G5', 'E6'])
        chord2 = chord1.closedPosition()
        self.assertEqual(repr(chord2), '<music21.chord.Chord C#4 E4 G4>')

    def testPostTonalChordsA(self):
        c1 = Chord([0, 1, 3, 6, 8, 9, 12])
        self.assertEqual(c1.pitchClasses, [0, 1, 3, 6, 8, 9, 0])
        self.assertEqual(c1.multisetCardinality, 7)
        self.assertEqual(c1.orderedPitchClasses, [0, 1, 3, 6, 8, 9])
        self.assertEqual(c1.pitchClassCardinality, 6)
        self.assertEqual(c1.forteClass, '6-29')
        self.assertEqual(c1.normalOrder, [0, 1, 3, 6, 8, 9])
        self.assertEqual(c1.forteClassNumber, 29)
        self.assertEqual(c1.primeForm, [0, 1, 3, 6, 8, 9])
        self.assertEqual(c1.intervalVector, [2, 2, 4, 2, 3, 2])
        self.assertFalse(c1.isPrimeFormInversion)
        self.assertTrue(c1.hasZRelation)
        self.assertTrue(c1.areZRelations(Chord([0, 1, 4, 6, 7, 9])))
        self.assertEqual(c1.commonName, 'combinatorial RI (RI9)')

    def testPostTonalChordsB(self):
        c1 = Chord([1, 4, 7, 10])
        self.assertEqual(c1.commonName, 'diminished seventh chord')
        self.assertEqual(c1.pitchedCommonName, 'A#-diminished seventh chord')

    def testScaleDegreesA(self):
        chord1 = chord.Chord(['C#5', 'E#5', 'G#5'])
        st1 = stream.Stream()
        st1.append(key.Key('c#'))   # c-sharp minor
        st1.append(chord1)
        self.assertEqual(repr(chord1.scaleDegrees),
                         '[(1, None), (3, <music21.pitch.Accidental sharp>), (5, None)]')

        st2 = stream.Stream()
        st2.append(key.Key('c'))    # c minor
        st2.append(chord1)          # same pitches as before gives different scaleDegrees
        sd2 = chord1.scaleDegrees
        self.assertEqual(repr(sd2),
                         '[(1, <music21.pitch.Accidental sharp>), '
                         + '(3, <music21.pitch.Accidental double-sharp>), '
                         + '(5, <music21.pitch.Accidental sharp>)]')

        st3 = stream.Stream()
        st3.append(key.Key('C'))    # C major
        chord2 = chord.Chord(['C4', 'C#4', 'D4', 'E-4', 'E4', 'F4'])  # 1st 1/2 of chromatic
        st3.append(chord2)
        sd3 = chord2.scaleDegrees
        self.assertEqual(repr(sd3),
                         '[(1, None), (1, <music21.pitch.Accidental sharp>), (2, None), '
                         + '(3, <music21.pitch.Accidental flat>), (3, None), (4, None)]')

    def testScaleDegreesB(self):
        # trying to isolate problematic context searches
        chord1 = Chord(['C#5', 'E#5', 'G#5'])
        st1 = stream.Stream()
        st1.append(key.Key('c#'))   # c-sharp minor
        st1.append(chord1)
        self.assertEqual(chord1.activeSite, st1)
        self.assertEqual(str(chord1.scaleDegrees),
                         '[(1, None), (3, <music21.pitch.Accidental sharp>), (5, None)]')

        st2 = stream.Stream()
        st2.append(key.Key('c'))    # c minor
        st2.append(chord1)  # same pitches as before gives different scaleDegrees

        self.assertNotEqual(chord1.activeSite, st1)

        # test id
        self.assertEqual(chord1.activeSite, st2)
        # for some reason this test fails when test cases are run at the
        # module level, but not at the level of running the specific method
        # from the class
        # self.assertEqual(chord1.activeSite, st2)

        self.assertEqual(
            str(chord1.scaleDegrees),
            '[(1, <music21.pitch.Accidental sharp>), '
            + '(3, <music21.pitch.Accidental double-sharp>), (5, <music21.pitch.Accidental sharp>)]'
        )

    def testTiesA(self):
        # test creating independent ties for each Pitch
        c1 = chord.Chord(['c', 'd', 'b'])
        # as this is a subclass of Note, we have a .tie attribute already
        # here, it is managed by a property
        self.assertEqual(c1.tie, None)
        # directly manipulate pitches
        t1 = tie.Tie()
        t2 = tie.Tie()
        c1._notes[0].tie = t1
        # now, the tie attribute returns the tie found on the first pitch
        self.assertEqual(c1.tie, t1)
        # try to set all ties for all pitches using the .tie attribute
        c1.tie = t2
        # must do id comparisons, as == comparisons are based on attributes
        self.assertEqual(id(c1.tie), id(t2))
        self.assertEqual(id(c1._notes[0].tie), id(t2))
        self.assertEqual(id(c1._notes[1].tie), id(t2))
        self.assertEqual(id(c1._notes[2].tie), id(t2))

        # set ties for specific pitches
        t3 = tie.Tie()
        t4 = tie.Tie()
        t5 = tie.Tie()

        c1.setTie(t3, c1.pitches[0])
        c1.setTie(t4, c1.pitches[1])
        c1.setTie(t5, c1.pitches[2])

        self.assertEqual(id(c1.getTie(c1.pitches[0])), id(t3))
        self.assertEqual(id(c1.getTie(c1.pitches[1])), id(t4))
        self.assertEqual(id(c1.getTie(c1.pitches[2])), id(t5))

        s = converter.parse(testPrimitive.chordIndependentTies)
        chords = s.flatten().getElementsByClass(chord.Chord)
        # the middle pitch should have a tie
        self.assertEqual(chords[0].getTie(pitch.Pitch('a4')).type, 'start')
        self.assertEqual(chords[0].getTie(pitch.Pitch('c5')), None)
        self.assertEqual(chords[0].getTie(pitch.Pitch('f4')), None)

        self.assertEqual(chords[1].getTie(pitch.Pitch('a4')).type, 'continue')
        self.assertEqual(chords[1].getTie(pitch.Pitch('g5')), None)

        self.assertEqual(chords[2].getTie(pitch.Pitch('a4')).type, 'continue')
        self.assertEqual(chords[2].getTie(pitch.Pitch('f4')).type, 'start')
        self.assertEqual(chords[2].getTie(pitch.Pitch('c5')), None)

        # s.show()
        GEX = m21ToXml.GeneralObjectExporter()
        out = GEX.parse(s).decode('utf-8')
        out = out.replace(' ', '')
        out = out.replace('\n', '')
        # print(out)
        self.assertTrue(out.find('<pitch><step>A</step><octave>4</octave></pitch>'
                                 + '<duration>15120</duration><tietype="start"/>'
                                 + '<type>quarter</type><dot/><stem>up</stem>'
                                 + '<notations><tiedtype="start"/></notations>') != -1,
                        out)

    def testTiesB(self):
        sc = scale.WholeToneScale()
        s = stream.Stream()
        for i in range(7):
            tiePos = list(range(i + 1))  # py3 = list
            c = sc.getChord('c4', 'c5', quarterLength=1)
            for pos in tiePos:
                c.setTie(tie.Tie('start'), c.pitches[pos])
            s.append(c)
        # s.show()

    def testTiesC(self):
        c2 = Chord(['D4', 'D4'])
        secondD4 = c2.pitches[1]
        c2.setTie('start', secondD4)
        self.assertIsNone(c2._notes[0].tie)
        self.assertEqual(c2._notes[1].tie.type, 'start')

    def testChordQuality(self):
        c1 = Chord(['c', 'e-'])
        self.assertEqual(c1.quality, 'minor')

    def testVolumeInformation(self):
        c = Chord(['g#', 'd-'])
        c.setVolumes([volume.Volume(velocity=96), volume.Volume(velocity=96)])
        self.assertTrue(c.hasComponentVolumes())

        self.assertFalse(c.hasVolumeInformation())
        self.assertIsNone(c._volume)

    def testVolumePerPitchA(self):
        c = Chord(['c4', 'd-4', 'g4'])
        v1 = volume.Volume(velocity=111)
        v2 = volume.Volume(velocity=98)
        v3 = volume.Volume(velocity=73)
        c.setVolume(v1, 'c4')
        c.setVolume(v2, 'd-4')
        c.setVolume(v3, 'g4')
        self.assertEqual(c.getVolume('c4').velocity, 111)
        self.assertEqual(c.getVolume('d-4').velocity, 98)
        self.assertEqual(c.getVolume('g4').velocity, 73)
        self.assertEqual(c.getVolume('c4').client, c)
        self.assertEqual(c.getVolume('d-4').client, c)
        self.assertEqual(c.getVolume('g4').client, c)
        cCopy = copy.deepcopy(c)
        self.assertEqual(cCopy.getVolume('c4').velocity, 111)
        self.assertEqual(cCopy.getVolume('d-4').velocity, 98)
        self.assertEqual(cCopy.getVolume('g4').velocity, 73)
        # environLocal.printDebug(['in test',
        #        'id(c)', id(c)])
        # environLocal.printDebug(['in test',
        #        "c.getVolume('g4').client", id(c.getVolume('g4').client)])
        # environLocal.printDebug(['in test', 'id(cCopy)', id(cCopy)])
        # environLocal.printDebug(['in test',
        #        "cCopy.getVolume('g4').client", id(cCopy.getVolume('g4').client)])
        self.assertEqual(cCopy.getVolume('c4').client, cCopy)
        self.assertEqual(cCopy.getVolume('d-4').client, cCopy)
        self.assertEqual(cCopy.getVolume('g4').client, cCopy)

    def testVolumePerPitchB(self):
        s = stream.Stream()
        amps = [0.1, 0.5, 1]
        for j in range(12):
            c = Chord(['c3', 'd-4', 'g5'])
            for i, sub in enumerate(c):
                sub.volume.velocityScalar = amps[i]
            s.append(c)
        match = []
        for c in s:
            for sub in c:
                match.append(sub.volume.velocity)
        self.assertEqual(match, [13, 64, 127, 13, 64, 127, 13, 64, 127, 13, 64,
                                 127, 13, 64, 127, 13, 64, 127, 13, 64, 127, 13, 64, 127, 13, 64,
                                 127, 13, 64, 127, 13, 64, 127, 13, 64, 127])

    def testVolumePerPitchC(self):
        c = Chord(['f-2', 'a-2', 'c-3', 'f-3', 'g3', 'b-3', 'd-4', 'e-4'])
        c.duration.quarterLength = 0.5
        s = stream.Stream()
        s.insert(tempo.MetronomeMark(referent=2, number=50))
        amps = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        for accent in [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 1, 0.5, 1,
                       0.5, 0.5, 0.5, 0.5, 0.5, 1, 0.5, 0.5, 1, 0.5, 0.5, 0.5,
                        1, 0.5, 0.5, 0.5, 0.5, 1, 0.5, 0.5,
                        None, None, None, None,
                        None, None, None, None,
                        None, None, None, None,
                        None, None, None, None,
                        0.5, 0.5, 0.5, 0.5, 0.5, 1, 0.5, 1, 0.5, 0.5, 0.5, 0.5,
                        0.5, 1, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5,
                        0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5,
                        0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5,
                       ]:
            cNew = copy.deepcopy(c)
            if accent is not None:
                cNew.volume.velocityScalar = accent
                self.assertFalse(cNew.hasComponentVolumes())
            else:
                random.shuffle(amps)
                cNew.setVolumes([volume.Volume(velocityScalar=x) for x in amps])
                self.assertTrue(cNew.hasComponentVolumes())
            s.append(cNew)

    def testVolumePerPitchD(self):
        c = Chord(['f-3', 'g3', 'b-3'])
        # set a single velocity
        c.volume.velocity = 121
        self.assertEqual(c.volume.velocity, 121)
        self.assertFalse(c.hasComponentVolumes())
        # set individual velocities
        c.setVolumes([volume.Volume(velocity=x) for x in (30, 60, 90)])
        # components are set
        self.assertEqual([x.volume.velocity for x in c], [30, 60, 90])
        # hasComponentVolumes is True
        self.assertTrue(c.hasComponentVolumes())
        # if we get a volume, the average is taken, and we get this velocity
        self.assertEqual(c.volume.velocity, 60)
        # still have components
        self.assertTrue(c.hasComponentVolumes())
        self.assertEqual([x.volume.velocity for x in c], [30, 60, 90])
        # if we set the outer velocity of the volume, components are not
        # changed; now we have an out-of sync situation
        c.volume.velocity = 127
        self.assertEqual(c.volume.velocity, 127)
        self.assertTrue(c.hasComponentVolumes())
        self.assertEqual([x.volume.velocity for x in c], [30, 60, 90])
        # if we set the volume property, then we drop the components
        c.volume = volume.Volume(velocity=20)
        self.assertEqual(c.volume.velocity, 20)
        self.assertFalse(c.hasComponentVolumes())
        # if we can still set components
        c.setVolumes([volume.Volume(velocity=x) for x in (10, 20, 30)])
        self.assertEqual([x.volume.velocity for x in c], [10, 20, 30])
        self.assertTrue(c.hasComponentVolumes())
        self.assertEqual(c._volume, None)

    def testGetItemA(self):
        c = Chord(['c4', 'd-4', 'g4'])
        self.assertEqual(str(c[0].pitch), 'C4')
        self.assertEqual(str(c[1].pitch), 'D-4')
        self.assertEqual(str(c[2].pitch), 'G4')
        self.assertEqual(str(c['0.pitch']), 'C4')
        self.assertEqual(str(c['1.pitch']), 'D-4')
        self.assertEqual(str(c['2.pitch']), 'G4')
        # cannot do this, as this provides raw access
        # self.assertEqual(str(c[0]['volume']), 'C4')
        self.assertEqual(str(c['0.volume']), '<music21.volume.Volume realized=0.71>')
        self.assertEqual(str(c['1.volume']), '<music21.volume.Volume realized=0.71>')
        self.assertEqual(str(c['1.volume']), '<music21.volume.Volume realized=0.71>')
        c['0.volume'].velocity = 20
        c['1.volume'].velocity = 80
        c['2.volume'].velocity = 120
        self.assertEqual(c['0.volume'].velocity, 20)
        self.assertEqual(c['1.volume'].velocity, 80)
        self.assertEqual(c['2.volume'].velocity, 120)
        self.assertEqual([x.volume.velocity for x in c], [20, 80, 120])
        cCopy = copy.deepcopy(c)
        self.assertEqual([x.volume.velocity for x in cCopy], [20, 80, 120])
        velocities = [11, 22, 33]
        for i, x in enumerate(cCopy):
            x.volume.velocity = velocities[i]
        self.assertEqual([x.volume.velocity for x in cCopy], [11, 22, 33])
        self.assertEqual([x.volume.velocity for x in c], [20, 80, 120])
        self.assertEqual([x.volume.client for x in cCopy], [cCopy, cCopy, cCopy])
        self.assertEqual([x.volume.client for x in c], [c, c, c])

    def testChordComponentsA(self):
        c = Chord(['d2', 'e-1', 'b-6'])
        s = stream.Stream()
        for n in c:
            s.append(n)
        self.assertEqual(len(s.notes), 3)
        self.assertEqual(s.highestOffset, 2.0)
        self.assertEqual(
            str(s.pitches),
            '[<music21.pitch.Pitch D2>, <music21.pitch.Pitch E-1>, <music21.pitch.Pitch B-6>]')

    def testInvertingSimple(self):
        a = chord.Chord(['g4', 'b4', 'd5', 'f5'])
        self.assertEqual(a.inversion(), 0)
        a.inversion(1)
        self.assertEqual(repr(a), '<music21.chord.Chord B4 D5 F5 G5>')

    def testDeepcopyChord(self):
        ch = Chord('C4 E4 G4')
        ch2 = copy.deepcopy(ch)
        self.assertEqual(ch, ch2)

    def testNewBassAfterRemove(self):
        '''
        Test that bass and root caches invalidate after removal.
        '''
        ch = Chord('C4 E4 G4')
        r = ch.root()
        ch.bass()
        ch.remove(r)
        self.assertEqual(ch.bass().name, 'E')

        # TODO(msc): overrides do not invalidate.  Should they?

    def testChordCannotContainUnpitched(self):
        msg = r'Use a PercussionChord to contain Unpitched objects; got \[<music21.note.Unpitched'
        with self.assertRaisesRegex(TypeError, msg):
            # noinspection PyTypeChecker
            Chord([note.Unpitched()])  # type: ignore

    def testCacheClearedOnAdd(self):
        ch = chord.Chord('C4 E4 G4')
        self.assertTrue(ch.isConsonant())
        # value is now cached.
        ch.add('C#5', runSort=False)
        # value should no longer be cached.
        self.assertFalse(ch.isConsonant())


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)  # , runTest='testInvertingSimple')
