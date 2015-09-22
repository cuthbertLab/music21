# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         icmc2011.py
# Purpose:      Demonstrations for the ICMC 2011 poster session
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-11 Michael Scott Cuthbert and the music21 Project
# License:      BSD or LGPL, see license.txt
#-------------------------------------------------------------------------------

import unittest
from music21 import alpha, note, stream, clef, metadata, spanner, environment, converter, scale, corpus, common


_MOD = 'demo/icmc2011.py'
environLocal = environment.Environment(_MOD)




#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass
    


    def testStreams01(self):
        #from music21 import note, stream, clef, metadata, spanner


        #==== "fig-df02"
        # Storing, Ordering, and Timing Elements

        n1 = note.Note('g3', type='half')
        n2 = note.Note('d4', type='half')
        n3 = note.Note('g#3', quarterLength=0.5)
        n4 = note.Note('d-4', quarterLength=3.5)
        cf1 = clef.AltoClef()
        
        m1 = stream.Measure(number=1)
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
        
        m2 = stream.Measure(number=2)
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
        # can access Notes from Part using multiple indices
        assert p1[1][0].pitch.nameWithOctave == 'G#3'
        
        s1 = stream.Score()
        s1.append(p1)
        md1 = metadata.Metadata(title='The music21 Stream')
        s1.insert(0, md1)
        # calling show by default renders musicxml output
        #s1.show()

        #==== "fig-df02" end



        #==== "fig-df03"
        # Positioning the Same Element in Multiple Containers
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
        assert set(n2.sites.getSites()) == set([None, m1, s2, s3])
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




        #==== "fig-df04"
        # Simultaneous Access to Hierarchical and Flat Representations
        #s1.flat.show('t')

        # lengths show the number of elements; indices are sequential
        s1Flat = s1.flat
        assert len(s1) == 2
        assert len(s1Flat) == 6
        assert s1Flat[4] == n3
        assert s1Flat[5] == n4
        
        # adding another Part to the Score results in a different flat representation
        n5 = note.Note('a#1', quarterLength=2.5)
        n6 = note.Note('b2', quarterLength=1.5)
        m4 = stream.Measure(number=2)
        m4.append([n5, n6])
        
        r1 = note.Rest(type='whole')
        cf2 = m4.bestClef() # = BassClef
        m3 = stream.Measure(number=1)
        m3.append([cf2, r1])
        
        p2 = stream.Part()
        p2.append([m3, m4])
        s1.insert(0, p2)

        assert 'BassClef' in cf2.classes
        
        # objects are sorted by offset
        s1Flat = s1.flat
        assert len(s1) == 3
        assert len(s1.flat) == 10
        assert s1Flat[6] == n3
        assert s1Flat[7] == n5
        assert s1Flat[8] == n4
        assert s1Flat[9] == n6
        
        # the F-sharp in m. 2 now as offsets for both flat non-flat sites
        assert n3.getOffsetBySite(m2) == 0
        assert n3.getOffsetBySite(s1Flat) == 4
        # the B in m. 2 now as offsets for both flat non-flat sites
        assert n6.getOffsetBySite(m4) == 2.5
        assert n6.getOffsetBySite(s1Flat) == 6.5
        
        #s1.show()

        #==== "fig-df04" end




        #==== "fig-df05"
        # Iterating and Filtering Elements by Class


        # get the Clef object, and report its sign, from Measure 1
        assert m1.getElementsByClass('Clef')[0].sign == 'C'
        # collect into a list the sign of all clefs in the flat Score
        assert [cf.sign for cf in s1.flat.getElementsByClass('Clef')] == ['C', 'F']
        
        # collect the offsets Measures in the first part
        assert [e.offset for e in p1.elements] == [0.0, 4.0]
        # collect the offsets of Note in the first part flattened
        assert [e.offset for e in p1.flat.notesAndRests] == [0.0, 2.0, 4.0, 4.5]
        # collect the offsets of Notes in all parts flattened
        assert [e.offset for e in s1.flat.notesAndRests] == [0.0, 0.0, 2.0, 4.0, 4.0, 4.5, 6.5]
        
        
        # get all pitch names
        match = []
        for e in s1.flat.getElementsByClass('Note'):
            match.append(e.pitch.nameWithOctave)
        assert match == ['G3', 'C4', 'G#3', 'A#1', 'D-4', 'B2']
        
        # collect all Notes and transpose up a perfect fifth
        for n in s1.flat.getElementsByClass('Note'):
            n.transpose('P5', inPlace=True)
        
        # check that all pitches are correctly transposed
        match = []
        for e in s1.flat.getElementsByClass('Note'):
            match.append(e.pitch.nameWithOctave)    
        assert match == ['D4', 'G4', 'D#4', 'E#2', 'A-4', 'F#3']
        
        #s1.show()

        #==== "fig-df05" end





        #==== "fig-df06"
        # Searching by Locations and Contexts

        # a Note can always find a Clef
        assert n4.getContextByClass('Clef') == cf1
        # must search oldest sites first
        assert n6.getContextByClass('Clef', sortByCreationTime='reverse') == cf2
        
        
