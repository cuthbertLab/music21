#-------------------------------------------------------------------------------
# Name:         testDocumentation.py
# Purpose:      tests from or derived from the Documentation
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import copy, types, random
import doctest, unittest



import music21
from music21 import corpus, stream, note, meter
from music21 import environment
_MOD = "test.testDocumentation.py"  
environLocal = environment.Environment(_MOD)



def test():
    '''Doctest placeholder

    >>> True
    True
    '''
    pass



#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass


    def testQuickStart(self):
        from music21 import stream, corpus, note
        sBach = corpus.parseWork('bach/bwv7.7')
        # with metadata
        self.assertEquals(len(sBach), 5)
        self.assertEquals(len(sBach.parts), 4)

        select = sBach.parts[0].measures(2,4)
        self.assertEquals(len(select), 3)
        self.assertEquals('Measure' in select[0].classes, True)
        self.assertEquals([part.id for part in sBach.parts], [u'Soprano', u'Alto', u'Tenor', u'Bass'] )
        self.assertEquals('Part' in sBach.getElementById('Soprano').classes, True)

        mx = select.musicxml


        # Creating Notes, Measures, Parts, and Scores
        n1 = note.Note('e4')
        n1.duration.type = 'whole'
        n2 = note.Note('d4')
        n2.duration.type = 'whole'
        m1 = stream.Measure()
        m2 = stream.Measure()
        m1.append(n1)
        m2.append(n2)
        partLower = stream.Part()
        partLower.append(m1)
        partLower.append(m2)

        self.assertEquals(len(partLower.getElementsByClass('Measure')), 2)
        self.assertEquals(len(partLower.flat), 2)
        mx = partLower.musicxml

        data1 = [('g4', 'quarter'), ('a4', 'quarter'), ('b4', 'quarter'), ('c#5', 'quarter')]
        data2 = [('d5', 'whole')]
        data = [data1, data2]
        partUpper = stream.Part()
        for mData in data:
            m = stream.Measure()
            for pitchName, durType in mData:
                n = note.Note(pitchName)
                n.duration.type = durType
                m.append(n)
            partUpper.append(m)

        self.assertEquals(len(partUpper.getElementsByClass('Measure')), 2)
        self.assertEquals(len(partUpper.flat), 5)
        mx = partLower.musicxml

        sCadence = stream.Score()
        sCadence.insert(0, partUpper)
        sCadence.insert(0, partLower)

        self.assertEquals(len(sCadence.getElementsByClass('Part')), 2)
        self.assertEquals(len(sCadence.flat.notes), 7)

        #sCadence.show()



    def testOverviewNotes(self):
        from music21 import duration, pitch, chord

        p1 = pitch.Pitch('b-4')
        self.assertEquals(p1.octave, 4)
        self.assertEquals(p1.pitchClass, 10)
        self.assertEquals(p1.name, 'B-')
        self.assertEquals(p1.nameWithOctave, 'B-4')
        self.assertEquals(p1.midi, 70)
        p1.name = 'd#'
        p1.octave = 3

        self.assertEquals(p1.nameWithOctave, 'D#3')

        self.assertEquals(str(p1.accidental), '<accidental sharp>')
        self.assertEquals(p1.accidental.alter, 1.0)

        p2 = p1.transpose('M7')
        self.assertEquals(p2.nameWithOctave, 'C##4')


        # creating and editing durations
        d1 = duration.Duration('half')  
        d2 = duration.Duration(1.5)
        self.assertEquals(d1.quarterLength, 2.0)        
        self.assertEquals(d2.dots, 1)
        self.assertEquals(d2.type, 'quarter')
        self.assertEquals(d2.quarterLength, 1.5)

        d1.quarterLength = 2.25
        self.assertEquals(d1.quarterLength, 2.25)
        self.assertEquals(d1.type, 'complex')

        mx = d1.musicxml


        # creating and editing notes
        n1 = note.Note('e-5')
        self.assertEquals(n1.name, 'E-')
        self.assertEquals(n1.pitchClass, 3)
        self.assertEquals(n1.midi, 75)
        self.assertEquals(n1.quarterLength, 1.0)

        n1.addLyric(n1.name)
        n1.addLyric(n1.pitchClass)
        n1.addLyric('QL: %s' % n1.quarterLength)

        n1.quarterLength = 6.25
        mx = n1.musicxml


        # creating and editing chords
        c1 = chord.Chord(['a#3', 'g4', 'f#5'])
        self.assertEquals(str(c1.pitches), '[A#3, G4, F#5]')        
        c1.quarterLength = 1 + 1/3.0
        self.assertEquals(str(c1.quarterLength), '1.33333333333')        
        mx  = c1.musicxml

        c2 = c1.transpose('m2')
        self.assertEquals(str(c2.pitches), '[B3, A-4, G5]')        
        mx  = c2.musicxml

        c2.addLyric(c2.forteClass)
        mx  = c2.musicxml


    def testOverviewStreams(self):
        s = stream.Stream()
        n1 = note.Note()
        n1.pitch.name = 'E4'
        n1.duration.type = 'half'
        self.assertEquals(n1.quarterLength, 2.0)
        s.append(n1)
        self.assertEquals(len(s), 1)

        n2 = note.Note('f#')
        n2.quarterLength = .5
        s.append(n2)
        self.assertEquals(len(s), 2)
        self.assertEquals(n2.offset, 2.0)
    
        post = s.musicxml
        self.assertEquals(s.duration.quarterLength, 2.5)
        self.assertEquals(s.highestTime, 2.5)
        self.assertEquals(s.lowestOffset, 0.0)

        n3 = note.Note('d#5') # octave values can be included in creation arguments
        n3.quarterLength = .25 # a sixteenth note
        s.repeatAppend(n3, 6)
        self.assertEquals(len(s), 8)

        r1 = note.Rest()
        r1.quarterLength = .5
        n4 = note.Note('b5')
        n4.quarterLength = 1.5
        s.insert(4, r1)
        s.insert(4.5, n4)


    def testOverviewMeterA(self):

        sSrc = corpus.parseWork('bach/bwv13.6.xml')
        sPart = sSrc.getElementById('Bass')

        # create a new set of measure partitioning
        # we now have the same notes in new measure objects
        sMeasures = sPart.flat.notes.makeMeasures(meter.TimeSignature('6/8'))

        # measure 2 is at index 1
        self.assertEquals(sMeasures[1].number, 2)

        # getting a measure by context, we should 
        # get the most recent measure that was this note was in
        mCanddiate = sMeasures[1][0].getContextByClass(stream.Measure,
                     sortByCreationTime=True)

        self.assertEquals(mCanddiate, sMeasures[1])


        # from the docs:
        sSrc = corpus.parseWork('bach/bwv57.8.xml')
        sPart = sSrc.getElementById('Alto')
        post = sPart.musicxml

        # we get 3/4
        self.assertEquals(sPart.getElementsByClass('Measure')[0].timeSignature.numerator, 3)
        self.assertEquals(sPart.getElementsByClass('Measure')[1].timeSignature, None)

        sPart.getElementsByClass('Measure')[0].timeSignature = meter.TimeSignature('5/4')
        self.assertEquals(sPart.getElementsByClass('Measure')[0].timeSignature.numerator, 5)
        post = sPart.musicxml

        sNew = sPart.flat.notes
        sNew.insert(0, meter.TimeSignature('2/4'))
        post = sNew.musicxml

        ts = sNew.getTimeSignatures()[0]
        self.assertEquals(ts.numerator, 2)    

        sNew.replace(ts, meter.TimeSignature('5/8'))
        sNew.insert(10, meter.TimeSignature('7/8'))
        sNew.insert(17, meter.TimeSignature('9/8'))
        sNew.insert(26, meter.TimeSignature('3/8'))
        post = sNew.musicxml


        tsStream = sNew.getTimeSignatures()
        tsOffset = [e.offset for e in tsStream]
        self.assertEquals(tsOffset, [0.0, 10.0, 17.0, 26.0])


        sRebar = stream.Stream()
        for part in sSrc.getElementsByClass(stream.Part):
            newPart = part.flat.notes.makeMeasures(tsStream)
            newPart.makeTies(inPlace=True)
            sRebar.insert(0, newPart)
        post = sRebar.musicxml

        #sSrc = corpus.parseWork('bach/bwv57.8.xml')
        sPart = sSrc.getElementById('Soprano')
        self.assertEquals(sPart.flat.notes[0].name, 'B-')
        self.assertEquals(sPart.flat.notes[4].beat, 2.5)
        self.assertEquals(sPart.flat.notes[4].beatStr, '2 1/2')

        for n in sPart.flat.notes:
            n.addLyric(n.beatStr)
        post = sPart.musicxml


        # meter terminal objects
        mt = meter.MeterTerminal('3/4')
        self.assertEquals(mt.numerator, 3)


    def testOverviewMeterB(self):

        sSrc = corpus.parseWork('bach/bwv13.6.xml')

        sPart = sSrc.getElementById('Alto')
        ts = meter.TimeSignature('6/8')

        sMeasures = sPart.flat.notes.makeMeasures(ts)
        #sMeasures.show('t')

        sMeasures.makeTies(inPlace=True)

        # we have the same time signature value, but not the same object
        self.assertEquals(sMeasures[0].timeSignature.numerator, ts.numerator)
        self.assertEquals(sMeasures[0].timeSignature.denominator,
                         ts.denominator)
        # only have ts in first bar
        self.assertEquals(sMeasures[1].timeSignature, None)

        beatStrList = []
        for n in sMeasures.flat.notes:
            bs = n.beatStr
            n.addLyric(bs)
            beatStrList.append(bs)
            #environLocal.printDebug(['offset/activeSite', n, n.offset, n.activeSite, beatStr, 'bestMeasure:', beatMeasure])

        self.assertEquals(beatStrList[:10], ['1', '1 2/3', '2 1/3', '1', '1 2/3', '2 1/3', '1', '1 2/3', '2 1/3', '2 2/3'] )

        # TODO: there is a problem here with tied notes
        # the tied note gets the same offset as its origin
        # need to investigate
        #self.assertEquals(beatStrList, ['1', '1 2/3', '2 1/3', '1', '1 2/3', '2 1/3', '1', '1 2/3', '2 1/3', '2 2/3', '1', '1 1/3', '1 2/3', '2', '2 1/3', '1', '1 2/3', '1', '1 2/3', '2 1/3', '1', '1 2/3', '2 1/3', '1', '1', '1 2/3', '2 1/3', '1', '1 2/3', '2 1/3', '1', '1 2/3', '2 1/3', '1', '1 1/3', '1 2/3', '2', '2 1/3', '2 2/3', '1', '1 1/3', '1 2/3', '2 1/3', '1', '1 2/3', '2 1/3', '1', '1 1/3', '1 2/3', '2 1/3', '2 2/3', '1', '1 2/3', '2', '2 1/3'])

        #sMeasures.show()
        post = sMeasures.musicxml



    def testExamplesA(self):


        # mensural cannon
        from music21 import stream, corpus
        src = corpus.parseWork('bach/bwv323.xml')
        ex = src.getElementById('Soprano').flat.notes[:20]
        
        s = stream.Score()
        for scalar, t in [(1, 'p1'), (2, 'p-5'), (.5, 'p-11'), (1.5, -24)]:
            part = ex.augmentOrDiminish(scalar, inPlace=False)
            part.transpose(t, inPlace=True)
            s.insert(0, part)
        post = s.musicxml
        #s.show()
        # all parts have the same number of notes
        for i in range(3):
            self.assertEqual(len(s.parts[i].flat.notes), 20) 

        self.assertEqual(len(s.parts[0].measures(1,4).flat.notes), 9) 
        self.assertEqual(len(s.parts[1].measures(1,4).flat.notes), 6) 
        self.assertEqual(len(s.parts[2].measures(1,4).flat.notes), 19) 
        self.assertEqual(len(s.parts[3].measures(1,4).flat.notes), 10) 
        


        # counting and searching musical elements
        s = corpus.parseWork("bach/bwv30.6")                
        total = 0
        for p in s.pitches:
            if p.name == 'G#':
                total += 1
        
        self.assertEqual(total, 28) # returns 28



        # finding adjacent chords from a specific root
        from music21 import corpus, stream, note
        
        # Parse a work from the corpus
        s = corpus.parseWork('bwv66.6')        
        # Reduce the work to a series of simultaneities, then extract only
        # the resultant Chords
        chords = s.chordify().getElementsByClass('Chord')
        # Create a Stream for display
        display = stream.Stream()
        # Iterate through the chords by index and a Chord
        for i, c1 in enumerate(chords):
            # Get the next Chord, or a Rest
            if i < len(chords) - 1:
                c2 = chords[i+1]
            else:
                c2 = note.Rest()
            
            # If the root of the Chord is A, collect and display this Chord
            # and the next Chord
            if c1.findRoot().name == 'A':
                m = stream.Measure()
                m.append(c1)
                m.append(c2)
                display.append(m)
        
        self.assertEqual(len(display.flat.getElementsByClass('Chord')), 14)
        for m in display.getElementsByClass('Measure'):
            # get just the first chord
            c  = display.flat.getElementsByClass('Chord')[0]
            self.assertEqual(c.findRoot().name, 'A')
        #display.show()



    def testExamplesB(self):

        from music21 import corpus, chord, stream

        # First, we parse the score and get just the Violin part
        op133 = corpus.parseWork('beethoven/opus133.xml') 
        violin2 = op133.getElementById('2nd Violin')        
        # An empty container is created for later display
        display = stream.Stream() 
        # We iterate over each measure
        for m in violin2.getElementsByClass('Measure'):
        
            # We get a list of consecutive notes, skipping unisons, octaves,
            # and rests 
            notes = m.findConsecutiveNotes(skipUnisons=True, 
                    skipOctaves=True, skipRests=True, noNone=True )
            # From this collection of Notes we gather all Pitches
            pitches = stream.Stream(notes).pitches

            # Taking four Pitches at a time, we create Chords            
            for i in range(len(pitches) - 3):
                c = chord.Chord(pitches[i:i+4])           
                c.duration.type = "whole"                 
                # We test to see if this Chord is a Dominant seventh
                if c.isDominantSeventh():
                    # We label the Chord and the first Note of the Measure
                    c.lyric = "m. " + str(m.number)
                    primeForm = chord.Chord(m.pitches).primeFormString
                    firstNote = m.notes[0]
                    firstNote.lyric = primeForm
                    # The chord (in closed position) and the Measures are 
                    # appended for display 
                    mChord = stream.Measure()
                    mChord.append(c.closedPosition())
                    display.append(mChord)
                    display.append(m)
            
        #display.show()

        # 2 chords found
        self.assertEqual(len(display.flat.getElementsByClass('Chord')), 2)

        c1 = display.getElementsByClass('Measure'
                )[0].getElementsByClass('Chord')[0]
        c2 = display.getElementsByClass('Measure'
                )[2].getElementsByClass('Chord')[0]

        self.assertEqual(c1.isDominantSeventh(), True)
        self.assertEqual(c2.isDominantSeventh(), True)

