# -*- coding: utf-8 -*-

# pylint: disable=line-too-long

_DOC_IGNORE_MODULE_OR_PACKAGE = True

import re

splitLots = re.sub(r"\s\s\s\s+", "\t", 
r'''
**kern        **kern
*staff2       *staff1
*clefF4       *clefG2
*M2/4         *M2/4
=1            =1
2D            2e#
=2            =2
*^            *^
*     *       *     *^
2F    2G      2a#    2b#    2f#
=3    =3      =3    =3
*v    *v      *     *     *
*             *v    *v    *v
2A            4c#
.             4d#
=4            =4
*-            *-
''')


fakeTest = re.sub(r"\s\s\s\s+", "\t", 
r'''
!! Global Comment
!!!COM: Fake, Composer
!!!CDT: 1700-1990
!!!OTL: OjibwaySchubertMazurka
**kern    **lyrics      **kern     **kern     **dynam
!         ! In Ojibway  !          !          !
*staff3      *staff3       *staff2    *staff1    *staff1/2
*clefF4    *             *clefF4    *clefG2    *
*M3/4     *             *M3/4      *M3/4      *
*k[b-e-a-d-g-]    *     *k[b-e-a-d-g-]     *k[b-e-a-d-]     *
8.d-      Ma-           4r         4r         .
16d-      -gi-          .          .          .
=1        =1            =1         =1         =1
*         *             *^         *          *
! spine comment    .    .          .          .
8d-       -ja-          8A#/       4GG#^\ 4D#^\    4g#^/    p
16A-      -go          16B#/L      .               .        .
16A-      ic-          16c#/J      .               .        .
[4d-       -kew-         2B#        2r             2d#     f
4d-_       -yan          .          .                .      .
=2        =2            =2         =2              =2      =2
2d-]      .              4c#        4GG# 4D#        4g#    mp
*        *              *v         *v              *      *
.        .              4E-                        4r     pp
=3       =3             =3                         =3     =3
*-        *-            *-                         *-     *-
'''
)

strangeWTCOpening = re.sub(r"\s\s\s\s+", "\t", 
r'''
**kern
*k[]
*C:
*M4/4
*MM112
=1
*^
*^    *
8r    16r    2c\
.    [8.e\    .
16g/LL    .    .
16cc/JJ    .    .
16ee/LL    4e\]    .
16g/    .    .
16cc/    .    .
16ee/JJ    .    .
8r    16r    2c\
.    [8.e\    .
16g/LL    .    .
16cc/JJ    .    .
16ee/LL    4e\]    .
16g/    .    .
16cc/    .    .
16ee/JJ    .    .
=2    =2    =2
1cc;/ 1g/ 1e/    1C/    1CC;\
==|!    ==|!    ==|!
*-    *-    *-
'''
)

ojibway =  re.sub(r"\s\s\s\s+", "\t", \
r'''
!! Ojibway Indian Song
!! Transcribed by Frances Densmore
!! No. 84 "The Sioux Follow Me"
**kern    **lyrics
!         ! In Ojibway
*clefF4   *
*M3/4     *
*k[b-e-a-d-g-]    *
8.d-      Ma-
16d-      -gi-
=1        =1
8d-       -ja-
16A-      -go
16A-      ic-
4d-       -kew-
4d-       -yan
=2        =2
*-        *-
'''
)

# Tests the two kinds of flavors of JRP
dottedTuplet = re.sub(r'\s\s\s\s+', '\t', \
r'''
**kern
*M2/2
*d:
=1
6e
12.e
24d
12f
12f
4g
4d
=2
1d
*-
''')

splitSpines =  re.sub(r"\s\s\s\s+", "\t", \
r'''
**kern
*staff1
*clefG2
*M2/4
=1
4c
4c
=2
*^
4c    4a
4c    4a
==    ==
*-    *-
'''
)