#        # a Note can find their Measure number from a flat Part
#        match = []
#        for e in p1.flat.getElementsByClass('Note'):
#            match.append(e.getContextByClass('Measure').number)    
#        assert match == [1, 1, 2, 2]
        
        # all Notes can find their Measure number from a flat Score
        match = []
        for e in s1.flat.notesAndRests:
            match.append([e.name, e.getContextByClass('Measure').number])   
        assert match == [['D', 1], ['rest', 1], ['G', 1], ['D#', 2], ['E#', 2], ['A-', 2], ['F#', 2]]
        #==== "fig-df06" end




        #==== "fig-df06"
        # Non-Hierarchical Object Associations
        #oldIds = []
        #for idKey in n1.sites.siteDict:
        #    print (idKey, n1.sites.siteDict[idKey].isDead)
        #    oldIds.append(idKey)
        #print("-------")

        # Spanners can be positioned in Parts or Measures
        sp1 = spanner.Slur([n1, n4])
        p1.append(sp1)
        sp2 = spanner.Slur([n5, n6])
        m4.insert(0, sp2)

        #print(id(sp1), id(sp1.spannerStorage), n1.sites.siteDict[id(sp1.spannerStorage)].isDead)
        #if id(sp1.spannerStorage) in oldIds:
        #    print ("******!!!!!!!!!*******")
        
        # Elements can report on what Spanner they belong to
        ss1 = n1.getSpannerSites()
        self.assertTrue(sp1 in ss1, (ss1, sp1))
        
        ss6 = n6.getSpannerSites()
        assert sp2 in ss6

        p1Flat = p1.flat
        assert sp1.getDurationSpanBySite(p1Flat) == [0.0, 8.0]
        
        p2Flat = p2.flat
        assert sp2.getDurationSpanBySite(p2Flat) == [4.0, 8.0]
        
        #s1.show()
        #==== "fig-df06" end


        # additional tests 
        self.assertEqual(m1.clef, cf1)




    def testStreams02(self):

        # based on Stream.testAddSlurByMelisma(self):

        #from music21 import corpus, spanner
        nStart = None
        nEnd = None
        
        ex = corpus.parse('luca/gloria').parts['cantus'].measures(1,11)        
        exFlatNotes = ex.flat.notesAndRests
        nLast = exFlatNotes[-1]
        
        for i, n in enumerate(exFlatNotes):
            if i < len(exFlatNotes) - 1:
                nNext = exFlatNotes[i+1]
            else: continue
        
            if n.hasLyrics():
                nStart = n
            # if next is a begin, then this is an end
            elif nStart is not None and nNext.hasLyrics() and n.tie is None:
                nEnd = n
            elif nNext is nLast:
                nEnd = n
            if nStart is not None and nEnd is not None:
                nStart.addLyric(nStart.beatStr)
                ex.insert(spanner.Slur(nStart, nEnd))
                nStart = None
                nEnd = None
        
        for sp in ex.spanners.getElementsByClass('Slur'):  
            #environLocal.printDebug(['sp', n.nameWithOctave, sp])
            unused_dur = sp.getDurationBySite(exFlatNotes)
            n = sp.getFirst()
            
        
        #ex.show()





    def testScales01(self):
        from music21 import pitch


        #==== "fig-py01"

        # Providing a tonic makes this concrete
        sc1 = scale.MajorScale('g4')
        sc2 = scale.MajorScale('e-3')
        
        # Comparing Concrete and Abstract Scales
        assert (sc1 == sc2) == False
        assert (sc1.abstract == sc2.abstract) == True
        
        # Without arguments, getPitches() returns a single span 
        assert common.pitchList(sc1.getPitches()) == '[G4, A4, B4, C5, D5, E5, F#5, G5]'
        assert common.pitchList(sc2.getPitches('c2', 'c3')) == '[C2, D2, E-2, F2, G2, A-2, B-2, C3]'
        
        # As a Chord, Scale pitches gain additional functionality
        assert sc1.getChord().forteClass == '7-35'
        
        # Given a degree, get the pitch
        assert str(sc1.pitchFromDegree(5)) == 'D5'
        assert common.pitchList(sc2.pitchesFromScaleDegrees([7,2], 'e-6', 'e-9')) == '[F6, D7, F7, D8, F8, D9]'
        
        # Get a scale degree from a pitch
        assert sc1.getScaleDegreeFromPitch('d') == 5
        assert sc2.getScaleDegreeFromPitch('d') == 7
        
        # Get the next pitch given step directions
        match = [pitch.Pitch('g2')]
        for direction in [1, 1, 1, -2, 4, -1, 1, 1, 1]:
            # Append the next pitch based on the last-added pitch
            match.append(sc1.next(match[-1], direction))
        assert common.pitchList(match), '[G2, A2, B2, C3, A2, E3, D3, E3, F#3, G3]'
        
        # Derive new scales based on a provided collection or degree
        assert str(sc1.derive(['c4', 'g4', 'b8', 'f2'])) == '<music21.scale.MajorScale C major>'
        assert str(sc1.deriveByDegree(7, 'C#')) == '<music21.scale.MajorScale D major>'
        
        # Methods unique to DiatonicScale subclasses
        assert str(sc2.getRelativeMinor()) == '<music21.scale.MinorScale C minor>'
        #==== "fig-py01" end



        #==== "fig-py02"
        sc1 = scale.PhrygianScale('g4')
        assert common.pitchList(sc1.getPitches()) == '[G4, A-4, B-4, C5, D5, E-5, F5, G5]'
        assert str(sc1.getRelativeMajor()) == '<music21.scale.MajorScale E- major>'
        assert str(sc1.getTonic()), str(sc1.getDominant()) == ('G4', 'D5')
        
        sc2 = scale.HypodorianScale('a6')
        assert common.pitchList(sc2.getPitches('e2', 'e3')) == '[E2, F#2, G2, A2, B2, C3, D3, E3]'
        assert str(sc2.getRelativeMajor()) == '<music21.scale.MajorScale G major>'
        assert str(sc2.getTonic()), str(sc2.getDominant()) == ('A6', 'C7')

        #==== "fig-py02" end



        #==== "fig-py06"
        # see below
        #==== "fig-py06" end




        #==== "fig-py03"
        #print('\n\nfig-py03')

        sc1 = scale.HarmonicMinorScale('a3')
        assert common.pitchList(sc1.getPitches()) == '[A3, B3, C4, D4, E4, F4, G#4, A4]'
        assert str(sc1.getTonic()), str(sc1.getDominant()) == ('A3', 'E4')
        
        s = stream.Stream()    
        for d in [1, 3, 2, 1, 6, 5, 8, 7, 8]:
            s.append(note.Note(
                sc1.pitchFromDegree(d, equateTermini=False),
                type='eighth'))
        #s.show()
        #==== "fig-py03" end




        #==== "fig-py04"
        import random


        sc1 = scale.MelodicMinorScale('c4')
        assert common.pitchList(sc1.getPitches(direction='ascending')) == '[C4, D4, E-4, F4, G4, A4, B4, C5]'
        assert common.pitchList(sc1.getPitches('c3', 'c5', direction='descending')) == '[C5, B-4, A-4, G4, F4, E-4, D4, C4, B-3, A-3, G3, F3, E-3, D3, C3]'
        assert str(sc1.getTonic()), str(sc1.getDominant()) == ('C4', 'G4')
        
        s = stream.Stream()
        p = None
        for i in range(16):
            direction = random.choice([-1, 1])
            for j in range(2):
                p = sc1.next(p, direction)
                s.append(note.Note(p, quarterLength=.25))
        #s.show()
        #==== "fig-py04" end



        #==== "fig-py05"
        sc1 = scale.OctatonicScale('e3', 'm2')
        assert common.pitchList(sc1.getPitches()) == '[E3, F3, G3, A-3, B-3, C-4, D-4, D4, E4]'
        sc2 = scale.OctatonicScale('e3', 'M2')
        assert common.pitchList(sc2.getPitches()) == '[E3, F#3, G3, A3, B-3, C4, D-4, E-4, F-4]'
        
        part1 = stream.Part()
        part2 = stream.Part()
        durPart1 = [1,1,.5,.5,1]
        durPart2 = [3,1]
        degrees = list(range(1,9))
        for unused in range(4):
            random.shuffle(degrees)
            random.shuffle(durPart1)
            random.shuffle(durPart2)
            i = 0
            for dur in durPart1:
                part1.append(note.Note(sc2.pitchFromDegree(degrees[i]),
                            quarterLength = dur))
                i += 1
            for dur in durPart2:
                part2.append(note.Note(
                    sc2.pitchFromDegree(degrees[i], minPitch='c2', maxPitch='c3'),
                    quarterLength=dur))
                i += 1
        s = stream.Score()
        s.insert(0, part1)
        s.insert(0, part2)
        #s.show()

        # add notation example; perhaps create tri-chords from scale-completing selections
        #==== "fig-py05" end




        #sc = scale.SieveScale('c2', '(-3@2 & 4) | (-3@1 & 4@1) | (3@2 & 4@2) | (-3 & 4@3)') 

        #==== "fig-py07"
        # add examples
        sc1 = scale.SieveScale('c4', '3@0|4@0')
        assert common.pitchList(sc1.getPitches()) == '[C4, E-4, F-4, G-4, A-4, A4, C5]'
        
        sc2 = scale.SieveScale('c4', '5@0|7@0')
        assert common.pitchList(sc2.getPitches()) == '[C4, F4, G4, B-4, D5, E-5, A-5, A5, C#6, E6, F#6, B6]'
        
        s = stream.Stream()
        pColection = sc2.getPitches('c3', 'c7')
        random.shuffle(pColection)
        for p in pColection:
            s.append(note.Note(p, type='16th'))
        #s.show()
        #==== "fig-py07" end




        #==== "fig-py08"

        sc1 = scale.RagAsawari('g3')
        assert common.pitchList(sc1.getPitches(direction='ascending')) == '[G3, A3, C4, D4, E-4, G4]'
        assert common.pitchList(sc1.getPitches(direction='descending')) == '[G4, F4, E-4, D4, C4, B-3, A3, G3]'
        
        
        sc2 = scale.RagMarwa('g3')
        assert common.pitchList(sc2.getPitches(direction='ascending')) == '[G3, A-3, B3, C#4, E4, F#4, E4, G4, A-4]'
        assert common.pitchList(sc2.getPitches(direction='descending')) == '[A-4, G4, A-4, F#4, E4, C#4, B3, A-3, G3]'
        
        
        p1 = None
        s = stream.Stream()
        for direction in ([1]*10) + ([-1]*8) + ([1]*4) + ([-1]*3) + ([1]*4):
            p1 = sc1.next(p1, direction)
            s.append(note.Note(p1, quarterLength=.25))
        #s.show()
        
        p1 = None
        s = stream.Stream()
        for direction in ([1]*10) + ([-1]*8) + ([1]*4) + ([-1]*3) + ([1]*4):
            p1 = sc2.next(p1, direction)
            s.append(note.Note(p1, quarterLength=.25))
        #s.show()

        #==== "fig-py08" end


        #==== "fig-py09"
        #import random
        sc1 = scale.WeightedHexatonicBlues('c3')
        p = 'c3'
        s = stream.Stream()
        for n in range(32):
            p = sc1.next(p, random.choice([-1, 1]))
            n = note.Note(p, quarterLength=random.choice([.5,.25,.25]))
            s.append(n)
        #s.show()
        #==== "fig-py09" end




    def testScalesPy06(self):
        #from music21 import corpus, scale, note
        #from music21 import analysis

        scGMajor = scale.MajorScale('g4')
        scDMajor = scale.MajorScale('d4')
        s = corpus.parse('mozart/k80/movement1').measures(21,25)
        s.remove(s['cello'])
        s.remove(s['viola'])
        for part in s.parts: 
            for sc in [scGMajor, scDMajor]:
                groups = alpha.analysis.search.findConsecutiveScale(part.flat, sc, degreesRequired=5, comparisonAttribute='name')
                for group in groups:
                    for n in group['stream'].notesAndRests:
                        n.addLyric('%s^%s' % (sc.getTonic().name, sc.getScaleDegreeFromPitch(n.pitch)))
        #s['violin i'].show()



