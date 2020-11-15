# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         romanText/base.py
# Purpose:      test files for roman numeral text analysis
#
# Authors:      Christopher Ariza
#
# Copyright:    Copyright © 2011 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Objects for processing roman numeral analysis text files,
as defined and demonstrated by Dmitri Tymoczko.
'''
import unittest

_DOC_IGNORE_MODULE_OR_PACKAGE = True


monteverdi_3_13 = """
Composer: Claudio Monteverdi
Madrigal: 3.13
Title: Ch'io non t'ami, cor mio
Time Signature: 4/4
Analyst: Michael Scott Cuthbert

m1 a: v b3 i b4 VI
m2 b2 III b4 iv
m3 i6/4 b3 V
m4 i b3 v b4 VI
m5 b2 g: IV b4 V
m6 i
m7 D: V
m8 I b3 IV
m9 bVII b3 a: i6
Note: m9 is a murky transition with voice-leading chords; next passage alternates between a minor and A major
m10 V
m11 i || b4 I
m13 b2 iv b3 III
m14 b2 III6 || b4 I
m16 b2 iv b3 G: IV
m17 || b4 vi
m19 b2 viio6 b3 I
m21 I6 b3 IV b4 ii6/5
m22 I
m23 b3 IV6/4
m24 I
m25 IV || b3 d: III b4 ii
m26 v b2 III6 b3 iv6 b4 ii/o6/5
m27 i6/4 b3 V
m28 I6 b3 IV
m29 VII6 b2 v b3 V b4 vi6
m30 V/V
m31 v b2 VII b3 III b4 ii
Note: mm31-37 are basically a repeat of mm25-31 but not coming out of a previous key, m31 is labeled differently
m32-33 = m26-27
m34 I b3 IV
m35-36 = m29-30
m37 v ||
m38 C: IV b4 I
Note: mm. 38 to 44 could also be labeled in F since IV plays such a prominent role
m39 b4 ii
m40 V/ii
m41 IV b4 I
m42 b4 ii
m43 V/ii
m44 V/V || b2 V[no3] b3 I
m46 b3 IV
m47 b3 V b4 vi
m48 V b3 I
m49-51 = m41-43
m52-54 = m38-40
m55-57 = m44-46
m58 b3 vi
m59 V
m60 I ||
m61 I b3 V
m62 a: i b2 V b4 VI
m63 V
m64 b2 i b3 VII
m65 b3 v
Note: mm 65-70 could be analyzed in G as well)
m66 ( VII
m67 b4 v7
m68 ii6 b4 VII6/4
m69 IV
m70 b3 iv )
m71 VI b3 v6
m72 i
m74 III b3 ii6
m75 V
m79 i ||
m80 VI b3 III
m81 d: i b2 V b4 VI
m82 V
m83 b2 i b3 C: I
m85 V b3 vi b4 V/vi
m86 b2 IV b3 V/vi
m87 b4 vi
m88 V
m90 b3 V6
m91 a: iio6[no5]
m92 IV
m93 i
m94 III b3 iio6
m95 V
m97 V6 b3 i
m98 iio6/5[no5] b3 viio6
m99 i
m99var1 i b3 ii4/2
Note: D as suspension in quintus resolves just as d as PT appears in soprano
m101 III b4 i6
m102 VII
m103 I
m107 V
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
m94 V b1.5 I6/4 b2 V
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
Time Signature: 3/4
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
m131 I || Bb: b2 vi
m132 ii b2 V
m133 I
Note: reading passing motion in the following measures, embellishing a single G minor chord.
m134 b2 g: i
m137 V b2 V6 b2.5 i
m138 V
m139 I
"""

mozartK279 = """Composer: Mozart
Piece: K279
Analyst: Dmitri Tymoczko
Proofreader: David Castro
Note: please email corrections to dmitri@princeton.edu

Movement: 1
Tempo: Allegro
Time Signature: 4/4

Form: exposition
m1 C: I
m2 ii6 b3.5 I6 b4 ii6 b4.5 V
m2var1 ii6 b2 V2 b3.5 I6 b4 ii6 b4.5 V
m3-4 = m1-2
m5 I b3 V6
m6 b3 I
m7 b2 V7/IV b3 IV6/4
m8 b3 I
m9 I6 b3 IV
m10 b1.5 I6/4 b2 V7 b3 viio7/vi b4 vi ||
m11 = m9
m12 b1.5 I6/4 b2 V7 b3 I b4 V7/IV
m13 b1.5 IV6/4 b2.5 viio6 b3 I b4 V7/IV
m14 b1.5 IV6/4 b2.5 viio6 b3 I6 b3.5 I6/4 b4 V7
m15 I6/4 b2 V7 b3 I6 b4.5 ii6
m16 I6/4 b1.5 V ||
Form: second theme
m17 G: V7/ii
m18 ii
m19 V7
m20 I b2 I6 b3 IV
m21 I6 b2 I b3 IV
m22 I6 b2.5 V6/5/ii b3 ii b4.5 V6/5
m23 I b2.5 IV6 b3 ii6 b4.5 V6/5/V
m24 V b2.5 V6/5/ii b3 V7/V b4.5 V6/5
m25 I b2.5 IV6 b3 ii6/5 b4 I6/4
m26 IV6 b2 I6/4 b3 ii6/5 b4 I6/4
m27 IV6 b2 I6 b3 ii6
m30 I6/4 b3 V7
m31 I b3 V6
m32 I b3 ii6 b4 V7
m33 I b3 V6/5
m34 I b3 ii6 b4 V7
m35 I
m36 ii b3 V7
m37 I
Form: development
m39 g: i
m40 V2/V d: V2
m41 i6 C: ii6
m42 V2
m43 I6
m44 a: N6
m45 V7 b3 i g: ii
m46 V7 b3 i F: ii
m47 V7 b3 I
m48 C: IV b3 I6
m49 V4/3 b3 I
m50 b3 V6
m51 V4/3/V b3 V
m52 V7 b3 I6/4
m53 b3 V
m54 V7 b3 I6/4
m55 I6/4 b3 V b4 I6/4
m56 V b2 I b3 V7
Form: recapitulation
m58-61 = m1-4
m62 I b3 V2/IV
m63 b3 IV6
m64 b3 viio4/3/ii
m65 b3 viio4/3
m66 I6 b2 i6 b3 V7/V b4 V6/5
m67 I b2 viio7/V b3 V7
m68 I6/4 b2.5 viio6/V b3 V7
m69 I6/4 b2.5 viio6/V b3 V
Form: second theme
m70 b3 V7/ii
m72 ii
m73 V7
m74 b3 I
m75 IV6/4 b3 I
m76 IV6/4 b3 I b4.5 V6/5/ii
m77 ii b2.5 V6/5 b3 I b4.5 IV6
m78 ii6 b2.5 V6/5/V b3 V b4 I6
m79 IV b3 I6 b4 I
m80 IV b3 I6 b4.5 V6/5/ii
m81 V7/V b2.5 V6/5 b3 I b4.5 IV6
m82 ii6 b3 iii6
m83 IV6 b3 V6
m84 V2 b3 I6 b4 V7
m85 I6/4 b2 V7 b3 I6 b4.5 ii6
m86 I6/4 b1.5 V || b3 ii6/5 b4 I6/4
m87 IV6 b2 I6/4 b3 ii6/5 b4 I6/4
m88 IV6 b2 I6/4 b3 ii6
m91 I6/4 b3 V7
m92 I b3 V6
m93 I b3 ii6 b4 V7
m94 I b3 V6
m95 I b3 ii6 b4 V7
m96 I
m97 ii b3 V7
m98 I

Movement: 2
Tempo: Andante
Time Signature: 3/4

Form: exposition
m1 F: I b2 V4/3 b3 I
m2 V6/5 b2 V7 b3 I
m3 ii6 b2 I6/4 b3 V7
m4 IV6 b2 V6/5 b3 I
m5 ii6 b2 I6/4 b3 V7
m6 I
m7 V
m8 I b2 V6/5/IV
m9 IV b3 V6/5/V
m10 V C: I
Form: second theme
m11 V4/3
m12 I6
m13 V6/5
m14 I
m15 V6/5/V b2 V b3.5 V2
m16 I6 b1.5 IV b2 I6/4 b3 V7
m17 I6
m18 viio7/V b2 V b3 vii/o7
m19 I b2 viio7/vi b3 vi
m20 ii6 b2 I6/4 b3 V7
m21 I b2 viio6 b3 I6
m22 ii6
m23 viio7/V
m24 I6/4
m25 V6/5 b2 I6/4 b3 V
m26 I b3 V7
m27 I b3 V7
m28 I
Form: development
m30 V6 d: IV6
m31 iv6
m32 i6/4 b2 V
m33 viio4/3 b2 i6 b3 i
m34 iio6 b2 i6/4 b3 V
m35 viio6/4 b2 i6 b3 i
m36 = m34
m37 viio6/5/iv
m38 iv6 F: ii6
m41 I6/4 b2 V7
Form: recapitulation
m43-45 = m1-3
m46 viio2 b2 V7 b3 viio2
m47 V7 b2 viio7/vi b3 vi
m48 V6/5/V
m49 V4/3/V
m49var1 viio6/V
m50 V
Form: second theme
m51 V4/3
m52 I6
m53 V6/5
m54 I
m55 V6/5/V b2 V b3.5 V2
m56 I6 b1.5 IV b2 I6/4 b3 V7
m57 I6
m58-61 = m18-21
m62-63 = m20-21
m64 ii6/5
m65 V6/5/V
m66 I6/4
m67 V6/5/V b2 V7
m68 I
m69 V
m70 I b2 V6/5/IV
m71 IV b2 I6/4 b3 V7
m72 I b3 V7
m73 = m72
m74 I

Movement: 3
Tempo: Allegro
Time Signature: 2/4

Form: exposition
m1 C: I
m2 V7
m3 I b2 ii6 b2.5 V6/5/V
m4 V
m5-6 = m1-2
m7 I b2 V6/5
m8 = m7
m9 I b1.5 I6 b2 ii6 b2.5 V
m10 I
m11 I
m12 V6 G: I6
m14 viio6
m15 V7
m16 IV6 b2 iii6
m17 ii6 b2.5 V6/5/V
m18 V b2 V2 b2.5 I6
m19 V6/4 b1.5 I b2 V6/5 b2.5 I
m20-21 = m18-19
m22 V
Form: second theme
m24 vi b2 viio6/V b2.5 V
m25 iii
m26 IV b2 ii6 b2.5 iii
m27 I
m28 ii b2 viio6 b2.5 I
m29 IV b2 viio/V
m30 V b2 i6/4
m31 V b2 i6/4
m32 V
m33 I
m34 IV6 b2 iii6 b2.5 ii6
m35 I6 b1.5 viio6 b2 vi6 b2.5 V6
m36 IV6 b1.5 iii6 b2 ii6 b2.5 I6
m37 ii6 b2 I6/4 b2.5 V
m38 I b2 IV6
m39 I6/4 b2 V2
m40 I6 b2 IV6
m41-42 = m39-40
m43 = m39
m44 I6 b2 ii6
m45 I6/4 b2 V7
m46 I
m47 viio6/V b2 viio b2.5 I
m48 ii6
m49 I6/4 b2 V
m50 I
m51-53 = m47-49
m54 I b2 V7
m55 = m54
m56 I
Form: development
m58 b2 vii/o7/V b2.5 V
m59 iii e: v
m60 i6 b2 viio7/V b2.5 v
m61 C: V6/5 b2 I
m62 vi a: i b2.5 V
m64 i b2 viio4/3/V b2.5 v6
m65 F: V
m66 I b2 vii/o4/3/V b2.5 V6
m67 iii d: v
m68 i b2 viio4/3/V b2.5 v6
m69 a: Ger6/5
m70 V
m71 Ger6/5
m72 V b1.5 i b2 V6 b2.5 i6/4
m73 V b1.5 i6/4 b2 V b2.5 i6/4
m74 V b1.5 i6/4 b2 V b2.5 i6/4
m75 V
m77 e: i
m78 V7
m79 i b1.5 d: ii/o7
m80 V2
m81 i6 b2.5 i
m82 V7
m83 i C: ii
m84 V2
m85 I6 b2.5 I
m86 V7
Form: recapitulation
m87-90 = m1-4
m91 I
m92 V2
m93 I6 b2 V2
m94 I6 b2 V6/5
m95 = m9
m96 I
m97 V7/IV
m98 IV6/4
m100 I
m101 I6
m102 ii6
m103 b2.5 V6/5/V
m104-131 = m18-45
m132 I b2 i6/4
m133 V b2 i6/4
Form: second theme
m134 V
m137 viio/V b2.5 V
m138 viio[b3]/iii b2.5 iii
m139 viio b2.5 I6/4
m141 vi6 b2 viio6/V b2.5 V6
m142 iii
m143 viio4/3/iii b2.5 iii6
m144 I
m145 ii6 b2 viio6/4 b2.5 I6
m146 ii6 b2 I6/4 b2.5 V
m147-156 = m46-55
m157 I b2 V7
m158 I
"""

mozartK283_2_opening = '''Composer: Mozart
Piece: K283
Analyst: Emilio Renard i Vallet
Proofreader: Dmitri Tymoczko and Thomas Robinson
Note: please email corrections to dmitri@princeton.edu