splitSpines2 =  re.sub(r"\s\s\s\s+", "\t", \
r'''
**kern
*staff1
*clefG2
*M2/4
=1
4d
4d
=2
2d
=3
*^
4c    4a
4c    4a
=4    =4
2c    2a
=5    =5
*v    *v
4d
4d
=6
2d
==
*-
'''
)


  
schubert = re.sub(r"\s\s\s\s", "\t", \
r'''
!!!COM: Schubert, Franz Peter
!!!CDT: 1797-1828
!!!OTL: Heidenroeslein
!!!OPS: Opus 3
!!!ONM: No. 3
!!!SCT: DV 257
!!!YOR: Franz Schubert: Selected songs
!!!PPE: Max Friedlaender
!!!PSR: C.F. Peters 
!!!PSP: Frankfurt, London, New York
!!!PSD: n.d.
!!!PPG: pp.73-74
!!!ODT: 1815///
!!!ONB: Leading and trailing bars of rest have been deleted.
**kern
*M2/4
*MM[Lieblich]
*G:
*k[f#]
=1
8b
8b
8b
8b
=2
(16dd
16cc)
(16cc
16b)
4a
=3
8a
8a
8b
8cc
=4
4dd
8gg
8r
=5
8b
8b
8b
8b
=6
(16dd
16cc#)
(16cc#
16b)
4a
=7
8dd
8dd
8.ee
16dd
=8
(16cc#
16dd)
(16ee
16ff#)
4dd
=9
(16dd
16ff#)
(16ee
16dd)
(16cc#
16b)
(16a#
16b)
=10
(8.gg
16cc#)
4dd;
=11
8a
8a
8b
8ccn
=12
8dd
(16ee
16ff#)
4gg;
=13
8ee
8gg
8cc
8ee
=14
(8g
16b
16a)
4g
=15
2r
=16
2r
=17
8b
8b
8b
8b
=18
(16dd
16cc)
(16cc
16b)
4a
=19
8a
8a
8b
8cc
=20
4dd
8gg
8r
=21
8b
8b
8b
8b
=22
(16dd
16cc#)
(16cc#
16b)
4a
=23
8dd
8dd
8.ee
16dd
=24
(16cc#
16dd)
(16ee
16ff#)
4dd
=25
(16dd
16ff#)
(16ee
16dd)
(16cc#
16b)
(16a#
16b)
=26
(8.gg
16cc#)
4dd;
=27
8a
8a
8b
8ccn
=28
8dd
(16ee
16ff#)
4gg;
=29
8ee
8gg
8cc
8ee
=30
(8g
16b
16a)
4g
=31
2r
=32
2r
=33
8b
8b
8b
8b
=34
(16dd
16cc)
(16cc
16b)
4a
=35
8a
8a
8b
8cc
=36
4dd
8gg
8r
=37
8b
8b
8b
8b
=38
(16dd
16cc#)
(16cc#
16b)
4a
=39
8dd
8dd
8.ee
16dd
=40
(16cc#
16dd)
(16ee
16ff#)
4dd
=41
(16dd
16ff#)
(16ee
16dd)
(16cc#
16b)
(16a#
16b)
=42
(8.gg
16cc#)
4dd;
=43
8a
8a
8b
8ccn
=44
8dd
(16ee
16ff#)
4gg;
=45
8ee
8gg
8cc
8ee
=46
(8g
16b
16a)
4g
==
*-
!!!ENC: David Huron
!!!EMD: Paul von Hippel updated this file in the following ways (1998/9/2,21-22/):
!!!EMD:  (1) changed the representation of slurs from curly braces to parentheses 
!!!EMD:  (2) changed freeform comments into reference records and tandem interpretations
!!!EMD:  (3) changed final barline from quadruple (====) to double (==)
!!!EMD:  (4) added key signatures, key designations, and tempi
!!!EEV: Version 2.0
'''
)
    
    
mazurka6 = re.sub(r"\s\s\s\s", "\t", \
r'''
!!!COM: Chopin, Frederic
!!!CDT: 1810///-1849///
!!!OTL: Mazurka in C-sharp Minor, Op. 6, No. 2
!!!OPS: Op. 6
!!!ONM: No. 2
!!!ODT: 1830///-1832///
!!!PDT: 1832///-1833///
!!!PPP: Leipzig (1832); Paris (1833) and London
!!!ODE: Pauline Plater
!!!AIN: piano
**kern    **kern    **dynam
*staff2    *staff1    *staff1/2
*Ipiano    *Ipiano    *Ipiano
*>[I,A,A,B,B,C]    *>[I,A,A,B,B,C]    *>[I,A,A,B,B,C]
*>norep[I,A,B,C]    *>norep[I,A,B,C]    *>norep[I,A,B,C]
*>I    *>I    *>I
*clefF4    *clefG2    *clefG2
*k[f#c#g#d#]    *k[f#c#g#d#]    *k[f#c#g#d#]
*c#:    *c#:    *c#:
*M3/4    *M3/4    *M3/4
*MM64    *MM64    *MM64
=1-    =1-    =1-
*^    *    *
4B#/    4GG#\ 4D#\    4g#/    p
4A#/    2GG#^\ 2D#^\    2g#^/    .
8B#/L    .    .    .
8c#/J    .    .    .
*v    *v    *    *
=2    =2    =2
*    *^    *
4GG#\ 4D#\    4g#/    8d#\L    .
.    .    8B#\J    .
2GG#^\ 2D#^\    2g#^/    4.c#^\    .
.    .    8A#/    .
*    *v    *v    *
=3    =3    =3
*^    *    *
12B#/L    4GG#\ 4D#\    4g#/    .
12c#/    .    .    .
12B#/J    .    .    .
4A#/    2GG#^\ 2D#^\    2g#^/    .
8B#/L    .    .    .
8c#/J    .    .    .
*v    *v    *    *
=4    =4    =4
*    *^    *
4GG#/ 4D#/    4g#/    12d#\L    .
.    .    12f#\    .
.    .    12e\J    .
2GG#^/ 2D#^/    2g#/    2d#^\    .
*    *v    *v    *
=5    =5    =5
*^    *    *
12B#/L    4GG#\ 4D#\    4g#^/    .
12c#/    .    .    .
12B#/J    .    .    .
4A#/    4GG#\ 4D#\    4g#^/    .
8B#/L    4GG#\ 4D#\    4g#^/    .
8c#/J    .    .    .
*v    *v    *    *
=6    =6    =6
*    *^    *
4GG#\ 4D#\    4g#/    8d#\L    .
.    .    8B#\    .
4GG#\ 4D#\    4g#/    8c#^\    .
.    .    8B#\    .
4GG#\ 4D#\    4g#/    8c#^\    .
.    .    8A#\J    .
*    *v    *v    *
=7    =7    =7
*^    *    *
12B#/L    4GG#\ 4D#\    4g#^/    .
12c#/    .    .    .
12B#/J    .    .    .
4A#/    4GG#\ 4D#\    4g#/    .
4r    4GG#\ 4D#\    8B#'/ 8g#'/L    .
.    .    8c#'/ 8g#'/J    .
*v    *v    *    *
=8    =8    =8
4GG#/ 4D#/    (12d#'/ 12g#'/L    .
.    12f#'/ 12g#'/    .
.    12e'/) 12g#'/J    .
4GG#/ 4D#/    4d#/ 4g#/    .
=!|:    =!|:    =!|:
*>A    *>A    *>A
4r    (4g#^/    .
=9    =9    =9
4BB#/    8gg#\L)    .
.    16r    .
.    (16aa\Jk    .
4G#\ 4d#\ 4f#\    4.ff#\    .
4G#\ 4d#\ 4f#\    .    .
.    8gg#\    .
=10    =10    =10
4C#/    8.ee\L    .
.    16gg#\Jk    .
4G#\ 4c#\ 4e\    4cc#\    .
4G#\ 4c#\ 4e\    4ee\    .
=11    =11    =11
4BB#/    8.gg#\L)    .
.    (16aa\Jk    .
4G#\ 4d#\ 4f#\    4ff#\)    .
4G#\ 4d#\ 4f#\    4gg#\    .
=12    =12    =12
4C#/    (12ee\L    .
.    12ff#\    .
.    12gg#\J)    .
4G#^\ 4c#^\ 4e^\    4.cc#\    .
4r    .    .
.    (8cc##\    .
=13    =13    =13
4FF##/    8dd#'\L)    .
.    16r    .
.    (16ee\Jk    <
4D#\ 4A#\ 4c#\    4.cc#\    .
4D#\ 4A#\ 4c#\    .    .
.    8dd#\    .
=14    =14    =14
4GG#/    8.b#\L    .
.    16dd#\Jk    .
4D#\ 4F#\ 4B#\    4g#/)    .
4D#\ 4F#\ 4B#\    (4a/    f
=15    =15    =15
4GG#/    8g#'/L)    .
.    16r    .
.    (16f#/Jk    .
4D#\ 4F#\ 4B#\    4d#/)    .
4D#\ 4F#\ 4B#\    4g#/    .
=16    =16    =16
4CC#/    2c#^/    .
4C#\ 4G#\ 4e\    .    .
=:|!|:    =:|!|:    =:|!|:
*>B    *>B    *>B
4r    (4c##/    .
=17    =17    =17
4GG#/    8d#/L)    .
.    16r    .
.    (16f##/Jk    .
4D#\ 4G#\ 4B#\    4g#/    .
4D#\ 4G#\ 4B#\    8b#\L    .
.    8dd#\J)    .
=18    =18    =18
4GG#/    8d#'/L    .
.    16r    .
.    (16f##/Jk    .
4D#\ 4G#\ 4B#\    8g#/L    .
.    8b#/J    .
4D#\ 4G#\ 4B#\    4dd#^\)    .
=19    =19    =19
*^    *    *
2A#/    4E\ (4G#\    8.cc##^\L    .
.    .    (16a#\Jk    .
.    4D#\ 4F##\    4cc#'\)    .
4r    4GG#''\ 4G#''\)    (8b#/L    .
.    .    8g#/J)    .
=20    =20    =20    =20
(2A#/    4E\ 4G#\    (12cc##^\L    .
.    .    12a#\    .
.    .    12b#\J)    .
.    4D#\ 4F##\    4cc#\    .
4r    4GG#'\ 4G#'\)    (8b#/L    .
.    .    8g#/J)    .
*v    *v    *    *
=21    =21    =21
4GGG#/ 4GG#/    8d#/L    .
.    16r    .
.    16f##/Jk    <
4D#\ 4G#\ 4B#\    (4g#/    .
4D#\ 4G#\ 4B#\    8b#\L    .
.    8dd#\J)    .
=22    =22    =22
4GG#'/    8d#/L    .
.    16r    .
.    (16f##/Jk    .
4D#\ 4G#\ 4B#\    8g#/L    .
.    8b#/J    .
4D#\ 4G#\ 4B#\    4dd#^\)    .
=23    =23    =23
*^    *    *
2A#^/    4E\ 4G#\    (8cc##\L    .
.    .    8a#\J    .
.    4D#\ 4F##\    4cc#\    .
4r    4GG#''\ &(4G#''\&)    8b#/L)    .
.    .    (8g#/J    .
*v    *v    *    *
=24    =24    =24
2.r    8.gg#\L)    .
.    (16g#\k    .
.    8.gg#\)    .
.    (16g#\k    .
.    8.gg#\)    .
.    (16g#\Jk    .
=25    =25    =25
4BB#/    8.gg#\L)    .
.    (16aa\Jk    .
4G#\ 4d#\ 4f#\    4.ff#\    .
4G#\ 4d#\ 4f#\    .    .
.    8gg#\    .
=26    =26    =26
4C#/    8.ee\L    .
.    16gg#\Jk    .
4G#\ 4c#\ 4e\    4cc#\    .
4G#\ 4c#\ 4e\    4ee\    .
=27    =27    =27
4BB#/    8gg#''\L)    .
.    16r    .
.    (16aa\Jk    .
4G#\ 4d#\ 4f#\    4ff#\)    .
4G#\ 4d#\ 4f#\    4gg#^\    .
=28    =28    =28
4C#/    (12ee\L    .
.    12ff#\    .
.    12gg#\J)    .
4G#^\ 4c#^\ 4e^\    4.cc#^\    .
4r    .    .
.    8cc##\    .
=29    =29    =29
*^    *    *
4r    2.FF##\    8dd#^\L    f
.    .    8ee^\J    .
4D#/ 4A#/    .    4cc#^\    .
4D#/ 4A#/    .    4dd#^\    .
*v    *v    *    *
=30    =30    =30
4GG#/    8b#^\L    .
.    8dd#^\J    .
4D#\ 4F#\ &(4B#\&)    8g#^/    .
.    8r    .
4r    (4an^/    .
=31    =31    =31
4GG#/    8g#''/L)    .
.    16r    .
.    (16f#/Jk    .
4D#\ 4F#\ 4B#\    4d#/)    .
4D#\ 4F#\ 4B#\    4g#/    .
=32    =32    =32
4CC#/    2c#/    .
4C#\ 4G#\ 4e\    .    .
=:|!    =:|!    =:|!
*>C    *>C    *>C
4r    (4c#/    p
=33    =33    =33
4AA/    8cc#\L    .
.    8dd#\J    .
4E\ 4c#\    4.ee\    .
4E\ 4c#\    .    .
.    8cc#\)    .
=34    =34    =34
4EE/    (8b/L    .
.    8g#/J    .
4E\ 4B\    2e/)    .
4E\ 4B\    .    .
=35    =35    =35
4AA/    (8cc#\L    <
.    8dd#\J    .
4E\ 4c#\    4ee'\)    .
4E\ 4c#\    (8ee\L    .
.    8cc#\J    .
=36    =36    =36
4EE/    8b/L    .
.    8g#/J)    .
4E\ 4B\    [2e^/    .
4E\ 4B\    .    .
=37    =37    =37
*    *^    *
(4AA/ 4E/    (8e/L]    4c#\    p
.    8a/J    .    .
4EE'/ 4E'/    2g#/)    4B\    .
4EE'/) 4E'/    .    4B\    .
=38    =38    =38    =38
(4AA/ 4E/    (8e/L    4c#\    .
.    8a/J    .    .
4EE'/ 4E'/    2g#/)    4B\    .
4EE'/) 4E'/    .    4B\    .
=39    =39    =39    =39
(4AA/ 4E/    (8e/L    4c#^\    .
.    8a/J    .    .
4EE'/ 4E'/    4g#/    4B\    .
4EE'/) 4E'/    4g#/)    4B\    .
=40    =40    =40    =40
*^    *    *    *
4E/    8.AA\L    8e/L    4c#\    .
.    .    8a/J    .    .
.    16BB\Jk    .    .    .
4C#^/    4r    4G#/ 4g#/    4r    f
4CC#/    4r    4r    4r    .
*v    *v    *    *    *
*    *v    *v    *
=41    =41    =41
4r    (8ee#\L    f
.    8ff##\J    .
4E#\ 4G#\ 4c#\ 4e#\    4.gg#^\    .
4E#\ 4G#\ 4c#\ 4e#\    .    .
.    8ee#\)    .
=42    =42    =42
4GG#/    (8dd#\L    .
.    8b#\J)    .
4D#\ 4G#\ 4B#\    2g#^/    .
4D#\ 4G#\ 4B#\    .    .
=43    =43    =43
4C#/    (8ee#\L    .
.    8ff##\J    .
4E#\ 4G#\ 4c#\ 4e#\    4gg#\)    .
4E#\ 4G#\ 4c#\ 4e#\    (8gg#\L    .
.    8ee#\J)    .
=44    =44    =44
4GG#/    (8dd#\L    .
.    8b#\J    .
4D#\ 4G#\ 4B#\    [2g#^/)    .
4D#\ 4G#\ 4B#\    .    .
=45    =45    =45
*    *^    *
4C#\ 4G#\ 4c#\    (8g#/L]    4e#\    .
.    8cc#/J    .    .
(4GG#'/ 4G#'/    2b#^/)    4d#\    .
4GG#'/) 4G#'/    .    4d#\    .
=46    =46    =46    =46
4C#\ 4G#\    (8g#/L    4e#\    .
.    8cc#/J    .    .
(4GG#/ 4G#/    2b#/)    4d#\    .
4GG#/ 4G#/    .    4d#'\    .
=47    =47    =47    =47
4C#\) 4G#\    8g#/L    4e#^\    .
.    8cc#/J    .    .
4GG#/ 4G#/    4b#'/    4d#\    .
4GG#/ 4G#/    4b#'/    4d#\    .
=48    =48    =48    =48
4C#\ 4G#\    (8g#/L    4e#^\    .
.    8cc#/J    .    .
4GG#/ 4G#/    4b#/)    4d#\    .
4GG#/ 4G#/    4r    8d#\L    .
.    .    8c#\J    .
*    *v    *v    *
=49    =49    =49
*^    *    *
4B#/    4GG#\ 4D#\    4g#/    .
4A#/    2GG#^\ 2D#^\    2g#^/    .
(8B#/L    .    .    .
8c#/J)    .    .    .
*v    *v    *    *
=50    =50    =50
*    *^    *
4GG#\ 4D#\    4g#/    8d#\L    .
.    .    8B#\J    .
2GG#^\ 2D#^\    2g#^/    4.c#\    .
.    .    8A#/    .
*    *v    *v    *
=51    =51    =51
*^    *    *
(12B#/L    4GG#\ 4D#\    4g#/    pp
12c#/    .    .    .
12B#/J    .    .    .
4A#/    2GG#^\ 2D#^\    2g#^/    .
8B#/L    .    .    .
8c#/J)    .    .    .
*v    *v    *    *
=52    =52    =52
*    *^    *
4GG#/ 4D#/    4g#/    (12d#\L    .
.    .    12f#\    .
.    .    12e\J)    .
2GG#^/ 2D#^/    2g#^/    2d#^\    .
*    *v    *v    *
=53    =53    =53
*^    *    *
12B#/L    4GG#\ 4D#\    4g#^/    .
12c#/    .    .    .
12B#/J    .    .    .
4A#/    4GG#\ 4D#\    4g#^/    .
8B#/L    4GG#\ 4D#\    4g#^/    .
8c#/J    .    .    .
*v    *v    *    *
=54    =54    =54
*    *^    *
4GG#\ 4D#\    4g#^/    8d#\L    .
.    .    8B#\    .
4GG#\ 4D#\    4g#/    8c#^\    .
.    .    8B#\    .
4GG#\ 4D#\    4g#^/    8c#\    .
.    .    8A#\J    .
*    *v    *v    *
=55    =55    =55
*^    *    *
12B#/L    4GG#\ 4D#\    4g#/    .
12c#/    .    .    .
12B#/J    .    .    .
4A#/    4GG#\ 4D#\    4g#/    .
4r    4GG#\ 4D#\    8B#'/ 8g#'/L    .
.    .    8c#'/ 8g#'/J    .
*v    *v    *    *
=56    =56    =56
4GG#/ 4D#/    (12d#'/ 12g#'/L    .
.    12f#'/ 12g#'/    .
.    12e'/) 12g#'/J    .
4GG#/ 4D#/    4d#/ 4g#/    .
4r    (4g#^/    .
=57    =57    =57
4BB#/    8gg#\L)    p
.    16r    .
.    (16aa\Jk    .
4G#\ 4d#\ 4f#\    4.ff#\    .
4G#\ 4d#\ 4f#\    .    .
.    8gg#\)    .
=58    =58    =58
4C#/    8.ee\L    .
.    16gg#\Jk    .
4G#\ 4c#\ 4e\    4cc#\    .
4G#\ 4c#\ 4e\    4ee\    .
=59    =59    =59
4BB#/    8.gg#\L    .
.    (16aa\Jk    .
4G#\ 4d#\ 4f#\    4ff#\    .
4G#\ 4d#\ 4f#\    4gg#^\)    .
=60    =60    =60
4C#/    (12ee\L    .
.    12ff#\    .
.    12gg#\J)    .
4G#^\ 4c#^\ 4e^\    4.cc#\    .
4r    .    .
.    (8cc##\    .
=61    =61    =61
4FF##/    8dd#''\L)    .
.    16r    .
.    (16ee\Jk    .
4D#\ 4A#\ 4c#\    4.cc#\    .
4D#\ 4A#\ 4c#\    .    .
.    8dd#\    .
=62    =62    =62
4GG#/    8.b#\L    .
.    16dd#\Jk    .
4D#\ 4F#\ 4B#\    4g#/)    .
4D#\ 4F#\ 4B#\    (4an^/    .
=63    =63    =63
4GG#/    8g#/L)    .
.    16r    .
.    (16f#/Jk    .
4D#\ 4F#\ 4B#\    4d#/)    .
4D#\ 4F#\ 4B#\    4g#/    .
=64    =64    =64
4CC#/    2c#/    .
4C#\ 4G#\ 4e\    .    .
4r    (4g#/    p
=65    =65    =65
4BB#/    8gg#'\L    .
.    8aa'\J    .
4G#\ 4d#\ 4f#\    4ff#'\    .
4G#\ 4d#\ 4f#\    4gg#'\    .
=66    =66    =66
4C#/    8ee'\L    .
.    8gg#'\J    .
4G#\ 4c#\ 4e\    4cc#'\    .
4G#\ 4c#\ 4e\    4ee'\)    .
=67    =67    =67
4BB#/    12gg#\L    .
.    12aa\    .
.    24r    .
.    24gg#\Jk    .
4G#\ 4d#\ 4f#\    4dd#\    .
4G#\ 4d#\ 4f#\    4gg#^\    .
=68    =68    =68
4C#/    (12ee\L    .
.    12ff#\    .
.    12gg#\J)    .
4G#\ 4c#\ 4e\    4.cc#\    .
4r    .    .
.    8cc##\    .
=69    =69    =69
4FF##/    8dd#'\L    f
.    16r    .
.    16ee'\Jk    .
4D#\ 4A#\ 4c#\    4cc#'\    .
4D#\ 4A#\ 4c#\    4dd#'\    .
=70    =70    =70
(4GG#/    8b#'\L    .
.    16r    .
.    16dd#'\Jk    .
4D#\ 4F#\ 4B#\)    4g#/    .
4r    4an/    .
=71    =71    =71
4GG#/    8g#/L    .
.    16r    .
.    (16f#/Jk    .
4D#\ 4F#\ 4B#\    4d#/)    .
4D#\ 4F#\ 4B#\    4g#/    .
=72    =72    =72
4CC#/    2.c#^;/    .
4C#\ 4G#\ 4e\    .    .
4r;    .    .
==    ==    ==
*-    *-    *-
!!!ENC: Craig Stuart Sapp
!!!END: 2005/01/05/
!!!URL: http://www.chopinsociety.org/maz_rf.htm#maz62 (short description by David Dubal)
!!!URL: http://chopin.lib.uchicago.edu/gsdl/cgi-bin/library?e=d-000-00---0chopin--00-0-0-0prompt-10---4---Document-dtt--0-1l--1-en-Zz-1---50-home-mazurka--001-001-0-0utfZz-8-0&a=d&c=chopin&cl=CL3.10.5 (Early editions of op. 6 at the University of Chicago)
'''\
)