#     def testScalesPy10(self):
#         # look through s = corpus.parse('bwv1080/06')
#         #part = corpus.parse('bwv1080/03').measures(24,29).parts[0]
#         #part = corpus.parse('bwv1080/03').parts[0]
# 
#         #from music21 import corpus, scale, note
#         from music21 import analysis
# 
#         scDMelodicMinor = scale.MelodicMinorScale('d4')
#         scGMelodicMinor = scale.MelodicMinorScale('g4')
#         part = corpus.parse('bwv1080/03').parts[0].measures(46,53)
#         
#         for sc in [scDMelodicMinor, scGMelodicMinor]:
#             groups = alpha.analysis.search.findConsecutiveScale(part.flat, sc, degreesRequired=4, comparisonAttribute='name')
#             for group in groups:
#                 for n in group['stream'].notes:
#                     n.addLyric('%s^%s' % (sc.getTonic().name.lower(), sc.getScaleDegreeFromPitch(n.pitch, group['direction'])))
#         #part.show()





        # this is applied to all  parts
#         s = corpus.parse('mozart/k80/movement1').measures(1,28)
#         for sc in [scGMajor, scDMajor, scAMajor]:
#             for part in s.parts: 
#                 post = alpha.analysis.search.findConsecutiveScale(part.flat, sc, degreesRequired=5,             
#                        comparisonAttribute='name')
#                 for g, group in enumerate(post):
#                     for n in group:
#                         n.addLyric('%s%s' % (sc.getTonic().name, g+1))
#         s.show()












    def testEx01(self):
        # Basic operations for creating and manipulating scales.

        sc1 = scale.MajorScale('a-')

        # get pitches from any range of this scale
        #print(sc1.getPitches('g2', 'c4'))
        self.assertEqual(', '.join([p.nameWithOctave for p in sc1.getPitches('g2', 'c4')]), 
        'G2, A-2, B-2, C3, D-3, E-3, F3, G3, A-3, B-3, C4')

        # get a scale degree from a pitch
        #print(sc1.getScaleDegreeFromPitch('b-'))
        self.assertEqual(sc1.getScaleDegreeFromPitch('b-'), 2)

        # what is the scale degree of the pitch in relative minor
        #print(str(sc1.getRelativeMinor().getScaleDegreeFromPitch('b-')))
        self.assertEqual(sc1.getRelativeMinor().getScaleDegreeFromPitch('b-'), 4)

        # given a pitch in this scale, what is the next pitch
        #print(sc1.next('g2', 'ascending'))
        self.assertEqual(str(sc1.next('g2', 'ascending')), 'A-2')

        # descending three scale steps
        #print(sc1.next('g2', 'descending', 3))
        self.assertEqual(str(sc1.next('g2', 'descending', 3)), 'D-2')


        # derive a new major scale based on a pitch for a scale degree
        #print(sc1.deriveByDegree(7, 'f#4').pitches)
        self.assertEqual(common.pitchList(sc1.deriveByDegree(7, 'f#4').pitches), 
            '[G3, A3, B3, C4, D4, E4, F#4, G4]')


        # a whole tone scale
        sc2 = scale.WholeToneScale('f#')

        # get pitches from any range of this scale
        #print str(sc2.getPitches('g2', 'c4'))
        self.assertEqual(common.pitchList(sc2.getPitches('g2', 'c4')), 
        '[A-2, B-2, C3, D3, F-3, G-3, A-3, B-3, C4]')

            # get a scale degree from a pitch
        #print(str(sc2.getScaleDegreeFromPitch('e')))
        self.assertEqual(sc2.getScaleDegreeFromPitch('e'), 6)

        # given a pitch in this scale, what is the next pitch
        #print(sc2.next('d4', 'ascending'))
        self.assertEqual(str(sc2.next('d4', 'ascending')), 'E4')


        # transpose the scale
        #print(sc2.transpose('m2').pitches)
        self.assertEqual(common.pitchList(sc2.transpose('m2').pitches), '[G4, A4, B4, C#5, D#5, E#5, G5]')

        # get as a chord and get its forte class
        self.assertEqual(sc2.transpose('m2').chord.forteClass, '6-35')






