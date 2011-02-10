# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         romanText/base.py
# Purpose:      test files for roman numeral text analysis
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''Objects for processing roman numeral analysis text files, as defined and demonstrated by Dmitri Tymoczko.
'''
import unittest
import music21







monteverdi_4_12 = """
Composer: Claudio Monteverdi
Madrigal: 4.12
Title: OhimË, se tanto amate
Time Signature: 4/4

m1 g: i
Note: all ii2 and V2/V chords in the piece are examples of the Artusi 9-7 leap controversy.
m2 b2 ii2 b3 V
m3 Bb: I
m4 b2 V2/V b3 V
m5 V
m6 c: viio6 b3 i
m7 b3 vi6 b4 ii2
m8 v F: ii
m9 viio6/5 b2 V6/4 b3 vi
m10 b3 IV b4 viio6/4
Note: III before I is common enough in the late Renaissance that I didnt bother to switch keys to avoid it
m11 III
m12 I b3 vi C: ii b4 viio6
m13 I ||
m14 F: IV b3 ii7 b4 ii
m15 I
Note: purpose of the bass G is unclear tonally.  Could be read as a passing tone to A with octave leap
m16 b2 ii11 b3 D: V9[no7]
m16var1 b3 d: V9[no7]
Note: LN + escape escape tones could allow a V13 analysis for b2...  b4 unclear tonally F-natural PT?
m17 V7 b4 iio6/5[no5]
m17var1 V7 b2 V13 b3 V7 iio6/5[no5]
m18 V
m19 I ||
m20 b2 i
m21 F: V b4 I
m22 b4 [[[[[[[start]]]]
"""


riemenschneider001 = """Composer: J. S. Bach
BWV: 269
Title: Aus meines Herzens Grunde

Analyst: Andrew Jones
Proofreader: Dmitri Tymoczko and Hamish Robb
Note: please email corrections to dmitri@princeton.edu



Time Signature: 3/4



Form: chorale

m0 b3 G: I

m1 b2 IV6 b3 V6

m2 I b2 V b3 vi

m3 IV b2.5 viio6 b3 I

m4 V || b3 I

m5 V6 b2 vi6/5 b3 viio6

m6 I6 b2 ii6/5 b3 V b3.5 V7
m7 I || b3 I

m8 I b2 ii b2.5 viio6 b3 I6

m9 I6 b2.5 V4/3 b3 I

m10 V || b3 vi
Note: consecutive first inversion triads

m11 vi b2 iii6 b3 ii6

m11var1 vi b2 I6/4 b3 ii6

m12 I6 b3 V7

m13 I b2 I6 b3 V7/IV

m14 IV || b3 I

m15 V6 b1.5 V6/5 b2 I b3 viio6

m16 I6 b2 I b3 V b3.5 V7

m17 vi b2 IV b3 I

m17var1 vi b2 IV b2.5 viio6/4 b3.5 I

m18 V || b3 I

m19 V6 b3 IV6

m20 vi b2 ii6/5 b3 V b3.5 V7

m21 I"""


swv23 = """Composer: Heinrich Schutz
Piece: Warum toben die Heiden, Psalmen Davids no. 2, SWV 23
Analyst: Saraswathi Shukla
Proofreader:
Time Signature: 2/2

m1 g: V b2 i
m2 = m1
m3 = m1
m4 = m1
m5 V
Note: key is uncertain in the following phrase
m6 Bb: iii
m7 I b2.5 V
m8 V/V b2.5 IV
m10 I
m11 V
m12 b2 V/V b2.5 iii d: i
m13 V b2.5 i
m14 V
m15 V ||
m16 Bb: V
m17 I b2.5 V
m18 ii g: iv b2.5 i
m19 V b1.5 i6/4 b2 V
m20 I ||
m21 Bb: I b2 vi
m22 b1.5 IV
m23 I b2 I6
m24 V
Note: ascending fifths sequence
m25 I
m26 V
m27 ii b2 ii6
m28 vi
m29 iii d: i
m30 V ||
m31 I
m32 i b2 VI F: IV
m33 V7 b1.5 I6/4 b2 V
Note: down-a-third, up-a-step sequence
m34 I b2 I b2.25 V/ii b2.5 bVII b2.75 V g: IV
m35 V b1.5 i6/4 b2 V
Note: down-a-third-up-a-step sequence
m36 I b2 III b2.25 i b2.5 ii b2.75 VII c: IV
m37 V b1.5 i6/4 b2 V ||
Time Signature: 3/2
Note: key is uncertain in the following passage
m38 I F: V b3 vi
m39 IV b3 I
Time Signature: 2/2
Note: descending-thirds pattern in what follows
m40 I b2 vi
m41 IV b2 ii
m42 vi d: i b2 V
m43 V b1.5 i b1.75 VII b2 III
m44 i b2 iv6 b2.5 iio6
m45 V b1.5 i6/4 b2 V ||
m46 I
m47 iv b1.5 V6/iv b2 iv b2.5 i
m48 V || b2.5 F: I
m49 b2.5 V6
m50 I b2 a: i6 b2.5 i
m51 V
Note: the next phrase outlines an ascending step sequence: d-Bb-[]-Eb-C-F-d
m52 I || b1.5 d: i
m53 VI b2.5 i
m54 bII b2.5 VII
m55 III b2 i b2.5 V6
m56 i
m57 V b2 i b2.5 iv6
m58 = m57
m59 = m57
Note: the next phrase is built on an ascending fifth sequence, F-C-g-D
m60 V || b2 g: VII
m61 IV b2.5 i
m62 V
m63 I ||
m64 b2 VII
m65 IV b2.5 i
m66 V
m67 i ||
m68 i b1.75 iv b2 V
m69 i b1.75 v b2 VI Bb: IV
m70 ii b1.5 I b2 V
m71 V b2 I
m72 V6 b2 I
m73 V
m74 I || b2 V d: III
m75 I b2 iv b2.5 I
m76 V b2 I || g: V
m77 i b1.5 VI b2 iv b2.5 iio6
m78 V b1.5 i6/4 b2 V
m79 I ||
Note: descending fifths root motion
m80 I b2 IV
m82 b1.5 VII
m83 III b2 v d: i
m84 V
m85 I || g: V 
m86 b2 i
m87 V6 b2 i b2.5 v b2.75 v6
m88 iv6
m89 V b1.5 i6/4 b2 V
m90 i || b2 V/V b2.5 V
Note: ascending 5-6 sequence
m91 V b1.5 III+6 b2 VI b2.5 iv6
m92 V || b1.5 F: IV
m93 I b1.5 V6 b2 IV6 b2.5 ii6
m94 V b1.5 I6/4 b3 V
m95 I ||
Time Signature: 3/2
m96 V b3 I
m97 = m96
m98 = m96
m99 V ||
Time Signature: 2/2
Note: ascending 5-6 sequence
m100 I
m101 IV
m102 b2 V/V g: I
m103 iv b2 i
m104 V b2 i6/4
m105 V
m106 I ||
m108 I
m110 IV
m111 VII
m112 v6 
m113 i b2 iv6 ||
Time Signature: 3/3
Note: harmony ambiguous on b2; could read IV6, with D as a suspension
m114 V b3 V6
Note: descending circle-of-fifths sequence
m115 I b3 I6
m116 IV b3 IV6
m117 VII b3 VII6
m118 III b3 III6
m119 VI b3 iv
m120 i b2 V
Time Signature: 2/2
m121 i || b2 III d: VI
m122 III b2 iv b2.5 i
m123 V b2 i ||
m124 III g: VII b2 iv
m125 V b1.5 iv6 b2 V
m126 I ||
m127 iv b2 VII
m128 III
m129 i b1.5 ii b2 i6 b2.5 IV
m130 V
m131 I || Bb: b2: vi
m132 ii b2 V
m133 I
Note: reading passing motion in the following measures, embellishing a single G minor chord.
m134 b2 g: i
m137 V b2 V6 b2.5 i
m138 V
m139 I"""






ALL  = [monteverdi_4_12, riemenschneider001, swv23]





#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
    




#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        t = Test()
        te = TestExternal()
        # arg[1] is test to launch
        if hasattr(t, sys.argv[1]): getattr(t, sys.argv[1])()

#------------------------------------------------------------------------------
# eof