ivesSpring = re.sub(r"\s\s\s\s", "\t", \
r'''
!!!COM: Ives, Charles
!!!CDT: 1874/10/20/-1954/05/19/
!!!OTL: Spring Song
!!!GNM: 65/114
!!!ODT: 1904///
!!!PDT: 1922///
!!!OPR: 114 Songs
!!!OMD: Allegretto
**kern    **kern    **dynam    **kern    **dynam    **text
*staff3    *staff2    *staff2/3    *staff1    *staff1    *staff1
*Ipiano    *Ipiano    *Ipiano    *Ivox    *Ivox    *Ivox
*clefF4    *clefG2    *clefG2    *clefG2    *clefG2    *
*k[b-]    *k[b-]    *k[b-]    *k[b-]    *k[b-]    *
*F:    *F:    *F:    *F:    *F:    *F:
*M3/4    *M3/4    *M3/4    *M3/4    *M3/4    *
*MM92    *MM92    *MM92    *MM92    *MM92    *MM92
8r    8f'/ 8a'/ (8cc'/L    mf    8r    .    .
4c\    8f/ 8a/ 8cc/    .    4r    .    .
.    8f/ 8g#/ 8bn/ 8cc#/J    .    .    .    .
=1    =1    =1    =1    =1    =1
8.C\L    8.e/ 8.b-/ &(8.dd/L&))    <    2.r    .    .
16c#\Jk    (16cc#/Jk    .    .    .    .
8d\L    8dd\L    <    .    .    .
8G\ 8e\J    8ee\ 8bb-\J    .    .    .    .
4A\ 4g\    8.cc#\ 8.aa\L    <    .    .    .
.    16gg\Jk    .    .    .    .
=2    =2    =2    =2    =2    =2
*^    *^    *    *    *    *
2B-\ 2f\    4r    4.gg/    2b-\ 2dd\    >    2.r    .    .
.    4BB-\    .    .    .    .    .    .
.    .    8ff/)    .    .    .    .    .
4BBn\ 4Bn\    4r    (8.ee/L    4f\ 4g#\    .    .    .    .
.    .    16dd/Jk    .    .    .    .    .
=3    =3    =3    =3    =3    =3    =3    =3
4r    8C'\ &(8c'\L&)    8cc/L)    8f\ 8a\    .    2.r    .    .
.    8AA\ ([8G\J    (8c#/    8r    .    .    .    .
8G/L]    4BB-\    8e/    4r    .    .    .    .
8F/J    .    8d/J    .    .    .    .    .
4r    &((4C\&) 4B-\)    8.gn;/L    4e\    .    .    .    .
.    .    16a/Jk)    .    .    .    .    .
*v    *v    *    *    *    *    *    *
*    *v    *v    *    *    *    *
=4    =4    =4    =4    =4    =4
2FF/) 2A/    8f'/L    .    4r    .    .
.    8f'/ 8a'/ 8ccn'/    .    .    .    .
.    8f'/ 8a'/ 8cc'/    .    8r    .    .
.    8f'/ 8a'/ 8cc'/    .    (8cc\    mf    A-
4c\    8f'/ 8a'/ 8cc'/    .    8cc\    .    -cross
.    8f'/ 8g#'/ 8bn'/ &(8cc#'/J&)    .    8bn\    .    the
=5    =5    =5    =5    =5    =5
*^    *    *    *    *    *
4C/    2C\    8e/ 8b-/ 8dd/    .    4.b-\    .    hill
.    .    8dd\ 8ee\ (8bb-\    .    .    .    .
4G/ 4e/    .    8ccn\ 8ee\ 8aa\L    .    .    .    .
.    .    [8b-\ [8ee\ [8gg\J    .    8g/    .    of
4r    &(4C\&)    8b-\] 8ee\] 8gg\L])    >    8.d/    .    late,
.    .    [8d\ [8gn\ [8b-\ ([8dd\J    .    .    .    .
.    .    .    .    16e/    .    came
=6    =6    =6    =6    =6    =6    =6
(4FF/    2FF\    8d/] 8g/] 8b-/] 8dd/L]    .    4d/    .    spring
.    .    8d/ 8g/ 8b-/ 8ee/J    .    .    .    .
8F/)    .    8c'/ 8f'/ 8a'/ 8cc'/)    .    8c/)    .    .
8A'/L    .    8f'\ 8cc'\ (8ff'\L    .    (8a/    .    and
8G#'/    4r    8f'\ 8bn'\ 8ff'\    .    8.g#/    .    stopped
8A'/J    .    8f'\ 8cc'\ 8ff'\J)    .    .    .    .
.    .    .    .    16a/    .    and
=7    =7    =7    =7    =7    =7    =7
[4D/    4D\    8r    .    4.cc\    .    looked
.    .    8ff#\ 8cccn\ (8eee-\L    .    .    .    .
4f#/    4D\] (4A\    8ff#\ 8cccn\ 8dddn\    .    .    .    .
.    .    8ee-\ 8aa\ 8ccc\    .    8ee-\    .    in-
4r    4D\)    8dd\ 8gg\ 8bb-\    .    8dd\    .    -to
.    .    8cc\ 8ff#\ 8aa\J)    .    8cc\    .    this
=8    =8    =8    =8    =8    =8    =8
4G/    [2GG\    8r    .    8.b-\    .    wood
.    .    8cc\ 8ee-\ (8ff#\L    .    .    .    .
.    .    .    .    16a/    .    and
(8d/L    .    8b-\ 8dd\ 8ggn\    .    4g/)    <    called
8e-/J    .    8aa\ 8ccc\    .    .    .    .
&(8G/&) 8d/)    4GG\] 4G\    8gg\ 8bb-\    .    8r    .    .
8r    .    8b-\ 8gg\J)    .    (8dd\    .    and
=9    =9    =9    =9    =9    =9    =9
*    *    *^    *    *    *    *
4r    [4BB-\ [4F\    2r    8.r    .    [2ff\    .    called
.    .    .    16b-'^\ 16dd'^\ (16ffn'^\LK    f    .    .    .
4f/    4BB-\] 4F\] [4B-\    .    8dd'^\ 8ff'^\ 8bb-'^\    .    .    .    .
.    .    .    8b-'^\ 8dd'^\ 8ff'^\J)    .    .    .    .
4r    4B-\]    4ff/ 4bb-/    8g\ 8dd\L    .    8ff\])    .    .
.    .    .    8g#\J    .    (8dd\    .    and
=10    =10    =10    =10    =10    =10    =10    =10
4r    [4FF/ [4C/    2r    8.r    .    2cc\)    .    called.
.    .    .    16cc'\ 16ff'\ (16aa'\LK    .    .    .    .
8c/L    4FF\] 4C\] 4F\    .    8ff'\ 8aa'\ 8ccc'\    .    .    .    .
8d/J    .    .    8cc'\ 8ff'\ 8aa'\J)    .    .    .    .
4F#/ &(4e-/&)    4r    (8.bbn/L    4cc\ 4ee-\ 4ff#\    .    4r    .    .
.    .    16aa/Jk    .    .    .    .    .
=11    =11    =11    =11    =11    =11    =11    =11
8en/L    &(8G'\L&)    8cc'\ 8een'\ 8gg'\)    2r    .    2.r    .    .
8Bn/ 8d/    8E\    8f/ (8g#/L    .    .    .    .    .
8d/    8Fn\    8f/ 8bn/    .    .    .    .    .
8c/J    8F\J    8f/ 8a/    .    .    .    .    .
4G/    4G\    8.dd/    4f\ 4b\    .    .    .    .
.    .    16ee/Jk)    .    .    .    .    .
=12    =12    =12    =12    =12    =12    =12    =12
(4A-/    2.C\    (8.dd/L    4f\ 4bn\    .    4r    .    .
.    .    16ee/Jk)    .    .    .    .    .
[4G/)    .    (8e'/ 8g'/ 8cc'/L    2r    p    4r    .    .
.    .    8e'/ 8g'/ 8cc'/    .    .    .    .    .
8G/]    .    8e'/ 8g'/ 8cc'/    .    .    4c/    .    Now
8r    .    8e'/) 8g'/ 8cc'/J    .    .    .    .    .
*v    *v    *    *    *    *    *    *
*    *v    *v    *    *    *    *
=13    =13    =13    =13    =13    =13
(4C/    8ee-\ 8gg\ 8ccc\L    .    (8.e-/    .    all
.    8ee-\ 8gg\ 8ccc\J    .    .    .    .
.    .    .    16e-/    .    the
4D\    8dd\ 8ff#\ 8bb-\L    .    8d/    .    dry
.    8dd\ 8ff#\ 8bb-\J    .    8f#/    .    brown
4G\    8dd-\ 8ffn\ 8bb-\L    .    8.b-\    .    things
.    8dd-\ 8ff\ 8bb-\J    .    .    .    .
.    .    .    16a/    .    are
=14    =14    =14    =14    =14    =14
4C/    8cc\ 8een\ 8aa\L    .    4a/    .    ans-
.    8cc\ 8ee\ 8aa\J    .    .    .    .
4c\    8b-\ 8ee\ 8gg\L    <    4.g/)    .    -'wring
.    8b-\ 8ee\ 8gg\J    .    .    .    .
4c#\    8b-\ 8ee\ 8gg\L    .    .    .    .
.    8b-\ 8ee\ 8gg\J    .    8g/    .    With
=15    =15    =15    =15    =15    =15
4d\)    8a\ 8dd\ 8ff\L    .    (8.g/    .    here
.    8a\ 8dd\ 8ff\J    .    .    .    .
.    .    .    16f/    .    a
[4F\    8a\ 8dd\ 8ff\L    .    8f/)    .    leaf
.    8a\ 8dd\ 8ff\J    .    (8a/    .    and
4FF/ 4F/]    8f\ 8cc\ 8ee-\L    .    8.dd\    .    there
.    8f\ 8cc\ 8ee-\J    .    .    .    .
.    .    .    16cc\    <    a
=16    =16    =16    =16    =16    =16
4BB-/    8f\ 8cc\ 8ee-\L    .    8cc\    .    fair
.    8f\ 8cc\ 8ee-\J    .    8b-\    .    brown
4BB-^\ 4B-^\    8f/ 8b-/ 8dd/L    .    (2b-\)    <    flow'r,
.    8f/ 8b-/ 8dd/J    .    .    .    .
4AA^\ 4A^\    8d/ 8f/ 8b-/ 8dd/L    .    .    .    .
.    8d/ 8f/ 8b-/ 8dd/J    .    .    .    .
!    !    !    !ddq/)    !.    !.
=17    =17    =17    =17    =17    =17
*^    *    *    *    *    *
2GG^/ 2G^/    4r    8g\ 8b-\ 8dd\ [8ff\L    .    (4ff\    .    I
.    .    8g\ 8b-\ 8ff\J]    .    .    .    .
*clefG2    *clefG2    *    *    *    *    *
.    [8B-/ 8d/ 8g/L    8b-\ 8dd\ [8ff\ [8gg\L    .    8gg\    .    on-
.    8B-/] 8d/ 8f/J    8b-\ 8dd\ 8ff\] 8gg\J]    .    8ff\    .    -ly
4r    [8Bn/ [8e/ [8g#/L    [8bn\ [8ee\ [8gg#\L    .    8.ee\    .    heard
.    8B/] 8d/ 8e/] 8g#/J]    8b\] 8dd\ 8ee\] 8gg#\J]    .    .    .    .
.    .    .    .    16dd\)    .    her
*v    *v    *    *    *    *    *
=18    =18    =18    =18    =18    =18
[2cn/ [2f/ [2a/    [2cc\ [2ff\ [2aa\    .    (4ff\    .    not,
.    .    .    4.cc\)    .    .
8c/] 8f/] 8a/]    8cc\] 8ff\] 8aa\]    .    .    .    .
8r;    8r;    .    (8a/    p    and
*clefF4    *    *    *    *    *
=19    =19    =19    =19    =19    =19
*^    *    *    *    *    *
8r    2.C\    8r    .    [2cc\    .    wait
[8G/    .    8d/ (8f/    pp    .    .    .
2G/]    .    8e/ 8g/L    .    .    .    .
.    .    8f/ 8a/J    .    .    .    .
.    .    &(4g/&) 4b-/)    .    8cc\])    .    .
.    .    .    .    (8g/    .    and
=20    =20    =20    =20    =20    =20    =20
8r    2.FF\    8r    .    [2cc\    .    wait.
[8C/    .    8e/ (8g/    <    .    .    .
2C/]    .    8f/ 8a/L    .    .    .    .
.    .    8g/ 8b-/J    >    .    .    .
.    .    &(4e-/&) 4a/ 4cc/)    .    8cc\])    .    .
.    .    .    .    8r    .    .
*v    *v    *    *    *    *    *
=21    =21    =21    =21    =21    =21
*M4/4    *M4/4    *M4/4    *M4/4    *M4/4    *
1BBB- 1FF    1d 1f 1b- 1dd    ppp    1r    .    .
==    ==    ==    ==    ==    ==
*-    *-    *-    *-    *-    *-
!!!ENC: Craig Stuart Sapp
!!!END: 2008/07/25/
'''
)                    