Form: exposition
m1 C: I b3 V4/3 b4 V6/5 b4.5 V7
m2 I b2 IV6 b2.5 IV b3 I6/4 b4 V b4.5 viio6/4
m3 I6 b3 V4/3 b4 V6/5 b4.5 V7
m4 I b1.5 ii6 b2 I6/4 b2.5 V7 b3 I
Form: transition
m5 I b2 V6 b3 I b4 I6 b4.5 I
m6 V6 G: I6 b1.5 viio6 b2 I6 b2.5 I b3 V6/4 b3.5 V6/5 b4 I
m7 ii6 b3 viio6
m8 I6 b2.5 ii6 b3 I6/4 b3.5 vii/o7/V b4 V
Form: second theme
m9 I b3 V4/3
m10 = m9
m11 I6 b2.5 V6/5/IV b3 IV
m12 I6 b1.5 ii6 b2 I6/4 b2.5 viio6/4 b3 I6 b4.5 V6/5/IV
m13 IV b3 I6 b3.5 IV b4 I6/4 b4.5 V
m14a I b1.5 V7 b2 I b2.5 V7 b3 I C: V b4 V9
m14b I b1.5 V7 b2 I b2.5 V7 b3 I b4 d: iio2
Note: m14 melodic texture, inferred harmony
Form: development
m15 viio7
m16 b3 i
m17 V4/3 b2 V6/5 b2.5 V7 b3 i b4 V6/5 b4.5 C: ii2
'''

testSecondaryInCopy = '''
Time Signature: 4/4
m1 g: i
m2 i6
m3 V7/v
m4-5 = m3-4
m6 d: i
m7-10 = m2-5
'''

testSetMinorRootParse = '''
Time Signature: 4/4
Minor Sixth: flat
Minor Seventh: sharp
m1 c: i b2 viio b3 i
m2 V b2 VI b3 V
m3 i b2 bVII b3 i
m4 V b2 #vi b3 V
'''


ALL = [monteverdi_3_13, riemenschneider001, swv23, mozartK279, testSetMinorRootParse]


# ------------------------------------------------------------------------------
class Test(unittest.TestCase):
    pass


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []


if __name__ == '__main__':
    # sys.arg test options will be used in mainTest()
    import music21
    music21.mainTest(Test)