#     def testEx02(self): 
#         # Labeling a vocal part based on scale degrees derived from key signature and from a specified target key.
# 
#         s = corpus.parse('hwv56/movement3-03.md')#.measures(1,7)
#         basso = s.parts['basso']
#         s.remove(basso)
#         
#         ksScale = s.flat.getElementsByClass('KeySignature')[0].getScale()
#         targetScale = scale.MajorScale('A')
#         for n in basso.flat.getElementsByClass('Note'):
#             # get the scale degree from this pitch
#             n.addLyric(ksScale.getScaleDegreeFromPitch(n.pitch))
#             n.addLyric(targetScale.getScaleDegreeFromPitch(n.pitch))
#         
#         reduction = s.chordify()
#         for c in reduction.flat.getElementsByClass('Chord'):
#             c.closedPosition(forceOctave=4, inPlace=True)
#             c.removeRedundantPitches(inPlace=True)
#         
#         
#         display = stream.Score()
#         display.insert(0, basso)
#         display.insert(0, reduction)
#         #display.show()




    def testEx03(self):

        # What is the most common closing soprano scale degree by key signature
        #s in the bach chorales?
        #from music21 import graph

        results = {}
        for fn in corpus.getBachChorales()[:2]:
            s = corpus.parse(fn)
            ksScale = s.flat.getElementsByClass('KeySignature')[0].getScale()
            for p in s.parts:
                if p.id.lower() == 'soprano':
                    n = s.parts['soprano'].flat.getElementsByClass('Note')[-1]
                    degree = ksScale.getScaleDegreeFromPitch(n.pitch)
                    if degree not in results.keys():
                        results[degree] = 0
                    results[degree] += 1
        #print(results)

        # Results for all Bach chorales
        #{1: 307, 2: 3, 3: 11, 4: 31, 5: 34, 6: 5, 7: 2, None: 3}

        #g = graph.GraphHistogram()
        #g.setData([(x, y) for x, y in sorted(results.items())])
        #g.process()

    def xtestEx04(self):
        # what

        scSrc = scale.MajorScale()

        niederlande = corpus.search('niederlande', field='locale')

        results = {}
        for unused_name, group in [('niederlande', niederlande)]:
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

        print ('Of %s works, the following major scale degrees are not used the following number of times:' % workCount)
        print (results)

        #Of 104 works, the following major scale degrees are not used the following number of times:
        #{4: 5, 5: 1, 6: 6, 7: 6}



if __name__ == "__main__":
    import music21
    import sys
    sys.argv.append('hi')

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)

    elif len(sys.argv) > 1:
        t = Test()
        #t.testEx02()
        #t.testEx03()
        #t.testEx04()

        t.testStreams01()
        #t.testStreams02()

        #t.testScales01()
        #t.testScalesPy06()


#------------------------------------------------------------------------------
# eof