sousaStars = re.sub(r"\s\s\s\s","\t",
r'''
!!!COM: Sousa, John Phillip
!!!CDT: 1854/11/05/-1932/04/08/
!!!OTL: Stars and Strips Forever March
!!!ODT: 1897///
!!!WIK: http://en.wikipedia.org/wiki/Stars_and_stripes_forever
!!!ONB: Arrangement for keyboard
**kern    **kern    **dynam
*staff2    *staff1    *staff1/2
*Ipiano    *Ipiano    *Ipiano
*>[I,A,A1,A,A2,B,B1,B,B2,C,D,D1,D,D2]    *>[I,A,A1,A,A2,B,B1,B,B2,C,D,D1,D,D2]    *>[I,A,A1,A,A2,B,B1,B,B2,C,D,D1,D,D2]
*>norep[I,A,A2,B,B2,C,D,D2]    *>norep[I,A,A2,B,B2,C,D,D2]    *>norep[I,A,A2,B,B2,C,D,D2]
*>I    *>I    *>I
*clefF4    *clefG2    *clefG2
*k[b-e-a-]    *k[b-e-a-]    *k[b-e-a-]
*E-:    *E-:    *E-:
*M2/2    *M2/2    *M2/2
*MM220    *MM220    *MM220
=1-    =1-    =1-
2EE-/ 2E-/    2e-/ 2ee-/    f
4.DD/ 4.D/    4.d/ 4.dd/    .
8EE-/ 8E-/    8e-/ 8ee-/    .
=2    =2    =2
4CC/ 4C/    4c/ 4cc/    .
4r    2e-/ 2ee-/    .
2C\ 2E-\ 2c\    .    .
.    4f\ 4ff\    .
=3    =3    =3
2C-\ 2E-\ 2c-\    4g-\ 4gg-\    .
.    4gn\ 4ggn\    .
2C-\ 2E-\ 2c-\    4a-\ 4aa-\    .
.    4an\ 4aan\    .
=4    =4    =4
4BB-\ 4D\ 4F\ 4B-\    4b-\ 4bb-\    .
4r    4r    .
2r    2b-\    .
=5!|:    =5!|:    =5!|:
*>A    *>A    *>A
*^    *    *
4r    2E-^\    4b-\ 4gg\    mf
4G/ 4B-/    .    8r    .
.    .    8b-\ 8gg\    <
4r    2D^\    4bn\ 4gg\    .
4F/ 4G/    .    4b\ 4gg\    .
=6    =6    =6    =6
4r    2C\    4cc\ 4gg\    .
4E-/ 4G/ 4c/    .    8r    .
.    .    8cc\ 8gg\    .
4r    2F\    4cc\ 4aa-\    .
4A-/ 4c/    .    4cc\ 4aa-\    .
=7    =7    =7    =7
4r    2D^\    (8ff\L    .
.    .    8een\)    .
4F/ 4B-/    .    8ff'\    .
.    .    8gg'\J    .
4r    2C^\    4ff'\    .
4F/ 4An/    .    4ee-'\    .
=8    =8    =8    =8
.    .    ee-q/    .
4r    2BB-^\    4dd'\    .
4F/ 4B-/    .    4cc'\    .
4r    2A-^\    4dd'\    .
4B-/ 4d/    .    4b-'\    .
=9    =9    =9    =9
4r    2G\    4b-\ 4bb-\    .
4B-/ 4e-/    .    8r    .
.    .    8b-\ 8bb-\    .
4r    2F\    4b-\ 4bb-\    .
4A-/ 4B-/    .    4b-\ 4bb-\    .
=10    =10    =10    =10
4r    2E-\    4b-\ 4bb-\    .
4G/ 4B-/    .    8r    .
.    .    8b-\ 8bb-\    .
4r    2D\    4bn\ 4bbn\    .
4G/ 4Bn/    .    4b\ 4bb\    .
=11    =11    =11    =11
4r    2C\    8cc\ (8ccc\L    .
.    .    8bbn\)    .
4G/ 4c/    .    8ccc'\    .
.    .    8eee-'\J    .
4r    2E-\    4ddd^\    .
4G/ 4c/    .    4cc\ 4ccc\    .
*v    *v    *    *
=12    =12    =12
4GG/    2.bn\ 2.bbn\    .
4G\ 4Bn\ 4d\    .    .
4G\ 4B\ 4d\    .    .
4G\ 4B\ 4d\    4b\ 4bb\    .
=13    =13    =13
4E-\    4b-\ 4bb-\    p
4G\ 4B-\    8r    .
.    8bb-\    .
4BB-/    4eee-'\    .
4G\ 4B-\    8r    .
.    8ccc'\    .
=14    =14    =14
4E-\    4bb-'\    .
4G\ 4B-\    4aan'\    .
4BB-/    4bb-'\    .
4G\ 4B-\    4gg'\    .
=15    =15    =15
4D\    4ff^\    f
4A-\ 4B-\    (8b-^/L    .
.    8an/J    .
4BB-/    8b-/L    .
.    8a/J    .
4A-\ 4B-\    4b-/)    .
=16    =16    =16
4D\    4ff^\    .
4A-\ 4B-\    (8b-^/L    .
.    8an/J    .
4BB-/    8b-/L    .
.    8a/J    .
4A-\ 4B-\    4b-/)    .
=17    =17    =17
4E-\    4b-\ 4bb-\    p
4G\ 4B-\    8r    .
.    8bb-'\    .
4BB-/    4eee-'\    .
4G\ 4B-\    8r    .
.    8ccc'\    .
=18    =18    =18
4E-\    4bb-'\    .
4G\ 4B-\    4aan'\    .
4BB-/    4bb-'\    .
4B-\ 4e-\    4gg-'\    .
=19    =19    =19
4F\    4ff\    f
4c\ 4e-\    (8an^/L    .
.    8g/J    .
4F\    8a/L    .
.    8g/J    .
4c\ 4e-\    4a/    .
=20    =20    =20
*>A1    *>A1    *>A1
4B-\ 4d\    4b-\)    .
4r    4r    .
2BB-\ 2D\ 2F\ 2B-\    2b-\    .
=21:|!    =21:|!    =21:|!
*>A2    *>A2    *>A2
4B-\ 4d\    4b-\    .
4r    4r    .
2BB-\ 2D\ 2F\ 2B-\    4.b-\ (4.bb-\    ff
.    8a-\ 8aa-\)    .
=22!|:    =22!|:    =22!|:
*>B    *>B    *>B
4E-\    2g\ 2gg\    ff
4G\ 4B-\    .    .
4BB-/    4.cc\ (4.ccc\    .
4G\ 4B-\    .    .
.    8b-\ 8bb-\)    .
=23    =23    =23
4F\    2d/ 2dd/    .
4A-\ 4B-\    .    .
4BB-/    2c/ 2cc/    .
4A-\ 4B-\    .    .
=24    =24    =24
4D\    2B-/ 2b-/    .
4A-\ 4B-\    .    .
4BB-/    2a-\ 2aa-\    .
4A-\ 4B-\    .    .
=25    =25    =25
4E-\    2g\ 2gg\    .
4G\ 4B-\ 4e-\    .    .
4G\ 4B-\ 4e-\    4.f\ (4.ff\    .
4G\ 4B-\ 4e-\    .    .
.    8g\ 8gg\)    .
=26    =26    =26
4AA-/    4a-\ 4aa-\    .
4A-\ 4c\ 4e-\    2cc\ 2ccc\    .
4A-\ 4c\ 4e-\    .    .
4A-\ 4c\ 4e-\    4ee-\ 4eee-\    .
=27    =27    =27
4AAn/    2ff\ 2fff\    .
4An\ 4c\ 4e-\    .    .
4A\ 4c\ 4e-\    2ee-\ 2eee-\    .
4A\ 4c\ 4e-\    .    .
=28    =28    =28
4BB-/    1g (1gg    .
4B-\ 4e-\    .    .
4E-^\    .    .
4G\ 4B-\ 4e-\    .    .
=29    =29    =29
4D^\    2f\ 2ff\)    .
4A-\ 4B-\ 4d\    .    .
2BB-\ 2D\ 2F\ 2B-\    4.b-\ (4.bb-\    .
.    8a-\ 8aa-\)    .
=30    =30    =30
4E-\    2g\ 2gg\    .
4G\ 4B-\    .    .
4BB-/    4.cc\ (4.ccc\    .
4G\ 4B-\    .    .
.    8b-\ 8bb-\)    .
=31    =31    =31
4F\    2d/ 2dd/    .
4A-\ 4B-\    .    .
4BB-/    2c/ 2cc/    .
4A-\ 4B-\    .    .
=32    =32    =32
4D\    2B-/ 2b-/    .
4A-\ 4B-\    .    .
4BB-/    2a-\ 2aa-\    .
4A-\ 4B-\    .    .
=33    =33    =33
*^    *    *
4r    2E-\    2g\ 2gg\    .
4G/ 4B-/    .    .    .
4r    2D-\    4.f\ (4.ff\    .
4G/ 4B-/    .    .    .
.    .    8g\ 8gg\)    .
=34    =34    =34    =34
4r    2C\    4a-\ (4aa-\    .
4E-/ 4A-/    .    4cc\ 4ccc\    .
4r    2C-\    4.ff\ 4.fff\    .
4E-/ 4A-/    .    .    .
.    .    8ee-\ 8eee-\)    .
*v    *v    *    *
=35    =35    =35
4BB-/    4g\ (4gg\    .
4G\ 4B-\ 4e-\    4b-\ 4bb-\    .
4G\ 4B-\ 4e-\    4.e-/ 4.ee-/    .
4G\ 4B-\ 4e-\    .    .
.    8g\ 8gg\)    .
=36    =36    =36
4BB-/    (1f 1ff    .
4A-\ 4B-\ 4d\    .    .
4A-\ 4B-\ 4d\    .    .
4A-\ 4B-\ 4d\    .    .
=37    =37    =37
*>B1    *>B1    *>B1
4E-\ 4G\ 4B-\    4e-/) 4ee-/    .
4r    4r    .
2BB-\ 2D\ 2F\ 2B-\    4.b-\ 4.bb-\    ff
.    8a-\ 8aa-\    .
=38:|!    =38:|!    =38:|!
*>B2    *>B2    *>B2
4E-\ 4G\ 4B-\    4e-/ 4ee-/    .
4r    4r    .
2r    2ee-\    p
=39    =39    =39
*>C    *>C    *>C
*k[b-e-a-d-]    *k[b-e-a-d-]    *k[b-e-a-d-]
4AA-^/    2ee-\    p
4A-\ 4c\ 4e-\    .    .
4A-\ 4c\ 4e-\    (4dd-\    .
4E-^\    4cc\)    .
=40    =40    =40
4AA-^/    2cc\    .
4A-\ 4c\ 4e-\    .    .
4A-\ 4c\ 4e-\    (4bn\    .
4E-^\    4cc\)    .
=41    =41    =41
4AA-^/    [1cc    .
4A-\ 4c\ 4e-\    .    .
4A-\ 4c\ 4e-\    .    .
4E-^\    .    .
=42    =42    =42
4AA-^/    2cc\]    .
4A-\ 4c\ 4e-\    .    .
4A-\ 4c\ 4e-\    (4bn^\    .
4E-^\    4cc\)    .
=43    =43    =43
4AA-^/    2cc\    .
4A-\ 4c\ 4e-\    .    .
4A-\ 4c\ 4e-\    (4bn^\    .
4E-^\    4cc\)    .
=44    =44    =44
4AA-^/    2ee-\    .
4A-\ 4c\ 4e-\    .    .
4A-\ 4c\ 4e-\    (4.cc^\    .
4E-^\    .    .
.    8ee-\)    .
=45    =45    =45
4BB-^/    (1dd-    .
4G\ 4d-\ 4e-\    .    .
4G\ 4d-\ 4e-\    .    .
4E-^\    .    .
=46    =46    =46
4BB-^/    2b-\)    .
4G\ 4d-\ 4e-\    .    .
4G\ 4d-\ 4e-\    2b-\    .
4E-^\    .    .
=47    =47    =47
4BB-^/    2b-\    .
4G\ 4d-\ 4e-\    .    .
4G\ 4d-\ 4e-\    4an^/    .
4E-^\    4b-/    .
=48    =48    =48
4BB-^/    2b-\    .
4G\ 4d-\ 4e-\    .    .
4G\ 4d-\ 4e-\    4an^/    .
4E-^\    4b-/    .
=49    =49    =49
4BB-^/    [1dd-    .
4G\ 4d-\ 4e-\    .    .
4G\ 4d-\ 4e-\    .    .
4E-^\    .    .
=50    =50    =50
4BB-^/    2dd-\]    .
4G\ 4d-\ 4e-\    .    .
4G\ 4d-\ 4e-\    (4cc\    .
4E-^\    4b-\)    .
=51    =51    =51
4AA-^/    4cc\    .
4A-\ 4c\ 4e-\    2.ee-\    .
4A-\ 4c\ 4e-\    .    .
4A-\ 4c\ 4e-\    .    .
=52    =52    =52
4D-^\    2.a-\ 2.dd-\ 2.ff\    .
4A-\ 4d-\ 4f\    .    .
4A-\ 4d-\ 4f\    .    .
4A-\ 4d-\ 4f\    (4ff\    .
=53    =53    =53
4E-^\    [1b-)    .
4G\ 4B-\ 4e-\    .    .
4BB-^/    .    .
4G\ 4B-\ 4e-\    .    .
=54    =54    =54
4GG^/    2b-\]    .
4G\ 4B-\ 4e-\    .    .
4E-^\    2ee-\    .
4G\ 4B-\ 4e-\    .    .
=55    =55    =55
4AA-^/    2ee-\    .
4A-\ 4c\ 4e-\    .    .
4A-\ 4c\ 4e-\    (4dd-\    .
4E-^\    4cc\)    .
=56    =56    =56
4AA-^/    2cc\    .
4A-\ 4c\ 4e-\    .    .
4A-\ 4c\ 4e-\    (4bn\    .
4E-^\    4cc\)    .
=57    =57    =57
4AA-^/    [1cc    .
4A-\ 4c\ 4e-\    .    .
4A-\ 4c\ 4e-\    .    .
4E-^\    .    .
=58    =58    =58
4AA-^/    2cc\]    .
4A-\ 4c\ 4e-\    .    .
4A-\ 4c\ 4e-\    (4bn^\    .
4E-^\    4cc\)    .
=59    =59    =59
4GG^/ 4G^/    2cc\    .
4B-\ 4c\ 4en\    .    .
4B-\ 4c\ 4e\    (4bn\    .
4C^/    4cc\)    .
=60    =60    =60
4GG^/ 4G^/    (4dd-\    <
4B-\ 4c\ 4en\    4cc\    .
4B-\ 4c\ 4e\    4.b-\    .
4C^/    .    .
.    8gg\)    .
=61    =61    =61
4F^\    (1b-    .
4B-\ 4c\ 4f\    .    .
4B-\ 4c\ 4f\    .    .
4C^/    .    .
=62    =62    =62
4F^\    2a-/)    .
4A-\ 4c\ 4f\    .    .
4A-\ 4c\ 4f\    2a-/    .
4C^/    .    .
=63    =63    =63
4F-\    2a-/    .
4A-\ 4d-\    .    .
4A-\ 4d-\    4g^/    .
4A-\ 4d-\    4a-/    .
=64    =64    =64
4F-\    (2cc-\    .
4A-\ 4c-\    .    .
4A-\ 4c-\    4b-\    <
4A-\ 4c-\    4a-/)    .
=65    =65    =65
4E-\    [1a- [1aa-    .
4cn\ 4e-\    .    .
4AA-/    .    .
4c\ 4e-\    .    .
=66    =66    =66
4C/    4a-\] 4aa-\]    .
4c\ 4e-\    (4a-/    <
4E-\    4b-\    .
4c\ 4e-\    4cc\    .
=67    =67    =67
4C/    8ee-\)    .
.    8r    .
4c\ 4e-\    (4a-/    <
4E-\    4b-\    .
4c\ 4e-\    4cc\    .
=68    =68    =68
4A-\    8ee-\)    .
.    8r    .
4c\ 4e-\    (4e-/    .
4c\    4f/    .
4e-\ 4a-\    4cc\    .
=69    =69    =69
4G\    (1b-)    .
4d-\ 4e-\    .    .
4E-\    .    .
4d-\ 4e-\    .    .
=70    =70    =70
4A-\ 4c\ 4e-\    4a-/)    .
4r    4r    .
4AA-^\ 4A-^\    2r    .
4AA-^\ 4A-^\    .    .
=71!|:    =71!|:    =71!|:
*>D    *>D    *>D
4AA-\ (4A-\    1r    .
8GG/ 8G/)    .    .
8r    .    .
(4GG/ 4G/    .    .
8FF/) 8F/    .    .
8r    .    .
=72    =72    =72
4FF/ 4F/    2r    .
4EEn/ 4En/    .    .
2r    4f\ 4ff\    f
.    4en/ 4een/    .
=73    =73    =73
4FF/ 4F/    2r    .
4EEn/ 4En/    .    .
4D-\ 4F\ 4B-\    4f\ 4ff\    .
4D-\ 4F\ 4B-\    4g\ 4gg\    .
=74    =74    =74
2C\ 2En\ 2G\ 2c\    2en/ 2een/    .
4C\ 4c\    2r    .
4C\ 4c\    .    .
=75    =75    =75
4C\ (4c\    1r    .
8BB-\ 8B-\)    .    .
8r    .    .
4BB-\ (4B-\    .    .
8AA-\ 8A-\)    .    .
8r    .    .
=76    =76    =76
4AA-\ 4A-\    2r    .
4GG/ 4G/    .    .
2r    4a-\ 4aa-\    .
.    4g\ 4gg\    .
=77    =77    =77
4AA-\ 4A-\    2r    .
4GG/ 4G/    .    .
4F-\ 4A-\ 4d-\    4a-\ 4aa-\    .
4F-\ 4A-\ 4d-\    4b-\ 4bb-\    .
=78    =78    =78
2E-\ 2G\ 2B-\ 2e-\    2g\ 2gg\    .
2r    (8e-/L    <
.    8g/    .
.    8b-/    .
.    8dd-/J    .
=79    =79    =79
*    *^    *
1r    4.ff-/)    4.f-\    .
.    8a-/ 8b-/ 8ff-/    8f-\    .
.    4a-/ 4b-/ 4ff-/    4f-\    .
.    4a-/ 4b-/ 4ff-/    4f-\    .
=80    =80    =80    =80
1r    4g/ 4b-/ 4ff-/    4f-\    .
.    4ee-/    4e-\    .
.    4ddn/    4dn\    .
.    4dd-/    4d-\    .
=81    =81    =81    =81
1r    4cc/    4c\    .
.    4cc-/    4c-\    .
.    4b-/    4B-\    .
.    4an/    4An\    .
=82    =82    =82    =82
2r    4a-/    4A-\    .
.    4g-/    4G-\    .
4r    (8f/L    2r    .
.    8an/    .    .
4r    8cc/    .    .
.    8ee-/J    .    .
=83    =83    =83    =83
1r    4.gg-/)    4.g-\    .
.    8b-/ 8cc/ 8gg-/    8g-\    .
.    4b-/ 4cc/ 4gg-/    4g-\    .
.    4b-/ 4cc/ 4gg-/    4g-\    .
=84    =84    =84    =84
1r    4an/ 4cc/ 4gg-/    4g-\    .
.    4ff/    4f\    .
.    4een/    4en\    .
.    4ee-/    4e-\    .
=85    =85    =85    =85
1r    4ddn/    4dn\    .
.    4dd-/    4d-\    .
.    4cc/    4c\    .
.    4cc-/    4c-\    .
=86    =86    =86    =86
2r    4b-/    4B-\    .
.    4a-/    4A-\    .
4r    (8g/L    2r    .
.    8b-/    .    .
4r    8ee-/    .    .
.    8gg/J    .    .
=87    =87    =87    =87
1r    4.bb-/)    4.b-\    .
.    8dd-/ 8ff-/ 8aa-/ 8bb-/    8b-\    .
.    4dd-/ 4ff-/ 4aa-/ 4bb-/    4b-\    .
.    4dd-/ 4ff-/ 4aa-/ 4bb-/    4b-\    .
=88    =88    =88    =88
2r    4dd-/ 4ee-/ 4gg/ 4bb-/    4e-\    .
.    4dd-/ 4ee-/ 4gg/ 4bb-/    4e-\    .
2r    2r    (8g\L    .
.    .    8b-\    .
.    .    8ee-\    .
.    .    8gg\J    .
=89    =89    =89    =89
1r    4.bb-/)    4.b-\    .
.    8dd-/ 8ff-/ 8aa-/ 8bb-/    8b-\    .
.    4dd-/ 4ff-/ 4aa-/ 4bb-/    4b-\    .
.    4dd-/ 4ff-/ 4aa-/ 4bb-/    4b-\    .
=90    =90    =90    =90
2r    4dd-/ 4ee-/ 4gg/ 4bb-/    4e-\    .
.    4dd-/ 4ee-/ 4gg/ 4bb-/    4e-\    .
2r    2r    (8g\L    .
.    .    8b-\    .
.    .    8ee-\    .
.    .    8gg\J    .
*    *v    *v    *
=91    =91    =91
4.BB-\ 4.B-\    4.b-\ 4.bb-\)    .
8BB-\ (8B-\    8b-\ (8bb-\    <
4.AAn\ 4.An\)    4.an\ 4.aan\)    .
8AA\ (8A\    8a\ (8aa\    .
=92    =92    =92
4.AA-\ 4.A-\)    4.a-\ 4.aa-\)    .
8AA-\ (8A-\    8a-\ (8aa-\    .
4.GG/ 4.G/)    4.g\ 4.gg\)    .
(8GG/ 8G/    8g\ (8gg\    .
=93    =93    =93
4.GG-/) 4.G-/    4.g-\ 4.gg-\)    .
(8GG-/ 8G-/    8g-\ (8gg-\    .
4.FF/) 4.F/    4.f\ 4.ff\)    .
(8FF/ 8F/    8f\ (8ff\    .
=94    =94    =94
4FF-/) 4F-/    4f-\ 4ff-\)    <
4EE-/ 4E-/    4e-/ 4ee-/    .
4FFn/ 4Fn/    4fn\ 4ffn\    .
4EE-/ 4E-/    4ee-\    .
=95    =95    =95
4AA-/    2ee-\ 2eee-\    ff
4A-\ 4c\ 4e-\    .    .
4A-\ 4c\ 4e-\    4dd-\ (4ddd-\    .
4E-\    4cc\ 4ccc\)    .
=96    =96    =96
4AA-/    2cc\ 2ccc\    .
4A-\ 4c\ 4e-\    .    .
4A-\ 4c\ 4e-\    4bn\ (4bbn\    .
4E-\    4cc\ 4ccc\)    .
=97    =97    =97
4AA-/    [1cc [1ccc    .
4A-\ 4c\ 4e-\    .    .
4A-\ 4c\ 4e-\    .    .
4E-\    .    .
=98    =98    =98
4AA-/    2cc\] 2ccc\]    .
4A-\ 4c\ 4e-\    .    .
4A-\ 4c\ 4e-\    4bn\ (4bbn\    .
4E-\    4cc\ 4ccc\)    .
=99    =99    =99
4AA-/    2cc\ 2ccc\    .
4A-\ 4c\ 4e-\    .    .
4A-\ 4c\ 4e-\    4bn\ (4bbn\    .
4E-\    4cc\ 4ccc\)    .
=100    =100    =100
4AA-/    2ee-\ 2eee-\    .
4A-\ 4c\ 4e-\    .    .
4A-\ 4c\ 4e-\    4.cc\ (4.ccc\    .
4E-\    .    .
.    8ee-\ 8eee-\)    .
=101    =101    =101
4BB-/    1dd- (1ddd-    .
4G\ 4d-\ 4e-\    .    .
4G\ 4d-\ 4e-\    .    .
4E-\    .    .
=102    =102    =102
4BB-/    2b-\ 2bb-\)    .
4G\ 4d-\ 4e-\    .    .
4G\ 4d-\ 4e-\    2b-\ 2bb-\    .
4E-\    .    .
=103    =103    =103
4BB-/    2b-\ 2bb-\    .
4G\ 4d-\ 4e-\    .    .
4G\ 4d-\ 4e-\    4an\ (4aan\    .
4E-\    4b-\ 4bb-\)    .
=104    =104    =104
4BB-/    2b-\ 2bb-\    .
4G\ 4d-\ 4e-\    .    .
4G\ 4d-\ 4e-\    4an\ (4aan\    .
4E-\    4b-\ 4bb-\)    .
=105    =105    =105
4BB-/    [1dd- [1ddd-    .
4G\ 4d-\ 4e-\    .    .
4G\ 4d-\ 4e-\    .    .
4E-\    .    .
=106    =106    =106
4BB-/    2dd-\] 2ddd-\]    .
4G\ 4d-\ 4e-\    .    .
4G\ 4d-\ 4e-\    4cc\ 4ccc\    .
4E-\    4b-\ 4bb-\    .
=107    =107    =107
4AA-/    4cc\ 4ccc\    <
4A-\ 4c\ 4e-\    2.ee-\ 2.eee-\    .
4A-\ 4c\ 4e-\    .    .
4A-\ 4c\ 4e-\    .    .
=108    =108    =108
4D-\    2.ff\ 2.fff\    .
4A-\ 4d-\ 4f\    .    .
4A-\ 4d-\ 4f\    .    .
4A-\ 4d-\ 4f\    4ff\ 4fff\    .
=109    =109    =109
4E-\    [1b- [1bb-    .
4G\ 4B-\ 4e-\    .    .
4BB-/    .    .
4G\ 4B-\ 4e-\    .    .
=110    =110    =110
4GG/    2b-\] 2bb-\]    .
4G\ 4B-\ 4e-\    .    .
4E-\    2ee-\ 2eee-\    .
4G\ 4B-\ 4e-\    .    .
=111    =111    =111
4AA-/    2ee-\ 2eee-\    .
4A-\ 4c\ 4e-\    .    .
4A-\ 4c\ 4e-\    4dd-\ (4ddd-\    .
4E-\    4cc\ 4ccc\)    .
=112    =112    =112
4AA-/    2cc\ 2ccc\    .
4A-\ 4c\ 4e-\    .    .
4A-\ 4c\ 4e-\    4bn\ (4bbn\    .
4E-\    4cc\ 4ccc\)    .
=113    =113    =113
4AA-/    [1cc [1ccc    .
4A-\ 4c\ 4e-\    .    .
4A-\ 4c\ 4e-\    .    .
4E-\    .    .
=114    =114    =114
4AA-/    2cc\] 2ccc\]    .
4A-\ 4c\ 4e-\    .    .
4A-\ 4c\ 4e-\    4bn\ (4bbn\    .
4E-\    4cc\ 4ccc\)    .
=115    =115    =115
4GG/ 4G/    2cc\ 2ccc\    .
4B-\ 4c\ 4en\    .    .
4B-\ 4c\ 4e\    4bn\ (4bbn\    .
4C/    4cc\ 4ccc\)    .
=116    =116    =116
4GG/ 4G/    4dd-\ (4ddd-\    .
4B-\ 4c\ 4en\    4cc\ 4ccc\    .
4B-\ 4c\ 4e\    4.b-\ 4.bb-\    .
4C/    .    .
.    8gg\ 8ggg\)    .
=117    =117    =117
4F\    1b- (1bb-    .
4B-\ 4c\ 4f\    .    .
4B-\ 4c\ 4f\    .    .
4C/    .    .
=118    =118    =118
4F\    2a-\ 2aa-\)    .
4A-\ 4c\ 4f\    .    .
4A-\ 4c\ 4f\    2a-\ 2aa-\    .
4C/    .    .
=119    =119    =119
4F-\    2a-\ (2aa-\    .
4A-\ 4d-\    .    .
4A-\ 4d-\    4g\ 4gg\    .
4A-\ 4d-\    4a-\ 4aa-\)    .
=120    =120    =120
4F-\    2cc-\ (2ccc-\    .
4A-\ 4c-\    .    .
4A-\ 4c-\    4b-\ 4bb-\    .
4A-\ 4c-\    4a-\ 4aa-\)    .
=121    =121    =121
4E-\    [1aa- [1aaa-    .
4c\ 4e-\    .    .
4AA-/    .    .
4c\ 4e-\    .    .
=122    =122    =122
4C/    4aa-\] 4aaa-\]    .
4c\ 4e-\    4a-\ (4aa-\    .
4E-\    4b-\ 4bb-\    .
4c\ 4e-\    4cc\ 4ccc\    .
=123    =123    =123
4C/    8ee-\ 8eee-\)    .
.    8r    .
4c\ 4e-\    4a-\ (4aa-\    .
4E-\    4b-\ 4bb-\    .
4c\ 4e-\    4cc\ 4ccc\    .
=124    =124    =124
4A-\    8ee-\ 8eee-\)    .
.    8r    .
4c\ 4e-\    4e-/ (4ee-/    .
4c\    4f\ 4ff\    .
4e-\ 4a-\    4cc\ 4ccc\    .
=125    =125    =125
4G\    1b- 1bb-    .
4d-\ 4e-\    .    .
4E-\    .    .
4d-\ 4e-\    .    .
=126    =126    =126
*>D1    *>D1    *>D1
4A-\ 4c\ 4e-\    4a-\ 4aa-\)    .
4r    4r    .
4AA-^\ 4A-^\    2r    .
4AA-^\ 4A-^\    .    .
=127:|!    =127:|!    =127:|!
*>D2    *>D2    *>D2
4A-\ 4c\ 4e-\    4a-\ 4aa-\    .
4r    4r    .
4AAA-^/ 4AA-^/    4a-^\ 4cc^\ 4ee-^\ 4aa-^\    .
4r    4r    .
==    ==    ==
*-    *-    *-
!!!ENC: Craig Stuart Sapp
!!!END: 2006/06/17/
'''
)

