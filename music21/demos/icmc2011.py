#-------------------------------------------------------------------------------
# Name:         smt2011.py
# Purpose:      Demonstrations for the SMT 2011 poster session
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------






import unittest, doctest
from music21 import *

_MOD = 'demo/smt2010.py'
environLocal = environment.Environment(_MOD)




#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        ''' 
        '''
        pass
    


    def testStreams01(self):
        from music21 import note, stream, clef, metadata, spanner


        #==== "fig-df02"

        n1 = note.Note('g3', type='half')
        n2 = note.Note('d4', type='half')
        n3 = note.Note('g#3', quarterLength=0.5)
        n4 = note.Note('d-4', quarterLength=3.5)
        cf1 = clef.AltoClef()

        m1 = stream.Measure()
        m1.append([n1, n2])
        m1.insert(0, cf1)

        # the measure has three elements
        assert len(m1) == 3
        # the offset returned is the most-recently set
        assert n2.offset == 2.0
        # automatic sorting positions Clef first
        assert m1[0] == cf1
        # list-like indices follow sort order 
        assert m1.index(n2) == 2
        # can find an element based on a given offset
        assert m1.getElementAtOrBefore(3) == n2 

        m2 = stream.Measure()
        m2.append([n3, n4])

        # appended position is after n3
        assert n4.offset == .5 
        assert m2.highestOffset == .5 
        # can access objects on elements
        assert m2[1].duration.quarterLength == 3.5 
        # the Stream duration is the highest offset + duration
        assert m2.duration.quarterLength == 4 

        p1 = stream.Part()
        p1.append([m1, m2])

        # the part has 2 components
        assert len(p1) == 2
        # the Stream duration is the highest offset + durations
        assert p1.duration.quarterLength == 8
        # can access notes using multiple indices
        assert p1[1][0].pitch.nameWithOctave == 'G#3'

        s1 = stream.Score()
        s1.append(p1)
        md = metadata.Metadata(title='The music21 Stream')
        s1.insert(0, md)
        # calling show by default renders musicxml output
        #s1.show()

        #==== "fig-df02" end



        #==== "fig-df03"
        # show positioning the same element in multiple containers
        # do not yet use a flat representation
        s2 = stream.Stream()
        s3 = stream.Stream()        
        s2.insert(10, n2)
        s3.insert(40, n2)
            
        # the offset attribute returns the last assigned
        assert n2.offset == 40
        # we can provide a site to finde a location-specific offset
        assert n2.getOffsetBySite(m1) == 2.0
        assert n2.getOffsetBySite(s2) == 10
        # the None site provides a default offset
        assert n2.getSites() == [None, m1, s2, s3]
        # the same instance is found in all Streams
        assert m1.hasElement(n2) == True
        assert s2.hasElement(n2) == True
        assert s3.hasElement(n2) == True

        # only offset is independent to each location
        n2.pitch.transpose('-M2', inPlace=True)
        assert s2[s2.index(n2)].nameWithOctave == 'C4'
        assert s3[s3.index(n2)].nameWithOctave == 'C4'
        assert m1[m1.index(n2)].nameWithOctave == 'C4'

        # the transposition is maintained in the original context
        #s1.show()

        #==== "fig-df03" end








        # tests
        self.assertEqual(m1.clef, cf1)



        r1 = note.Rest(type='whole')




    def testEx01(self):
        # Basic operations for creating and manipulating scales.

        sc1 = scale.MajorScale('a-')

        # get pitches from any range of this scale
        print(sc1.getPitches('g2', 'c4'))
        self.assertEqual(str(sc1.getPitches('g2', 'c4')), 
        '[G2, A-2, B-2, C3, D-3, E-3, F3, G3, A-3, B-3, C4]')

        # get a scale degree from a pitch
        print(sc1.getScaleDegreeFromPitch('b-'))
        self.assertEqual(sc1.getScaleDegreeFromPitch('b-'), 2)

        # what is the scale degree of the pitch in relative minor
        print(str(sc1.getRelativeMinor().getScaleDegreeFromPitch('b-')))
        self.assertEqual(sc1.getRelativeMinor().getScaleDegreeFromPitch('b-'), 4)

        # given a pitch in this scale, what is the next pitch
        print(sc1.next('g2', 'ascending'))
        self.assertEqual(str(sc1.next('g2', 'ascending')), 'A-2')

        # descending three scale steps
        print(sc1.next('g2', 'descending', 3))
        self.assertEqual(str(sc1.next('g2', 'descending', 3)), 'D-2')


        # derive a new major scale based on a pitch for a scale degree
        print(sc1.deriveByDegree(7, 'f#4').pitches)
        self.assertEqual(str(sc1.deriveByDegree(7, 'f#4').pitches), 
            '[G3, A3, B3, C4, D4, E4, F#4, G4]')


        # a whole tone scale
        sc2 = scale.WholeToneScale('f#')

        # get pitches from any range of this scale
        print str(sc2.getPitches('g2', 'c4'))
        self.assertEqual(str(sc2.getPitches('g2', 'c4')), 
        '[A-2, B-2, C3, D3, F-3, G-3, A-3, B-3, C4]')

            # get a scale degree from a pitch
        print(str(sc2.getScaleDegreeFromPitch('e')))
        self.assertEqual(sc2.getScaleDegreeFromPitch('e'), 6)

        # given a pitch in this scale, what is the next pitch
        print(sc2.next('d4', 'ascending'))
        self.assertEqual(str(sc2.next('d4', 'ascending')), 'E4')


        # transpose the scale
        print(sc2.transpose('m2').pitches)
        self.assertEqual(str(sc2.transpose('m2').pitches), '[G4, A4, B4, C#5, D#5, E#5, G5]')

        # get as a chord and get its forte class
        self.assertEqual(sc2.transpose('m2').chord.forteClass, '6-35')



    def testEx02(self): 
        # Labeling a vocal part based on scale degrees derived from key signature and from a specified target key.

        s = corpus.parseWork('hwv56/movement3-03.md')#.measures(1,7)
        basso = s.parts['basso']
        s.remove(basso)
        
        ksScale = s.flat.getElementsByClass('KeySignature')[0].getScale()
        targetScale = scale.MajorScale('A')
        for n in basso.flat.getElementsByClass('Note'):
            # get the scale degree from this pitch
            n.addLyric(ksScale.getScaleDegreeFromPitch(n.pitch))
            n.addLyric(targetScale.getScaleDegreeFromPitch(n.pitch))
        
        reduction = s.chordify()
        for c in reduction.flat.getElementsByClass('Chord'):
            c.closedPosition(forceOctave=4, inPlace=True)
            c.removeRedundantPitches(inPlace=True)
        
        
        display = stream.Score()
        display.insert(0, basso)
        display.insert(0, reduction)
        #display.show()




    def testEx03(self):

        # What is the most common closing soprano scale degree by key signature
        # in the bach chorales?
        from music21 import graph

        results = {}
        for fn in corpus.bachChorales[:2]:
            s = corpus.parseWork(fn)
            ksScale = s.flat.getElementsByClass('KeySignature')[0].getScale()
            for p in s.parts:
                if p.id.lower() == 'soprano':
                    n = s.parts['soprano'].flat.getElementsByClass('Note')[-1]
                    degree = ksScale.getScaleDegreeFromPitch(n.pitch)
                    if degree not in results.keys():
                        results[degree] = 0
                    results[degree] += 1
        print(results)

        # Results for all Bach chorales
        #{1: 307, 2: 3, 3: 11, 4: 31, 5: 34, 6: 5, 7: 2, None: 3}

        #g = graph.GraphHistogram()
        #g.setData([(x, y) for x, y in sorted(results.items())])
        #g.process()

    def xtestEx04(self):
        # what

        scSrc = scale.MajorScale()

        niederlande = corpus.search('niederlande', 'locale')

        results = {}
        for name, group in [('niederlande', niederlande)]:
            workCount = 0

            for fp, n in group:
                workCount += 1
    
                s = converter.parse(fp, number=n)
    
                # derive a best-fit concrete major scale
                scFound = scSrc.derive(s)

                # if we find a scale with no unmatched pitches
                if len(scFound.match(s)['notMatched']) == 0:
                    # find out what pitches in major scale are not used
                    post = scFound.findMissing(s)
                    for p in post:
                        degree = scFound.getScaleDegreeFromPitch(p)
                        if degree not in results.keys():
                            results[degree] = 0
                        results[degree] += 1

        print ('Of %s works, the following major scale degrees are not used the the following number of times:' % workCount)
        print results

        #Of 104 works, the following major scale degrees are not used the the following number of times:
        #{4: 5, 5: 1, 6: 6, 7: 6}



if __name__ == "__main__":
    import music21
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)

    elif len(sys.argv) > 1:
        t = Test()
        #t.testEx02()
        #t.testEx03()
        #t.testEx04()

        t.testStreams01()

#------------------------------------------------------------------------------
# eof