#             # get just the first chord
#             c  = display.flat.getElementsByClass('Chord')[0]
#             self.assertEqual(c.findRoot().name, 'A')



    def testExamplesC(self):

        from music21 import corpus, analysis, converter
        # Get an analysis tool
        mid = analysis.discrete.MelodicIntervalDiversity()
        results = []
        # Iterate over two regions
        for region in ['shanxi', 'fujian']:
            # Create storage units
            intervalDict = {}
            workCount = 0
            intervalCount = 0
            seventhCount = 0
            # Perform a location search on the corpus and iterate over 
            # resulting file name and work number
            for fp, n in corpus.search(region, 'locale'):
                workCount += 1
                # Parse the work and create a dictionary of intervals
                s = converter.parse(fp, number=n)
                intervalDict = mid.countMelodicIntervals(s, found=intervalDict)
            # Iterate through all intervals, and count totals and sevenths
            for label in intervalDict.keys():
                intervalCount += intervalDict[label][1] 
                if label in ['m7', 'M7']:
                    seventhCount += intervalDict[label][1]
            # Calculate a percentage and store results
            pcentSevenths = round((seventhCount / float(intervalCount) * 100), 
                            4)
            results.append((region, pcentSevenths, intervalCount, workCount))
    
        # Print results
        for region, pcentSevenths, intervalCount, workCount in results: 
            pass
        #print('locale: %s: found %s percent melodic sevenths, out of %s intervals in %s works' % (region, pcentSevenths, intervalCount, workCount))

        region, pcentSevenths, intervalCount, workCount = results[0]
        self.assertEqual(region, 'shanxi')
        self.assertEqual(pcentSevenths, 3.1994)
        self.assertEqual(intervalCount, 4282)
        self.assertEqual(workCount, 77)

        region, pcentSevenths, intervalCount, workCount = results[1]
        self.assertEqual(region, 'fujian')
        self.assertEqual(pcentSevenths, 0.7654)
        self.assertEqual(intervalCount, 2613)
        self.assertEqual(workCount, 53)



    def testExamplesD(self):
        from music21 import corpus
        # Parse an Opus, a collection of Scores
        o = corpus.parseWork('josquin/laDeplorationDeLaMorteDeJohannesOckeghem')
        # Create a Score from a Measure range
        sExcerpt = o.mergeScores().measures(127, 133)
        # Create a reduction of Chords
        reduction = sExcerpt.chordify()
        # Iterate over the Chords and prepare presentation
        for c in reduction.flat.getElementsByClass('Chord'):
            c.closedPosition(forceOctave=4, inPlace=True)
            c.removeRedundantPitches(inPlace=True)
            c.annotateIntervals()
        # Add the reduction and display the results
        sExcerpt.insert(0, reduction)
        #sExcerpt.show()

        self.assertEqual(len(sExcerpt.flat.getElementsByClass('Chord')), 13)

        self.assertEqual(str(sExcerpt.flat.getElementsByClass('Chord')[1]), '<music21.chord.Chord E4 G4 B4 E5>')

        self.assertEqual(str(sExcerpt.flat.getElementsByClass('Chord')[2]), '<music21.chord.Chord E4 G4 E5>')
        self.assertEqual(str(sExcerpt.flat.getElementsByClass('Chord')[3]), '<music21.chord.Chord D4 F4 A4 D5>')
        self.assertEqual(str(sExcerpt.flat.getElementsByClass('Chord')[4]), '<music21.chord.Chord D4 F4 A4 D5>')
        self.assertEqual(str(sExcerpt.flat.getElementsByClass('Chord')[5]), '<music21.chord.Chord D4 F4 A4 D5>')
        self.assertEqual(str(sExcerpt.flat.getElementsByClass('Chord')[6]), '<music21.chord.Chord A4 C5 E5>')
        self.assertEqual(str(sExcerpt.flat.getElementsByClass('Chord')[7]), '<music21.chord.Chord A4 C5>')

        self.assertEqual(str(sExcerpt.flat.getElementsByClass('Chord')[8]), '<music21.chord.Chord G4 A4 B4 C5>')
        self.assertEqual(str(sExcerpt.flat.getElementsByClass('Chord')[9]), '<music21.chord.Chord F4 A4 D5>')

        self.assertEqual(str(sExcerpt.flat.getElementsByClass('Chord')[10]), '<music21.chord.Chord F4 G4 A4 D5>')

        self.assertEqual(str(sExcerpt.flat.getElementsByClass('Chord')[11]), '<music21.chord.Chord F4 A4 D5>')
        self.assertEqual(str(sExcerpt.flat.getElementsByClass('Chord')[12]), '<music21.chord.Chord E4 G4 B4 E5>')


    def testExamplesE(self):
        # 100:150 finds 2
        # 150:200 finds 1
        # 200:250 finds 2
        # 250:300 finds 1
        # 300:350 finds 3

        from music21 import corpus, converter, chord
        # Create storage for the results
        results = stream.Stream()
        # Get file paths to all Chorales
        for fp in corpus.bachChorales[310:330]:
            # Parse, and then analyze the key
            chorale = converter.parse(fp)
            key, mode = chorale.analyze('key')[:2]
            # Select minor-mode chorales
            if mode == 'minor':
                # Gather last pitches from all parts into a Chord
                lastChordPitches = []
                for part in chorale.parts:
                    lastChordPitches.append(part.flat.pitches[-1])
                cLast = chord.Chord(lastChordPitches)
                cLast.duration.type = "whole"
                cLast.transpose("P8", inPlace=True)
                # If a minor triad, append to results with annotations
                if cLast.isMinorTriad() or cLast.isIncompleteMinorTriad():
                    cLast.lyric = chorale.metadata.title
                    m = stream.Measure()
                    m.keySignature = chorale.flat.getElementsByClass(
                      'KeySignature')[0]
                    m.append(cLast)
                    results.append(m.makeAccidentals(inPlace=True))
        #results.show()
        self.assertEqual(len(results.flat.getElementsByClass('Chord')), 2)
        self.assertEqual(str(results.flat.getElementsByClass('Chord')[0]), '<music21.chord.Chord A5 C5 E4 A3>')
        self.assertEqual(str(results.flat.getElementsByClass('Chord')[1]), '<music21.chord.Chord A5 C5 A4 A3>')


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        t = Test()


        #t.testExamplesA()

        t.testOverviewMeterB()
        #t.testExamplesB()
        #t.testExamplesC()

        #t.testExamplesD()
        #t.testExamplesE()


#------------------------------------------------------------------------------
# eof