multipartSanctus = re.sub(r"\s\s\s\s","\t",
r'''!!!COM: Palestrina, Giovanni Perluigi da
**kern    **kern    **kern    **kern
*Ibass    *Itenor    *Icalto    *Icant
!Bassus    !Tenor    !Altus    !Cantus
*clefF4    *clefGv2    *clefG2    *clefG2
*M4/2    *M4/2    *M4/2    *M4/2
=1    =1    =1    =1
0r    0r    1g    1r
.    .    1a    1cc
=2    =2    =2    =2
0r    0r    1g    1dd
.    .    1r    1cc
*-    *-    *-    *-
!! Pleni
**kern    **kern    **kern
*Ibass    *Itenor    *Icalto
*clefF4    *clefGv2    *clefG2
*M4/2    *M4/2    *M4/2
=3    =3    =3
1G    1r    0r
1A    1c    .
=4    =4    =4
1B    1d    1r
1c    1e    1g
*-    *-    *-
!! Hosanna
**kern    **kern    **kern    **kern
*Ibass    *Itenor    *Icalto    *Icant
*clefF4    *clefGv2    *clefG2    *clefG2
*M3/2    *M3/2    *M3/2    *M3/2
=5    =5    =5    =5
1r    1r    1g    1r
2r    2r    [2a    [2cc
=5    =5    =5    =5
1r    1r    2a]    2cc]
.    .    2f    1dd
2r    2r    2g    .
*-    *-    *-    *-
''')



#------------------------------------------------------------------------------
# eof

if __name__ == '__main__':
    from music21 import converter
    unused_s = converter.parse(multipartSanctus, format='humdrum')
    #s = corpus.parse('palestrina/Sanctus_0.krn')
    #print s
