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
        self.assertEquals(sMeasures[1].measureNumber, 2)

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