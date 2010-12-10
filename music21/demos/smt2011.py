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
        pass
    


    def testEx01(self):
        ''' Basic scale operations
        '''    
        # a simple major scale
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


    def testEx02(self): 
        # labeling a part based on scale degree

        s = corpus.parseWork('hwv56/movement3-03.md')#.measures(1,7)
        basso = s.parts['basso']
        s.remove(basso)

        ksScale = s.flat.getElementsByClass('KeySignature')[0].getScale()
        for n in basso.flat.getElementsByClass('Note'):
            n.addLyric(ksScale.getScaleDegreeFromPitch(n.pitch))

        display = stream.Score()
        display.insert(0, basso)
        display.insert(0, s.chordify())
        #display.show()

if __name__ == "__main__":
    import music21
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)

    elif len(sys.argv) > 1:
        t = Test()
#------------------------------------------------------------------------------
# eof

