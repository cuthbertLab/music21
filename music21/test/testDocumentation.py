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
            #environLocal.printDebug(['offset/parent', n, n.offset, n.parent, beatStr, 'bestMeasure:', beatMeasure])

        self.assertEquals(beatStrList, ['1', '1 2/3', '2 1/3', '1', '1 2/3', '2 1/3', '1', '1 2/3', '2 1/3', '2 2/3', '1', '1 1/3', '1 2/3', '2', '2 1/3', '1', '1 2/3', '1', '1 2/3', '2 1/3', '1', '1 2/3', '2 1/3', '1', '1', '1 2/3', '2 1/3', '1', '1 2/3', '2 1/3', '1', '1 2/3', '2 1/3', '1', '1 1/3', '1 2/3', '2', '2 1/3', '2 2/3', '1', '1 1/3', '1 2/3', '2 1/3', '1', '1 2/3', '2 1/3', '1', '1 1/3', '1 2/3', '2 1/3', '2 2/3', '1', '1 2/3', '2', '2 1/3'])

        #sMeasures.show()
        post = sMeasures.musicxml



    def testExamples(self):

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
        
        
        


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        a = Test()


        #a.testExamples()

        a.testOverviewMeterB()