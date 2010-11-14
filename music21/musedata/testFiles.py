# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         testFiles.py
# Purpose:      MuseData test files
#
# Authors:      most by Walter Hewlett; see examples
#
# License:      according to the files
#-------------------------------------------------------------------------------

import music21
import unittest

# musedata standard
# http://www.ccarh.org/publications/books/beyondmidi/online/musedata/

from music21 import environment
_MOD = 'musedata.testFiles.py'
environLocal = environment.Environment(_MOD)



# http://www.musedata.org/cgi-bin/mddata?composer=bach&edition=bg&genre=cant&work=0005&format=stage2&movement=03
bach_cantata5_mvmt3 = r'''&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
PART = 01
&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
(C) 1991, 2002 Center for Computer Assisted Research in the Humanities.
ID: {bach/bg/cant/0005/stage2/03/01} [KHM:1658122244]
TIMESTAMP: DEC/26/2001 [md5sum:6c630aa04ec9820c9bf44540e2d34d6c]
03/06/91 S. Rasmussen
WK#:5         MV#:3
Bach Gesellschaft i
Wo soll ich fliehen hin
Aria
Viola Solo
1 75
Group memberships: score
score: part 1 of 3
&
conversion from old-format Stage2 to new-format Stage2
S. Rasmussen    09/02/93
&
$ K:-3   Q:4   T:3/4   C:13
Bf3    4        q     u
measure 1       A
S C0:S4
G4     1        s     d  [[     (
F4     1        s     d  ==
Ef4    1        s     d  ==
D4     1        s     d  ]]
Ef4    1        s     u  [[     )
Bf3    1        s     u  ==
G3     1        s     u  ==
Bf3    1        s     u  ]]
Ef4    1        s     u  [[
Bf3    1        s     u  ==
G3     1        s     u  ==
Bf3    1        s     u  ]]
measure 2
G4     1        s     d  [[     (
F4     1        s     d  ==
Ef4    1        s     d  ==
D4     1        s     d  ]]
Ef4    1        s     d  [[     )
C4     1        s     d  ==
G3     1        s     d  ==
C4     1        s     d  ]]
Ef4    1        s     d  [[
C4     1        s     d  ==
G3     1        s     d  ==
C4     1        s     d  ]]
measure 3
F4     1        s     d  [[     (
Ef4    1        s     d  ==
D4     1        s     d  ==     )
C4     1        s     d  ]]
Af4    1        s     d  [[     (
G4     1        s     d  ==
F4     1        s     d  ==     )
Ef4    1        s     d  ]]
D4     1        s     d  [[     .
C5     1        s     d  ==     (
Bf4    1        s     d  ==
Af4    1        s     d  ]]     )
measure 4
G4     1        s     d  [[     (
F4     1        s     d  ==
Ef4    1        s     d  ==
D4     1        s     d  ]]
Ef4    1        s     u  [[     )
Bf3    1        s     u  ==
G3     1        s     u  ==
Bf3    1        s     u  ]]
Ef4    1        s     u  [[
Bf3    1        s     u  ==
G3     1        s     u  ==
Bf3    1        s     u  ]]
measure 5
Ef4    1        s     d  [[     (
D4     1        s     d  ==
C4     1        s     d  ==
D4     1        s     d  ]]
Ef4    1        s     d  [[     )
C5     1        s     d  ==
Ef4    1        s     d  ==     (
D4     1        s     d  ]]
Ef4    1        s     d  [[     )
C5     1        s     d  ==
Ef4    1        s     d  ==     (
D4     1        s     d  ]]
measure 6
Ef4    1        s     d  [[     )
D4     1        s     d  ==
C4     1        s     d  ==
D4     1        s     d  ]]
Ef4    1        s     d  [[     (
C4     1        s     d  ==     )
Ef4    1        s     d  ==     (
Bf3    1        s     d  ]]     )
Ef4    1        s     d  [[     (
A3     1        s n   d  ==     )
Ef4    1        s     d  ==     (
C4     1        s     d  ]]     )
measure 7
D4     1        s     d  [[     (
Bf3    1        s     d  ==     )
F4     1        s     d  ==     (
Bf3    1        s     d  ]]     )
G4     1        s     d  [[     (
Bf3    1        s     d  ==     )
Ef4    1        s     d  ==     (
Bf3    1        s     d  ]]     )
D4     1        s     u  [[     (
Bf3    1        s     u  ==     )
C4     1        s     u  ==     (
A3     1        s n   u  ]]     )
measure 8
Bf3    4-       q     u        -
Bf3    1        s     d  [[
C4     1        s     d  ==     (
D4     1        s     d  ==
Ef4    1        s     d  ]]
F4     1        s     d  [[
G4     1        s     d  ==
Af4    1        s     d  ==     +
Bf4    1        s     d  ]]     )
measure 9
G3     1        s     d  [[     (
E4     1        s n   d  ==     )
Bf4    1        s     d  ==     (
E4     1        s     d  ]]     )
Bf4    1        s     d  [[     (
E4     1        s     d  ==     )
Bf4    1        s     d  ==     (
E4     1        s     d  ]]     )
G3     1        s     d  [[     (
E4     1        s     d  ==     )
Bf4    1        s     d  ==     (
E4     1        s     d  ]]     )
measure 10
Af3    1        s     u  [[     .
F4     1        s     u  ==     .
Af3    1        s     u  ==     (
G3     1        s     u  ]]
Af3    1        s     u  [[     )
F4     1        s     u  ==     .
Af3    1        s     u  ==     (
G3     1        s     u  ]]
Af3    1        s     u  [[     )
Bf3    1        s     u  ==
C4     1        s     u  ==
D4     1        s     u  ]]
measure 11
A3     1        s n   d  [[     (
Ef4    1        s     d  ==     )
C5     1        s     d  ==     (
Ef4    1        s     d  ]]     )
C5     1        s     d  [[     (
Ef4    1        s     d  ==     )
C5     1        s     d  ==     (
Ef4    1        s     d  ]]     )
A3     1        s     d  [[     (
Ef4    1        s     d  ==     )
C5     1        s     d  ==     (
Ef4    1        s     d  ]]     )
measure 12
Bf3    1        s     u  [[     .
D4     1        s     u  ==     .
Bf3    1        s     u  ==     (
A3     1        s n   u  ]]
Bf3    1        s     u  [[     )
D4     1        s     u  ==
Bf3    1        s     u  ==     (
P C33:u
A3     1        s     u  ]]
Bf3    1        s     d  [[     )
C4     1        s     d  ==     .
D4     1        s     d  ==     .
Ef4    1        s     d  ]]     .
measure 13
Af3    1        s     d  [[     (+
F4     1        s     d  ==     )
D5     1        s     d  ==     (
F4     1        s     d  ]]     )
D5     1        s     d  [[     (
F4     1        s     d  ==     )
D5     1        s     d  ==     (
F4     1        s     d  ]]     )
Af3    1        s     d  [[     (
F4     1        s     d  ==     )
D5     1        s     d  ==     (
F4     1        s     d  ]]     )
measure 14
G3     1        s     d  [[     (
Ef4    1        s     d  ==     )
Df5    1        s f   d  ==     (
Ef4    1        s     d  ]]     )
Df5    1        s     d  [[     (
Ef4    1        s     d  ==     )
Df5    1        s     d  ==     (
Ef4    1        s     d  ]]     )
G3     1        s     d  [[     (
Ef4    1        s     d  ==     )
Df5    1        s     d  ==     (
Ef4    1        s     d  ]]     )
measure 15
Af3    1        s     d  [[     (
Ef4    1        s     d  ==     )
C5     1        s     d  ==     (
Bf4    1        s     d  ]]
Af4    1        s     d  [[
G4     1        s     d  ==
F4     1        s     d  ==
Ef4    1        s     d  ]]     )
Bf3    1        s     d  [[     .
Ef4    1        s     d  ==     .
F4     1        s     d  ==     .
D4     1        s     d  ]]     .
measure 16
Ef4    1        s     d  [[     .
C4     1        s     d  ==     (
Bf3    1        s     d  ==
Af3    1        s     d  ]]     )
G3     1        s     d  [[     (
Bf3    1        s     d  ==
Ef4    1        s     d  ==
D4     1        s     d  ]]     )
Ef4    1        s     d  [[     (
D4     1        s     d  ==
C4     1        s     d  ==
Bf3    1        s     d  ]]     )
measure 17
G4     1        s     d  [[     (p
F4     1        s     d  ==
Ef4    1        s     d  ==
D4     1        s     d  ]]
Ef4    1        s     u  [[     )
Bf3    1        s     u  ==
G3     1        s     u  ==
Bf3    1        s     u  ]]
Ef4    1        s     u  [[
Bf3    1        s     u  ==
G3     1        s     u  ==
Bf3    1        s     u  ]]
measure 18
G4     1        s     d  [[     (
F4     1        s     d  ==
Ef4    1        s     d  ==
D4     1        s     d  ]]
Ef4    1        s     u  [[     )
C4     1        s     u  ==
G3     1        s     u  ==
C4     1        s     u  ]]
Ef4    1        s     u  [[
C4     1        s     u  ==
G3     1        s     u  ==
C4     1        s     u  ]]
measure 19
F4     1        s     d  [[     (
Ef4    1        s     d  ==
D4     1        s     d  ==     )
C4     1        s     d  ]]
Af4    1        s     d  [[     (
G4     1        s     d  ==
F4     1        s     d  ==     )
Ef4    1        s     d  ]]
D4     1        s     d  [[
C5     1        s     d  ==     (
Bf4    1        s     d  ==
Af4    1        s     d  ]]     )
measure 20
G4     1        s     d  [[     (
F4     1        s     d  ==
Ef4    1        s     d  ==
D4     1        s     d  ]]
Ef4    1        s     u  [[     )
Bf3    1        s     u  ==
G3     1        s     u  ==
Bf3    1        s     u  ]]
Ef4    1        s     d  [[     (f
D4     1        s     d  ==     )
C4     1        s     d  ==     (
Bf3    1        s     d  ]]     )
measure 21
Af3    1        s     d  [[     (
F4     1        s     d  ==     )
D5     1        s     d  ==     (
F4     1        s     d  ]]     )
D5     1        s     d  [[     (
F4     1        s     d  ==     )
D5     1        s     d  ==     (
F4     1        s     d  ]]     )
Af3    1        s     d  [[     (
F4     1        s     d  ==     )
D5     1        s     d  ==     (
F4     1        s     d  ]]     )
measure 22
G3     1        s     d  [[     (
Ef4    1        s     d  ==     )
Df5    1        s f   d  ==     (
Ef4    1        s     d  ]]     )
Df5    1        s     d  [[     (
Ef4    1        s     d  ==     )
Df5    1        s     d  ==     (
Ef4    1        s     d  ]]     )
G3     1        s     d  [[     (
Ef4    1        s     d  ==     )
Df5    1        s     d  ==     (
Ef4    1        s     d  ]]     )
measure 23
Af3    1        s     d  [[     (
Ef4    1        s     d  ==     )
C5     1        s     d  ==     (
Bf4    1        s     d  ]]
Af4    1        s     d  [[
G4     1        s     d  ==
F4     1        s     d  ==
Ef4    1        s     d  ]]     )
Bf3    1        s     d  [[     .
Ef4    1        s     d  ==     .
F4     1        s     d  ==     .
D4     1        s     d  ]]     .
measure 24
Ef4    1        s     d  [[
C4     1        s     d  ==     (
Bf3    1        s     d  ==
Af3    1        s     d  ]]     )
G3     1        s     d  [[     (
Bf3    1        s     d  ==
Ef4    1        s     d  ==
D4     1        s     d  ]]     )
Ef4    1        s     d  [[     (
D4     1        s     d  ==
C4     1        s     d  ==
Bf3    1        s     d  ]]     )
measure 25
G4     1        s     d  [[     (p
F4     1        s     d  ==
Ef4    1        s     d  ==
D4     1        s     d  ]]
Ef4    1        s     u  [[     )
Bf3    1        s     u  ==
G3     1        s     u  ==
Bf3    1        s     u  ]]
Ef4    1        s     u  [[
Bf3    1        s     u  ==
G3     1        s     u  ==
Bf3    1        s     u  ]]
measure 26
G4     1        s     d  [[     (
F4     1        s     d  ==
Ef4    1        s     d  ==
D4     1        s     d  ]]
Ef4    1        s     u  [[     )
C4     1        s     u  ==
G3     1        s     u  ==
C4     1        s     u  ]]
Ef4    1        s     u  [[
C4     1        s     u  ==
G3     1        s     u  ==
C4     1        s     u  ]]
measure 27
F4     1        s     d  [[     (
Ef4    1        s     d  ==
D4     1        s     d  ==     )
C4     1        s     d  ]]
Af4    1        s     d  [[     (
G4     1        s     d  ==
F4     1        s     d  ==     )
Ef4    1        s     d  ]]
D4     1        s     d  [[     .
C5     1        s     d  ==     (
Bf4    1        s     d  ==
Af4    1        s     d  ]]     )
measure 28
G4     1        s     d  [[     (
F4     1        s     d  ==
Ef4    1        s     d  ==
D4     1        s     d  ]]
Ef4    1        s     u  [[     )
Bf3    1        s     u  ==
G3     1        s     u  ==
Bf3    1        s     u  ]]
F4     1        s     d  [[     (
Ef4    1        s     d  ==
D4     1        s     d  ==
C4     1        s     d  ]]     )
measure 29
D4     2        e     d  [      (
F4     2        e     d  ]      )
F4     1        s     d  [[     (
Ef4    1        s     d  ==
D4     1        s     d  ==
C4     1        s     d  ]]     )
Bf4    4-       q     d        -
measure 30
Bf4    4        q     d
Ef4    1        s     d  [[     (
D4     1        s     d  ==
C4     1        s     d  ==
Bf3    1        s     d  ]]     )
A4     4-       q n   d        -
measure 31
A4     4        q     d
D4     1        s     u  [[     (
C4     1        s     u  ==
Bf3    1        s     u  ==
A3     1        s n   u  ]]     )
G4     4-       q     d        -
measure 32
G4     2        e     d  [
A3     1        s n   d  =[     (
Bf3    1        s     d  ]]
C4     1        s     d  [[
D4     1        s     d  ==
Ef4    1        s     d  ==
F4     1        s     d  ]]
G4     1        s     d  [[
A4     1        s n   d  ==
Bf4    1        s     d  ==
C5     1        s     d  ]]     )
measure 33
D5     1        s     d  [[     (
C5     1        s     d  ==
Bf4    1        s     d  ==
A4     1        s n   d  ]]
Bf4    1        s     d  [[     )
F4     1        s     d  ==
D4     1        s     d  ==
F4     1        s     d  ]]
Bf4    1        s     d  [[
F4     1        s     d  ==
D4     1        s     d  ==
F4     1        s     d  ]]
measure 34
D5     1        s     d  [[     (
C5     1        s     d  ==
Bf4    1        s     d  ==
A4     1        s n   d  ]]
Bf4    1        s     d  [[     )
G4     1        s     d  ==
D4     1        s     d  ==
G4     1        s     d  ]]
Bf4    1        s     d  [[
G4     1        s     d  ==
D4     1        s     d  ==
G4     1        s     d  ]]
measure 35
C5     1        s     d  [[     (
Bf4    1        s     d  ==
A4     1        s n   d  ==
G4     1        s     d  ]]     )
Ef5    1        s     d  [[     (
D5     1        s     d  ==
C5     1        s     d  ==
Bf4    1        s     d  ]]
A4     1        s     d  [[
G4     1        s     d  ==
F4     1        s     d  ==
Ef4    1        s     d  ]]     )
measure 36
Bf4    2        e     d  [      (
F4     2        e     d  =      )
F4     2        e     d  =      (
D4     2        e     d  =      )
D4     2        e     d  =      (
G4     2        e     d  ]      )
measure 37
G4     2        e     d  [      (
Ef4    2        e     d  =      )
Ef4    2        e     d  =      (
C4     2        e     d  =      )
C4     2        e     d  =      (
F4     2        e     d  ]      )
measure 38
F4     1        s     d  [[     (
Ef4    1        s     d  ==
D4     1        s     d  ==
C4     1        s     d  ]]
D4     1        s     d  [[     )
Bf3    1        s     d  ==
Ef4    1        s     d  ==     (
Bf3    1        s     d  ]]     )
F4     1        s     d  [[     (
Bf3    1        s     d  ==     )
G4     1        s     d  ==     (
Bf3    1        s     d  ]]     )
measure 39
Af4    1        s     d  [[     (+
G4     1        s     d  ==
F4     1        s     d  ==
Ef4    1        s     d  ]]
D4     1        s     d  [[     )
G3     1        s     d  ==
Af4    1        s     d  ==     (
G3     1        s     d  ]]     )
G4     1        s     d  [[     (
G3     1        s     d  ==     )
F4     1        s     d  ==     (
G3     1        s     d  ]]     )
measure 40
G4     1        s     d  [[     (
F4     1        s     d  ==
Ef4    1        s     d  ==
D4     1        s     d  ]]     )
C5     1        s     d  [[     (
Bf4    1        s     d  ==
Af4    1        s     d  ==
G4     1        s     d  ]]     )
D5     1        s     d  [[     (
C5     1        s     d  ==
B4     1        s n   d  ==
Af4    1        s     d  ]]     )+
measure 41
G4     1        s     d  [[     (
F4     1        s     d  ==
Ef4    1        s     d  ==
D4     1        s     d  ]]
Ef4    1        s     d  [[     )
C4     1        s     d  ==
G3     1        s     d  ==
C4     1        s     d  ]]
Ef4    1        s     d  [[
C4     1        s     d  ==
G3     1        s     d  ==
C4     1        s     d  ]]
measure 42
G4     1        s     d  [[     (
F4     1        s     d  ==
Ef4    1        s     d  ==
D4     1        s     d  ]]
Ef4    1        s     d  [[     )
C4     1        s     d  ==
A3     1        s n   d  ==
C4     1        s     d  ]]
Ef4    1        s     d  [[
C4     1        s     d  ==
A3     1        s     d  ==
C4     1        s     d  ]]
measure 43
D4     2        e     d
rest   2        e
rest   4        q
F4     4        q     d         f
measure 44
D5     1        s     d  [[     (
C5     1        s     d  ==
Bf4    1        s     d  ==
A4     1        s n   d  ]]
Bf4    1        s     d  [[     )
F4     1        s     d  ==
D4     1        s     d  ==
F4     1        s     d  ]]
Af4    1        s f   d  [[
F4     1        s     d  ==
D4     1        s     d  ==
F4     1        s     d  ]]
measure 45
G4     1        s     d  [[     (
F4     1        s     d  ==
Ef4    1        s     d  ==
D4     1        s     d  ]]
Ef4    1        s     d  [[     )
C5     1        s     d  ==
Ef4    1        s     d  ==     (
D4     1        s     d  ]]
Ef4    1        s     d  [[     )
C5     1        s     d  ==
Ef4    1        s     d  ==     (
D4     1        s     d  ]]
measure 46
Ef4    1        s     d  [[     )
D4     1        s     d  ==
C4     1        s     d  ==
D4     1        s     d  ]]
Ef4    1        s     d  [[     (
C4     1        s     d  ==     )
Ef4    1        s     d  ==     (
Bf3    1        s     d  ]]     )
Ef4    1        s     d  [[     (
A3     1        s n   d  ==     )
Ef4    1        s     d  ==     (
C4     1        s     d  ]]     )
measure 47
D4     1        s     d  [[     (
Bf3    1        s     d  ==     )
F4     1        s     d  ==     (
Bf3    1        s     d  ]]     )
G4     1        s     d  [[     (
Bf3    1        s     d  ==     )
Ef4    1        s     d  ==     (
Bf3    1        s     d  ]]     )
D4     1        s     u  [[     (
Bf3    1        s     u  ==     )
C4     1        s     u  ==     (
A3     1        s n   u  ]]     )
measure 48
Bf3    4-       q     u        -
Bf3    1        s     d  [[
C4     1        s     d  ==     (p
D4     1        s     d  ==
Ef4    1        s     d  ]]
F4     1        s     d  [[
G4     1        s     d  ==
Af4    1        s     d  ==
Bf4    1        s     d  ]]     )
measure 49
G3     1        s     d  [[     (
E4     1        s n   d  ==     )
Bf4    1        s     d  ==     (
E4     1        s     d  ]]     )
Bf4    1        s     d  [[     (
E4     1        s     d  ==     )
Bf4    1        s     d  ==     (
E4     1        s     d  ]]     )
G3     1        s     d  [[     (
E4     1        s     d  ==     )
Bf4    1        s     d  ==     (
E4     1        s     d  ]]     )
measure 50
Af3    1        s     u  [[
F4     1        s     u  ==
Af3    1        s     u  ==     (
G3     1        s     u  ]]
Af3    1        s     u  [[     )
F4     1        s     u  ==
Af3    1        s     u  ==     (
G3     1        s     u  ]]
Af3    1        s     u  [[     )
Bf3    1        s     u  ==
C4     1        s     u  ==
D4     1        s     u  ]]
measure 51
A3     1        s n   d  [[     (
Ef4    1        s     d  ==     )
C5     1        s     d  ==     (
Ef4    1        s     d  ]]     )
C5     1        s     d  [[     (
Ef4    1        s     d  ==     )
C5     1        s     d  ==     (
Ef4    1        s     d  ]]     )
A3     1        s     d  [[     (
Ef4    1        s     d  ==     )
C5     1        s     d  ==     (
Ef4    1        s     d  ]]     )
measure 52
Bf3    1        s     u  [[
D4     1        s     u  ==
Bf3    1        s     u  ==     (
A3     1        s n   u  ]]
Bf3    1        s     u  [[     )
D4     1        s     u  ==
Bf3    1        s     u  ==     (
P C33:u
A3     1        s     u  ]]
Bf3    1        s     d  [[     )
D4     1        s     d  ==     .
Ef4    1        s     d  ==     .
F4     1        s     d  ]]     .
measure 53
G4     1        s     d  [[     (
F4     1        s     d  ==
Ef4    1        s     d  ==
D4     1        s     d  ]]
Ef4    1        s     u  [[     )
Bf3    1        s     u  ==
G3     1        s     u  ==
Bf3    1        s     u  ]]
Ef4    1        s     u  [[
Bf3    1        s     u  ==
G3     1        s     u  ==
Bf3    1        s     u  ]]
measure 54
G4     1        s     d  [[     (
F4     1        s     d  ==
Ef4    1        s     d  ==
D4     1        s     d  ]]
Ef4    1        s     u  [[     )
C4     1        s     u  ==
G3     1        s     u  ==
C4     1        s     u  ]]
Ef4    1        s     u  [[
C4     1        s     u  ==
G3     1        s     u  ==
C4     1        s     u  ]]
measure 55
F4     1        s     d  [[     (
Ef4    1        s     d  ==
D4     1        s     d  ==     )
C4     1        s     d  ]]
Af4    1        s     d  [[     (
G4     1        s     d  ==
F4     1        s     d  ==     )
Ef4    1        s     d  ]]
D4     1        s     d  [[     .
C5     1        s     d  ==     (
Bf4    1        s     d  ==
Af4    1        s     d  ]]     )
measure 56
G4     1        s     d  [[     (
F4     1        s     d  ==
Ef4    1        s     d  ==
D4     1        s     d  ]]
Ef4    1        s     u  [[     )
Bf3    1        s     u  ==
G3     1        s     u  ==
Bf3    1        s     u  ]]
Ef4    1        s     d  [[     (
D4     1        s     d  ==     )
C4     1        s     d  ==     (
Bf3    1        s     d  ]]     )
measure 57
Af3    1        s     d  [[     (
F4     1        s     d  ==     )
D5     1        s     d  ==     (
F4     1        s     d  ]]     )
D5     1        s     d  [[     (
F4     1        s     d  ==     )
D5     1        s     d  ==     (
F4     1        s     d  ]]     )
Af3    1        s     d  [[     (
F4     1        s     d  ==     )
D5     1        s     d  ==     (
F4     1        s     d  ]]     )
measure 58
G3     1        s     d  [[     (
Ef4    1        s     d  ==     )
Df5    1        s f   d  ==     (
Ef4    1        s     d  ]]     )
Df5    1        s     d  [[     (
Ef4    1        s     d  ==     )
Df5    1        s     d  ==     (
Ef4    1        s     d  ]]     )
G3     1        s     d  [[     (
Ef4    1        s     d  ==     )
Df5    1        s     d  ==     (
Ef4    1        s     d  ]]     )
measure 59
G3     1        s     d  [[     (
E4     1        s n   d  ==     )
Bf4    1        s     d  ==     (
E4     1        s     d  ]]     )
Bf4    1        s     d  [[     (
E4     1        s     d  ==     )
Bf4    1        s     d  ==     (
E4     1        s     d  ]]     )
G3     1        s     d  [[     (
E4     1        s     d  ==     )
Bf4    1        s     d  ==     (
E4     1        s     d  ]]     )
measure 60
C4     1        s     d  [[
Af4    1        s     d  ==
C4     1        s     d  ==     (
Bf3    1        s     d  ]]
C4     1        s     d  [[     )
C5     1        s     d  ==
E4     1        s n   d  ==     (
D4     1        s     d  ]]
E4     1        s     d  [[     )
Df5    1        s f   d  ==     (
C5     1        s     d  ==
Bf4    1        s     d  ]]     )
measure 61
C5     1        s     d  [[     (
Bf4    1        s     d  ==
Af4    1        s     d  ==
G4     1        s     d  ]]
Af4    1        s     d  [[     )
F4     1        s     d  ==
C4     1        s     d  ==
F4     1        s     d  ]]
Af4    1        s     d  [[
F4     1        s     d  ==
C4     1        s     d  ==
F4     1        s     d  ]]
measure 62
C5     1        s     d  [[     (
Bf4    1        s     d  ==
Af4    1        s     d  ==
G4     1        s     d  ]]
Af4    1        s     d  [[     )
F4     1        s     d  ==
D4     1        s     d  ==
F4     1        s     d  ]]
Af4    1        s     d  [[
F4     1        s     d  ==
D4     1        s     d  ==
F4     1        s     d  ]]
measure 63
Bf4    2        e     d
rest   2        e
rest   4        q
rest   4        q
measure 64
rest   1        s
Ef5    1        s     d  [[     (f
D5     1        s     d  ==
C5     1        s     d  ]]
Bf4    1        s     d  [[
Af4    1        s     d  ==
G4     1        s     d  ==
F4     1        s     d  ]]
Ef4    1        s     d  [[
D4     1        s     d  ==
C4     1        s     d  ==
Bf3    1        s     d  ]]     )
measure 65
Af3    1        s     d  [[     (
F4     1        s     d  ==     )
D5     1        s     d  ==     (
F4     1        s     d  ]]     )
D5     1        s     d  [[     (
F4     1        s     d  ==     )
D5     1        s     d  ==     (
F4     1        s     d  ]]     )
Af3    1        s     d  [[     (
F4     1        s     d  ==     )
D5     1        s     d  ==     (
F4     1        s     d  ]]     )
measure 66
G3     1        s     d  [[     (
Ef4    1        s     d  ==     )
Df5    1        s f   d  ==     (
Ef4    1        s     d  ]]     )
Df5    1        s     d  [[     (
Ef4    1        s     d  ==     )
Df5    1        s     d  ==     (
Ef4    1        s     d  ]]     )
G3     1        s     d  [[     (
Ef4    1        s     d  ==     )
Df5    1        s     d  ==     (
Ef4    1        s     d  ]]     )
measure 67
Af3    1        s     d  [[     (
Ef4    1        s     d  ==     )
C5     1        s     d  ==     (
Bf4    1        s     d  ]]
Af4    1        s     d  [[
G4     1        s     d  ==
F4     1        s     d  ==
Ef4    1        s     d  ]]     )
Bf3    1        s     d  [[     .
Ef4    1        s     d  ==     .
F4     1        s     d  ==     .
D4     1        s     d  ]]     .
measure 68
Ef4    4        q     d         F
S C8:F4
rest   4        q
rest   4        q
measure 69
rest   4        q
Ef4    1        s     d  [[     (p
D4     1        s     d  ==
C4     1        s     d  ==
B3     1        s n   d  ]]     )
C4     4-       q     d        -
measure 70
C4     4        q     d
Ef4    1        s     d  [[     (
D4     1        s     d  ==
C4     1        s     d  ==
B3     1        s n   d  ]]     )
C4     4-       q     d        -
measure 71
C4     4        q     d
Af4    1        s     d  [[     (
G4     1        s     d  ==
F4     1        s     d  ==
Ef4    1        s     d  ]]     )
F4     4-       q     d        -
measure 72
F4     2        e     d  [      (
G4     1        s     d  =[
Af4    1        s     d  ]]     )
G4     1        s     d  [[     (
F4     1        s     d  ==
Ef4    1        s     d  ==
D4     1        s     d  ]]
C4     1        s     u  [[
B3     1        s n   u  ==
A3     1        s n   u  ==
G3     1        s     u  ]]     )
measure 73
Ef4    1        s     d  [[     (
D4     1        s     d  ==
C4     1        s     d  ==
B3     1        s n   d  ]]     )
C4     8-       h     d        -
measure 74
C4     1        s     u  [[
Bf3    1        s     u  ==     (
A3     1        s n   u  ==
G3     1        s     u  ]]     )
A3     8-       h     u        -
measure 75
A3     1        s     d  [[
Ef4    1        s     d  ==     (
D4     1        s     d  ==
C4     1        s     d  ]]     )
A4     1        s n   d  [[     (
G4     1        s     d  ==
F#4    1        s #   d  ==
E4     1        s n   d  ]]     )
C5     4-       q     d        -
measure 76
C5     1        s     d  [[     (
Bf4    1        s     d  ==
A4     1        s n   d  ==
G4     1        s     d  ]]
A4     1        s     d  [[
G4     1        s     d  ==
F#4    1        s #   d  ==
Ef4    1        s     d  ]]
D4     1        s     u  [[
C4     1        s     u  ==
Bf3    1        s     u  ==
A3     1        s n   u  ]]     )
measure 77
G3     8        h     u
Ef4    1        s     d  [[     (
D4     1        s     d  ==
C4     1        s     d  ==
Bf3    1        s     d  ]]     )
measure 78
A3     8        h n   u
F4     1        s     d  [[     (
Ef4    1        s     d  ==
D4     1        s     d  ==
C4     1        s     d  ]]     )
measure 79
Bf3    8        h     u
G4     1        s     d  [[     (
F4     1        s     d  ==
Ef4    1        s     d  ==
D4     1        s     d  ]]     )
measure 80
C4    12-       h.    d        -(
measure 81
C4     1        s     d  [[
F#4    1        s #   d  ==     )
A4     1        s n   d  ==     (
F#4    1        s     d  ]]     )
A4     1        s     d  [[     (
F#4    1        s     d  ==     )
A4     1        s     d  ==     (
F#4    1        s     d  ]]     )
C4     1        s     d  [[     (
F#4    1        s     d  ==     )
A4     1        s     d  ==     (
F#4    1        s     d  ]]     )
measure 82
C4     1        s     d  [[     (
Ef4    1        s     d  ==     )+
A4     1        s n   d  ==     (
Ef4    1        s     d  ]]     )
A4     1        s     d  [[     (
Ef4    1        s     d  ==     )
A4     1        s     d  ==     (
Ef4    1        s     d  ]]     )
C4     1        s     d  [[     (
D4     1        s     d  ==     )
A4     1        s     d  ==     (
D4     1        s     d  ]]     )
measure 83
Bf3    2        e     u
rest   2        e
rest   4        q
rest   4        q
measure 84
rest   2        e
D5     1        s     d  [[     (f
C5     1        s     d  ]]
Bf4    1        s     d  [[
A4     1        s n   d  ==
G4     1        s     d  ==
F4     1        s     d  ]]
Ef4    1        s     d  [[
D4     1        s     d  ==
C4     1        s     d  ==
Bf3    1        s     d  ]]     )
measure 85
A3     1        s n   d  [[     (
G4     1        s     d  ==     )
C5     1        s     d  ==     (
G4     1        s     d  ]]     )
C5     1        s     d  [[     (
G4     1        s     d  ==     )
C5     1        s     d  ==     (
G4     1        s     d  ]]     )
A3     1        s     d  [[     (
G4     1        s     d  ==     )
C5     1        s     d  ==     (
G4     1        s     d  ]]     )
measure 86
A3     1        s n   d  [[     (
F#4    1        s #   d  ==     )
C5     1        s     d  ==     (
F#4    1        s     d  ]]     )
C5     1        s     d  [[     (
F#4    1        s     d  ==     )
C5     1        s     d  ==     (
F#4    1        s     d  ]]     )
A3     1        s     d  [[     (
F#4    1        s     d  ==     )
C5     1        s     d  ==     (
F#4    1        s     d  ]]     )
measure 87
G3     1        s     d  [[     (
D4     1        s     d  ==     )
Bf4    1        s     d  ==     (
A4     1        s n   d  ]]     )
C5     1        s     d  [[     (
Bf4    1        s     d  ==     )
A4     1        s     d  ==     (
G4     1        s     d  ]]     )
D4     1        s     d  [[     .
G4     1        s     d  ==     .
A4     1        s     d  ==     .
F#4    1        s #   d  ]]     .
measure 88
G4     1        s     d  [[
C4     1        s     d  ==     (
Bf3    1        s     d  ==
A3     1        s n   d  ]]     )
G3     1        s     u  [[     (p
A3     1        s     u  ==
Bf3    1        s     u  ==
C4     1        s     u  ]]
D4     1        s     d  [[
F#4    1        s #   d  ==
G4     1        s     d  ==
A4     1        s n   d  ]]     )
measure 89
Bf4    1        s     d  [[     (
A4     1        s     d  ==
&
Af4  in the BG edition (a possible error)
&
G4     1        s     d  ==
F#4    1        s #   d  ]]
G4     1        s     d  [[     )
D4     1        s     d  ==
Bf3    1        s     d  ==
D4     1        s     d  ]]
G4     1        s     d  [[
D4     1        s     d  ==
Bf3    1        s     d  ==
D4     1        s     d  ]]
measure 90
Bf4    1        s     d  [[     (
A4     1        s     d  ==
&
Af4  in the BG edition (a possible error)
&
G4     1        s     d  ==
F#4    1        s #   d  ]]
G4     1        s     d  [[     )
D4     1        s     d  ==
Bf3    1        s     d  ==
D4     1        s     d  ]]
G4     1        s     d  [[
D4     1        s     d  ==
Bf3    1        s     d  ==
D4     1        s     d  ]]
measure 91
G4     1        s     d  [[     (
F4     1        s     d  ==
E4     1        s n   d  ==
D4     1        s     d  ]]     )
Bf4    1        s     d  [[     (
Af4    1        s     d  ==     +
G4     1        s     d  ==
F4     1        s     d  ]]
E4     1        s     d  [[
D4     1        s     d  ==
C4     1        s     d  ==
Bf3    1        s     d  ]]     )
measure 92
Af3    4-       q     u        -
Af3    1        s     d  [[
C4     1        s     d  ==     (
D4     1        s     d  ==
E4     1        s n   d  ]]     )
F4     1        s     d  [[     (
E4     1        s     d  ==
D4     1        s     d  ==     )
C4     1        s     d  ]]
measure 93
Af4    1        s     d  [[     (
G4     1        s     d  ==
F4     1        s     d  ==
E4     1        s n   d  ]]     )
F4     8-       h     d        -
measure 94
F4     1        s     d  [[
Ef4    1        s     d  ==     (+
D4     1        s     d  ==
C4     1        s     d  ]]     )
D4     8-       h     d        -
measure 95
D4     1        s     u  [[
C4     1        s     u  ==     (
B3     1        s n   u  ==
A3     1        s n   u  ]]     )
G3     4        q     u
rest   4        q
measure 96
rest   1        s
Ef5    1        s     d  [[     (
D5     1        s     d  ==
C5     1        s     d  ]]     )
D5     1        s     d  [[     (
C5     1        s     d  ==
B4     1        s n   d  ==
Af4    1        s     d  ]]      +
G4     1        s     d  [[
F4     1        s     d  ==
Ef4    1        s     d  ==
D4     1        s     d  ]]     )
measure 97
C4     4-       q     d        -
C4     1        s     u  [[
Bf3    1        s     u  ==     (
Af3    1        s     u  ==
G3     1        s     u  ]]     )
F4     4-       q     d        -
measure 98
F4     1        s     d  [[
Bf4    1        s     d  ==     (
Af4    1        s     d  ==
G4     1        s     d  ]]     )
Bf3    1        s     d  [[
Af4    1        s     d  ==     (
G4     1        s     d  ==
F4     1        s     d  ]]     )
Ef4    4-       q     d        -
measure 99
Ef4    1        s     d  [[
Af4    1        s     d  ==     (
G4     1        s     d  ==
F4     1        s     d  ]]     )
Af3    1        s     d  [[
G4     1        s     d  ==     (
F4     1        s     d  ==
Ef4    1        s     d  ]]     )
D4     4-       q     d        -
measure 100
D4     1        s     d  [[
G4     1        s     d  ==     (
F4     1        s     d  ==
Ef4    1        s     d  ]]
F4     1        s     d  [[
Ef4    1        s     d  ==
F4     1        s     d  ==
G4     1        s     d  ]]     )
Af4    4-       q     d        -
measure 101
Af4    1        s     d  [[     (
F4     1        s     d  ==     )
D5     1        s     d  ==     (
F4     1        s     d  ]]     )
D5     1        s     d  [[     (
F4     1        s     d  ==     )
D5     1        s     d  ==     (
F4     1        s     d  ]]     )
Af3    1        s     d  [[     (
F4     1        s     d  ==     )
D5     1        s     d  ==     (
F4     1        s     d  ]]     )
measure 102
G3     1        s     d  [[     (
F4     1        s     d  ==     )
D5     1        s     d  ==     (
F4     1        s     d  ]]     )
D5     1        s     d  [[     (
F4     1        s     d  ==     )
D5     1        s     d  ==     (
F4     1        s     d  ]]     )
G3     1        s     d  [[     (
F4     1        s     d  ==     )
D5     1        s     d  ==     (
F4     1        s     d  ]]     )
measure 103
C5     2        e     d
 Ef4            e     d
 G3             e     d
rest   2        e
rest   4        q
rest   4        q
measure 104
rest   4        q
rest   1        s
Ef5    1        s     d  [[     (f
D5     1        s     d  ==
C5     1        s     d  ]]
Bf4    1        s     d  [[
Af4    1        s     d  ==
G4     1        s     d  ==
F4     1        s     d  ]]     )
*               B   39  Dal Segno
mheavy2         A
S C0:d
/END
/eof
&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
PART = 02
&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
(C) 1991, 2002 Center for Computer Assisted Research in the Humanities.
ID: {bach/bg/cant/0005/stage2/03/02} [KHM:1658122244]
TIMESTAMP: DEC/26/2001 [md5sum:bcce96553293672b44f5aeb074066fe8]
03/06/91 S. Rasmussen
WK#:5         MV#:3
Bach Gesellschaft i
Wo soll ich fliehen hin
Aria
TENORE
1 75 T
Group memberships: score
score: part 2 of 3
&
conversion from old-format Stage2 to new-format Stage2
S. Rasmussen    09/02/93
&
$ K:-3   Q:8   T:3/4   C:34
rest   8        q
measure 1       A
S C0:S8
rest  24
measure 2
rest  24
measure 3
rest  24
measure 4
rest  24
measure 5
rest  24
measure 6
rest  24
measure 7
rest  24
measure 8
rest  24
measure 9
rest  24
measure 10
rest  24
measure 11
rest  24
measure 12
rest  24
measure 13
rest  24
measure 14
rest  24
measure 15
rest  24
measure 16
rest   8        q
rest   8        q
Bf3    8        q     d                    Er-
measure 17
G4     2        s     d  [[                gie-
F4     2        s     d  ==                -
Ef4    2        s     d  ==                -
D4     2        s     d  =]                -
Ef4    4        e     d  ]                 -
Bf3    4        e     d                    sse
G3     4        e     u  [                 dich_
Bf3    4        e     u  ]                 _
measure 18
G4     2        s     d  [[                reich-
F4     2        s     d  ==                -
Ef4    2        s     d  ==                -
D4     2        s     d  =]                -
Ef4    4        e     d  ]                 -
C4     4        e     d                    lich
G3     4        e     u  [                 du_
C4     4        e     u  ]                 _
measure 19
F4    12        q.    d                    g\3ott-
G4     4        e     d                    li-
Af4    4        e     d  [                 che_
D4     4        e     d  ]                 _
measure 20
Bf3    4        e     d  [                 Quel-
Af4    4        e     d  ]                 -
G4     8        q     d                    le.
rest   8        q
measure 21
rest  24
measure 22
rest  24
measure 23
rest  24
measure 24
rest   8        q
rest   8        q
Bf3    8        q     d                    Er-
measure 25
G4     2        s     d  [[                gie-
F4     2        s     d  ==                -
Ef4    2        s     d  ==                -
D4     2        s     d  =]                -
Ef4    4        e     d  ]                 -
Bf3    4        e     d                    sse
G3     4        e     u  [                 dich_
Bf3    4        e     u  ]                 _
measure 26
G4     2        s     d  [[                reich-
F4     2        s     d  ==                -
Ef4    2        s     d  ==                -
D4     2        s     d  =]                -
Ef4    4        e     d  ]                 -
C4     4        e     d                    lich
G3     4        e     u  [                 du_
C4     4        e     u  ]                 _
measure 27
F4    12        q.    d                    g\3ott-
G4     4        e     d                    li-
Af4    4        e     d  [                 che_
D4     4        e     d  ]                 _
measure 28
Bf3    4        e     d  [                 Quel-
Af4    4        e     d  ]                 -
G4     8        q     d                    le,
F4     8        q     d                    ach
measure 29
F4     2        s     d  [[                wal-
Ef4    2        s     d  ==                -
D4     2        s     d  ==                -
C4     2        s     d  ]]                -
D4     2        s     d  [[                -
C4     2        s     d  ==                -
Bf3    2        s     d  ==                -
Af3    2        s     d  ]]                -
G4     2        s     d  [[                -
F4     2        s     d  ==                -
Ef4    2        s     d  ==                -
D4     2        s     d  ]]                -
measure 30
Ef4    2        s     d  [[                -
D4     2        s     d  ==                -
C4     2        s     d  ==                -
Bf3    2        s     d  ]]                -
C4     2        s     u  [[                -
Bf3    2        s     u  ==                -
A3     2        s n   u  ==                -
G3     2        s     u  ]]                -
F4     2        s     d  [[                -
Ef4    2        s     d  ==                -
D4     2        s     d  ==                -
C4     2        s     d  ]]                -
measure 31
D4     2        s     d  [[                -
C4     2        s     d  ==                -
Bf3    2        s     d  ==                -
A3     2        s     d  ]]                -
&
Af3 in the BG edition (an obvious error)
&
Bf3    2        s     u  [[                -
A3     2        s n   u  ==                -
G3     2        s     u  ==                -
F3     2        s     u  ]]                -
Ef4    2        s     d  [[                -
D4     2        s     d  ==                -
C4     2        s     d  ==                -
Bf3    2        s     d  ]]                -
measure 32
A3     2        s n   d  [[                -
Bf3    2        s     d  ==                -
C4     2        s     d  ==                -
A3     2        s     d  ]]                -
F3     8        q     u                    le,
C4     4        e     d  [                 ach_
D4     2        s     d  =[                _
Ef4    2        s     d  ]]                _
measure 33
D4     4        e     d  [                 wal-
Ef4    2        s     d  =[                -
F4     2        s     d  ]]                -
F4     4        e     d  [                 le_
Ef4    4        e     d  ]                 _
D4     4        e     d  [                 mit_
C4     4        e     d  ]                 _
measure 34
D4     4        e     d  [                 blu-
Ef4    2        s     d  =[                -
F4     2        s     d  ]]                -
F4     4        e     d  [                 ti-
Ef4    4        e     d  ]                 -
D4     4        e     d  [                 gen_
Ef4    2        s     d  =[                _
F4     2        s     d  ]]                _
measure 35
G3     4        e     d  [                 Str\3o-
G4     4-       e     d  ]     -           -
G4     2        s     d  [[                -
F4     2        s     d  ==                -
Ef4    2        s     d  ==                -
D4     2        s     d  ]]                -
F4     2        s     d  [[                -
Ef4    2        s     d  ==                -
D4     2        s     d  ==                -
C4     2        s     d  ]]                -
measure 36
F4     2        s     d  [[                -
G4     2        s     d  ==                -
F4     2        s     d  ==                -
Ef4    2        s     d  ]]                -
D4     2        s     d  [[                -
C4     2        s     d  ==                -
Bf3    2        s     d  ==                -
A3     2        s n   d  ]]                -
C4     2        s     u  [[                -
Bf3    2        s     u  ==                -
A3     2        s     u  ==                -
G3     2        s     u  ]]                -
measure 37
Ef4    2        s     d  [[                -
F4     2        s     d  ==                -
Ef4    2        s     d  ==                -
D4     2        s     d  ]]                -
C4     2        s     u  [[                -
Bf3    2        s     u  ==                -
A3     2        s n   u  ==                -
G3     2        s     u  ]]                -
Bf3    2        s     u  [[                -
A3     2        s     u  ==                -
G3     2        s     u  ==                -
F3     2        s     u  ]]                -
measure 38
D4     4        e     d  [                 -
C4     4        e     d  ]                 -
Bf3    4        e     d  [                 men,_
C4     4        e     d  ]                 _
D4     4        e     d  [                 mit_
Ef4    4        e     d  ]                 _
measure 39
F4     4        e     d  [                 blu-
G4     2        s     d  =[                -
Af4    2        s     d  ]]     +          -
G4     4        e     d  [                 ti-
F4     4        e     d  ]                 -
Ef4    4        e     d  [                 gen_
D4     4        e     d  ]                 _
measure 40
F4     4        e     d  [                 Str\3o-
Ef4    4        e     d  ]                 -
D4     4        e     d  [                 men,_
C4     4        e     d  ]                 _
G3     8        q     u                    ach
measure 41
Ef4    2        s     d  [[                wal-
D4     2        s     d  ==                -
C4     2        s     d  ==                -
Bf3    2        s     d  =]                -
C4     4        e     d  ]                 -
G3     4        e     u                    le
G4     4        e     d                    mit
Ef4    4-       e     d        -           blu-
measure 42
Ef4    2        s     d  [[                -
D4     2        s     d  ==                -
C4     2        s     d  ==                -
Bf3    2        s     d  =]                -
C4     4        e     d  ]                 -
Ef4    4        e     d                    ti-
G4     4        e     d  [                 gen_
F4     4        e     d  ]                 _
measure 43
F4     4        e     d  [                 Str\3o-
G4     2        s     d  =[                -
F4     2        s     d  ]]                -
Ef4    2        s     d  [[                -
D4     2        s     d  ==                -
C4     2        s     d  ==                -
Bf3    2        s     d  =]                -
Ef4    4        e     d  ]                 -
D4     2        s     d                    men
C4     2        s     d                    auf
measure 44
Bf3    8        q     d                    mich.
rest   8        q
rest   8        q
measure 45
rest  24
measure 46
rest  24
measure 47
rest  24
measure 48
rest   8        q
rest   8        q
Bf3    8        q     d                    Er-
measure 49
Df4    2        s f   d  [[                gie-
C4     2        s     d  ==                -
Bf3    2        s     d  ==                -
Af3    2        s     d  =]                -
Bf3    4        e     d  ]                 -
G3     4        e     u                    sse
F4     4        e     d  [                 dich_
E4     4        e n   d  ]                 _
measure 50
F4     8        q     d                    reich-
F3     4        e     u  [                 lich_
Af3    4        e     u  ]                 _
C4     4        e     d  [                 du_
Ef4    2        s     d  =[                _
D4     2        s     d  ]]                _
measure 51
Ef4    2        s     d  [[                g\3ott-
D4     2        s     d  ==                -
C4     2        s     d  ==                -
D4     2        s     d  =]                -
Ef4    4        e     d  ]                 -
G4     4        e     d                    li-
F4     8        q     d                    che
measure 52
F4     2        s     d  [[                Quel-
Ef4    2        s     d  ==                -
D4     2        s     d  ==                -
C4     2        s     d  =]                -
D4     4        e     d  ]                 -
Bf3    4        e     d                    le,
F4     6        e.    d  [                 er-
G4     1        t     d  =[[               -
Af4    1        t     d  ]]]               -
measure 53
G4     2        s     d  [[                gie-
F4     2        s     d  ==                -
Ef4    2        s     d  ==                -
D4     2        s     d  =]                -
Ef4    4        e     d  ]                 -
Bf3    4        e     d                    sse
G3     4        e     u  [                 dich_
Bf3    4        e     u  ]                 _
measure 54
G4     2        s     d  [[                reich-
F4     2        s     d  ==                -
Ef4    2        s     d  ==                -
D4     2        s     d  =]                -
Ef4    4        e     d  ]                 -
C4     4        e     d                    lich
G3     4        e     u  [                 du_
C4     4        e     u  ]                 _
measure 55
F4    12        q.    d                    g\3ott-
G4     4        e     d                    li-
Af4    4        e     d  [                 che_
D4     4        e     d  ]                 _
measure 56
Bf3    4        e     d  [                 Quel-
Af4    4        e     d  ]                 -
G4     8        q     d                    le,
Bf3    8        q     d                    ach
measure 57
F3     2        s     u  [[                wal-
G3     2        s     u  =]                -
Af3    4        e     u  ]                 -
Af3    4        e     u  [                 le_
G3     4        e     u  ]                 _
Af3    4        e     u  [                 mit_
F3     4        e     u  ]                 _
measure 58
G3     2        s     u  [[                blu-
Af3    2        s     u  =]                -
Bf3    4        e     u  ]                 -
Bf3    4        e     u  [                 ti-
Af3    4        e     u  ]                 -
G3     4        e     u                    gen,
Af3    4        e     u                    mit
measure 59
Bf3    2        s     d  [[                blu-
C4     2        s     d  =]                -
Df4    4        e f   d  ]                 -
C4     4        e     d  [                 ti-
Bf3    4        e     d  ]                 -
Af3    4        e     u  [                 gen_
G3     4        e     u  ]                 _
measure 60
Bf3    4        e     u  [                 Str\3o-
Af3    4        e     u  ]                 -
G3     4        e     u  [                 men,_
F3     4        e     u  ]                 _
C4     8        q     d                    ach
measure 61
Af4    2        s     d  [[                wal-
G4     2        s     d  ==                -
F4     2        s     d  ==                -
Ef4    2        s     d  =]                -
F4     4        e     d  ]                 -
C4     4        e     d                    le
Af3    4        e     d  [                 mit_
C4     4        e     d  ]                 _
measure 62
Af4    2        s     d  [[                blu-
G4     2        s     d  ==                -
F4     2        s     d  ==                -
Ef4    2        s     d  =]                -
F4     4        e     d  ]                 -
Af3    4        e     u                    ti-
C4     4        e     d  [                 gen_
Bf3    4        e     d  ]                 _
measure 63
Bf3    4        e     d  [                 Str\3o-
C4     2        s     d  =[                -
Bf3    2        s     d  ]]                -
Af3    2        s     u  [[                -
G3     2        s     u  ==                -
F3     2        s     u  ==                -
Ef3    2        s     u  =]                -
Af3    4        e     u  ]                 -
G3     2        s     u                    men
F3     2        s     u                    auf
measure 64
Ef3    8        q     u                    mich.
rest   8        q
rest   8        q
measure 65
rest  24
measure 66
rest  24
measure 67
rest  24
measure 68
rest   8        q               F
S C8:F8
rest   8        q
G3     8        q     u                    Es
measure 69
Ef4    2        s     d  [[                f\3uh-
D4     2        s     d  ==                -
C4     2        s     d  ==                -
B3     2        s n   d  =]                -
C4     4        e     d  ]                 -
G3     4        e     u                    let
Ef3    4        e     u  [                 mein_
G3     4        e     u  ]                 _
measure 70
Ef4    2        s     d  [[                Her-
D4     2        s     d  ==                -
C4     2        s     d  ==                -
B3     2        s n   d  =]                -
C4     4        e     d  ]                 -
G3     4        e     u                    ze
Ef4    4        e     d  [                 die_
D4     4        e     d  ]                 _
measure 71
D4     4        e     d  [                 tr\3ost-
Af4    2        s     d  =[                -
G4     2        s     d  ]]                -
F4     2        s     d  [[                -
Ef4    2        s     d  ==                -
D4     2        s     d  ==                -
C4     2        s     d  =]                -
D4     4        e     d  ]                 -
Ef4    2        s     d                    li-
F4     2        s     d                    che
measure 72
B3     8        q n   d                    Stun-
A3     4        e n   u  [                 de,_
G3     4        e     u  ]                 _
G4     8        q     d                    nun
measure 73
G4     8-       q     d        -           sin-
G4     2        s     d  [[                -
F4     2        s     d  ==                -
Ef4    2        s     d  ==                -
D4     2        s     d  =]                -
Ef4    4        e     d  ]                 -
F4     2        s     d                    ken
D4     2        s     d                    die
measure 74
Ef4    8-       q     d        -           dr\3u-
Ef4    2        s     d  [[                -
D4     2        s     d  ==                -
C4     2        s     d  ==                -
Bf3    2        s     d  =]                -
C4     4        e     d  ]                 -
D4     2        s     d                    cken-
Bf3    2        s     d                    den
measure 75
C4     8-       q     d        -           La-
C4     2        s     u  [[                -
Bf3    2        s     u  ==                -
A3     2        s n   u  ==                -
G3     2        s     u  =]                -
A3     4        e     u  ]                 -
Bf3    2        s     d                    sten
G3     2        s     u                    zu
measure 76
F#3    8        q #   u         t          Grun-
S C33:uhn8s15t75
E3     4        e n   u  [                 de,_
D3     4        e     u  ]                 _
A3     8        q n   u                    es
measure 77
C4     2        s     u  [[                w\3a-
Bf3    2        s     u  ==                -
A3     2        s n   u  ==                -
G3     2        s     u  ]]                -
Ef4    2        s     d  [[                -
D4     2        s     d  ==                -
C4     2        s     d  ==                -
Bf3    2        s     d  ]]                -
C4     2        s     u  [[                -
Bf3    2        s     u  ==                -
A3     2        s     u  ==                -
G3     2        s     u  ]]                -
measure 78
D4     2        s     d  [[                -
C4     2        s     d  ==                -
Bf3    2        s     d  ==                -
A3     2        s n   d  ]]                -
F4     2        s     d  [[                -
Ef4    2        s     d  ==                -
D4     2        s     d  ==                -
C4     2        s     d  ]]                -
D4     2        s     d  [[                -
C4     2        s     d  ==                -
Bf3    2        s     d  ==                -
A3     2        s     d  ]]                -
measure 79
Ef4    2        s     d  [[                -
D4     2        s     d  ==                -
C4     2        s     d  ==                -
Bf3    2        s     d  ]]                -
G4     2        s     d  [[                -
F4     2        s     d  ==                -
Ef4    2        s     d  ==                -
D4     2        s     d  ]]                -
Ef4    2        s     d  [[                -
D4     2        s     d  ==                -
C4     2        s     d  ==                -
Bf3    2        s     d  ]]                -
measure 80
F4     2        s     d  [[                -
Ef4    2        s     d  ==                -
D4     2        s     d  ==                -
C4     2        s     d  ]]                -
A4     2        s n   d  [[                -
G4     2        s     d  ==                -
F#4    2        s #   d  ==                -
E4     2        s     d  ]]                -
F#4    2        s n   d  [[                -
E4     2        s     d  ==                -
&
Ef4  \
F4     in the BG edition (a probable error)
Ef4  /
&
D4     2        s     d  ==                -
C4     2        s     d  ]]                -
measure 81
D4    12        q.    d                    -
Ef4    4        e     d                    schet
D4     8        q     d                    die
measure 82
F#3    4        e #   u  [                 s\3und-
A3     4        e     u  =                 -
&
Af3  in the BG edition (a probable error)
&
C4     4        e     u  ]                 -
Ef4    4        e     d                    li-
D4     8        q     d                    chen
measure 83
D4     4        e     d  [                 Fle-
Ef4    2        s     d  =[                -
D4     2        s     d  ]]                -
C4     2        s     d  [[                -
Bf3    2        s     d  ==                -
A3     2        s n   d  ==                -
G3     2        s     d  =]                -
C4     4        e     d  ]                 -
Bf3    2        s     d                    cken
A3     2        s     u                    von
measure 84
gA3    6        e n   u         (
S C1:ft50
G3     8        q     u         )          sich.
rest   8        q
rest   8        q
measure 85
rest  24
measure 86
rest  24
measure 87
rest  24
measure 88
rest   8        q
rest   8        q
D4     8        q     d                    Es
measure 89
D4     2        s     d  [[                f\3uh-
C4     2        s     d  ==                -
Bf3    2        s     d  ==                -
A3     2        s n   d  =]                -
Bf3    4        e     d  ]                 -
G3     4        e     u                    let
D4     8        q     d                    mein
measure 90
D4     2        s     d  [[                Her-
C4     2        s     d  ==                -
Bf3    2        s     d  ==                -
A3     2        s n   d  =]                -
Bf3    4        e     d  ]                 -
G3     4        e     u                    ze
D4     4        e     d  [                 die_
E4     2        s n   d  =[                _
F4     2        s     d  ]]                _
measure 91
E4     2        s n   d  [[                tr\3ost-
F4     2        s     d  =]                -
G4     4-       e     d  ]     -           -
G4     2        s     d  [[                -
F4     2        s     d  ==                -
E4     2        s     d  ==                -
D4     2        s     d  =]                -
C4     4        e     d  ]                 -
D4     2        s     d                    li-
E4     2        s     d                    che
measure 92
F4     4        e     d  [                 Stun-
G4     2        s     d  =[                -
Af4    2        s     d  ]]                -
Af4    8        q     d                    de,
C4     8        q     d                    nun
measure 93
C4     8-       q     d        -           sin-
C4     2        s     u  [[                -
Bf3    2        s     u  ==                -
Af3    2        s     u  ==                -
G3     2        s     u  =]                -
Af3    4        e     u  ]                 -
Bf3    2        s     d                    ken
G3     2        s     u                    die
measure 94
Af3    4        e     d  [                 dr\3u-
Af4    4-       e     d  ]     -           -
Af4    2        s     d  [[                -
F4     2        s     d  ==                -
G4     2        s     d  ==                -
Ef4    2        s     d  =]                -
F4     4        e     d  ]                 -
G4     2        s     d                    cken-
Ef4    2        s     d                    den
measure 95
F4     8-       q     d        -           La-
F4     2        s     d  [[                -
Ef4    2        s     d  ==                -
D4     2        s     d  ==                -
C4     2        s     d  =]                -
D4     4        e     d  ]                 -
Ef4    2        s     d                    sten
C4     2        s     d                    zu
measure 96
B3     8        q n   d                    Grun-
A3     4        e n   u  [                 de,_
G3     4        e     u  ]                 _
D4     8        q     d                    es
measure 97
F4     2        s     d  [[                w\3a-
Ef4    2        s     d  ==                -
D4     2        s     d  ==                -
C4     2        s     d  ]]                -
Af4    2        s     d  [[                -
G4     2        s     d  ==                -
F4     2        s     d  ==                -
Ef4    2        s     d  ]]                -
F4     2        s     d  [[                -
Ef4    2        s     d  ==                -
D4     2        s     d  ==                -
C4     2        s     d  ]]                -
measure 98
Ef4    2        s     d  [[                -
D4     2        s     d  ==                -
C4     2        s     d  ==                -
Bf3    2        s     d  ]]                -
G4     2        s     d  [[                -
F4     2        s     d  ==                -
Ef4    2        s     d  ==                -
D4     2        s     d  ]]                -
Ef4    2        s     d  [[                -
D4     2        s     d  ==                -
C4     2        s     d  ==                -
Bf3    2        s     d  ]]                -
measure 99
Df4    2        s f   d  [[                -
C4     2        s     d  ==                -
Bf3    2        s     d  ==                -
Af3    2        s     d  ]]                -
F4     2        s     d  [[                -
Ef4    2        s     d  ==                -
D4     2        s n   d  ==                -
C4     2        s     d  ]]                -
D4     2        s     d  [[                -
C4     2        s     d  ==                -
B3     2        s n   d  ==                -
A3     2        s n   d  ]]                -
measure 100
C4     2        s     u  [[                -
B3     2        s n   u  ==                -
A3     2        s n   u  ==                -
G3     2        s     u  ]]                -
D4     2        s     d  [[                -
C4     2        s     d  ==                -
B3     2        s     d  ==                -
A3     2        s     d  ]]                -
Ef4    2        s     d  [[                -
D4     2        s     d  ==                -
C4     2        s     d  ==                -
B3     2        s     d  ]]                -
measure 101
F4    12        q.    d                    -
G4     4        e     d                    schet
F4     8        q     d                    die
measure 102
B3     4        e n   d  [                 s\3und-
D4     4        e     d  =                 -
F4     4        e     d  ]                 -
Af4    4        e     d                    li-
G4     8        q     d                    chen
measure 103
G4     4        e     d  [                 Fle-
Af4    2        s     d  =[                -
G4     2        s     d  ]]                -
F4     2        s     d  [[                -
Ef4    2        s     d  ==                -
D4     2        s     d  ==                -
C4     2        s     d  =]                -
F4     4        e     d  ]                 -
Ef4    2        s     d                    cken
D4     2        s     d                    von
measure 104
C4     8        q     d                    sich.
rest   8        q
rest   8        q
*               B   39  Dal Segno
mheavy2         A
S C0:d
/END
/eof
&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
PART = 03
&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
(C) 1991, 2002 Center for Computer Assisted Research in the Humanities.
ID: {bach/bg/cant/0005/stage2/03/03} [KHM:1658122244]
TIMESTAMP: DEC/26/2001 [md5sum:d3a30662b48731ae35e243eb82937a72]
03/06/91 S. Rasmussen
WK#:5         MV#:3
Bach Gesellschaft i
Wo soll ich fliehen hin
Aria
Continuo
1 75
Group memberships: score
score: part 3 of 3
&
conversion from old-format Stage2 to new-format Stage2
S. Rasmussen    09/02/93
&
$ K:-3   Q:4   T:3/4   C:22
rest   4        q
measure 1       A
S C0:S4
Ef2    2        e     u  [
Ef3    2        e     u  =
Ef3    2        e     u  =      (
D3     2        e     u  =      )
D3     2        e     u  =      (
C3     2        e     u  ]      )
measure 2
C2     2        e     u  [
C3     2        e     u  =
C3     2        e     u  =      (
Bf2    2        e     u  =      )
Bf2    2        e     u  =      (
Af2    2        e     u  ]      )
measure 3
Af2    2        e     u
rest   2        e
F2     2        e     u
rest   2        e
Bf2    2        e     u
rest   2        e
measure 4
Ef2    2        e     u  [
Ef3    2        e     u  =
Ef3    2        e     u  =      (
D3     2        e     u  =      )
D3     2        e     u  =      (
C3     2        e     u  ]      )
measure 5
C3     2        e     d  [
C4     2        e     d  =
C4     2        e     d  =      (
Bf3    2        e     d  =      )
Bf3    2        e     d  =      (
A3     2        e n   d  ]      )
measure 6
A2     2        e n   d  [
A3     2        e n   d  =
A3     2        e     d  =      (
G3     2        e     d  =      )
G3     2        e     d  =      (
F3     2        e     d  ]      )
measure 7
Bf3    2        e     d
rest   2        e
Ef3    2        e     d
rest   2        e
F3     2        e     d
rest   2        e
measure 8
Bf2    2        e     d  [
Bf3    2        e     d  =
Bf3    2        e     d  =      (
Af3    2        e     d  =      )+
Af3    2        e     d  =      (
G3     2        e     d  ]      )
measure 9
G3     2        e     d
rest   2        e
C4     2        e     d
rest   2        e
C3     2        e     u
rest   2        e
measure 10
F3     2        e     d  [      (
Af3    2        e     d  =      )
Af3    2        e     d  =      (
C4     2        e     d  =      )
C4     2        e     d  =      (
F3     2        e     d  ]      )
measure 11
F3     2        e     d
rest   2        e
A3     2        e n   d
rest   2        e
F3     2        e     d
rest   2        e
measure 12
Bf3    2        e     d  [      (
F3     2        e     d  =      )
F3     2        e     d  =      (
D3     2        e     d  =      )
D3     2        e     d  =      (
Bf2    2        e     d  ]      )
measure 13
Bf2    2        e     u
rest   2        e
Bf3    2        e     d
rest   2        e
Bf2    2        e     u
rest   2        e
measure 14
Ef3    2        e     d
rest   2        e
G2     2        e     u
rest   2        e
Ef2    2        e     u
rest   2        e
measure 15
Af2    2        e     u
rest   2        e
F2     2        e     u
rest   2        e
Bf2    2        e     u
rest   2        e
measure 16
Ef2    2        e     u  [
Ef3    2        e     u  =
Ef3    2        e     u  =      (
Bf2    2        e     u  =      )
G2     2        e     u  =      (
Ef2    2        e     u  ]      )
measure 17
Ef2    2        e     u  [      p
Ef3    2        e     u  =
Ef3    2        e     u  =      (
D3     2        e     u  =      )
D3     2        e     u  =      (
C3     2        e     u  ]      )
measure 18
C2     2        e     u  [
C3     2        e     u  =
C3     2        e     u  =      (
Bf2    2        e     u  =      )
Bf2    2        e     u  =      (
Af2    2        e     u  ]      )
measure 19
Af2    2        e     u
rest   2        e
F2     2        e     u
rest   2        e
Bf2    2        e     u
rest   2        e
measure 20
Ef2    2        e     d  [
Ef3    2        e     d  =
Ef3    2        e     d  =      (
G3     2        e     d  =      )
G3     2        e     d  =      (
Bf3    2        e     d  ]      )
measure 21
Bf3    2        e     d         f
rest   2        e
Bf2    2        e     u
rest   2        e
Bf3    2        e     d
rest   2        e
measure 22
Ef3    2        e     d
rest   2        e
G2     2        e     u
rest   2        e
Ef2    2        e     u
rest   2        e
measure 23
Af2    2        e     u
rest   2        e
F2     2        e     u
rest   2        e
Bf2    2        e     u
rest   2        e
measure 24
Ef2    2        e     u  [
Ef3    2        e     u  =
Ef3    2        e     u  =      (
Bf2    2        e     u  =      )
G2     2        e     u  =      (
Ef2    2        e     u  ]      )
measure 25
Ef2    2        e     u  [      p
Ef3    2        e     u  =
Ef3    2        e     u  =      (
D3     2        e     u  =      )
D3     2        e     u  =      (
C3     2        e     u  ]      )
measure 26
C2     2        e     u  [
C3     2        e     u  =
C3     2        e     u  =      (
Bf2    2        e     u  =      )
Bf2    2        e     u  =      (
Af2    2        e     u  ]      )
measure 27
Af2    2        e     u
rest   2        e
F2     2        e     u
rest   2        e
Bf2    2        e     u
rest   2        e
measure 28
Ef2    2        e     u  [
Ef3    2        e     u  =
Ef3    2        e     u  =      (
C3     2        e     u  =      )
A2     2        e n   u  =      (
F2     2        e     u  ]      )
measure 29
Bf2    2        e     u
rest   2        e
Bf3    2        e     d
rest   2        e
Ef3    1        s     u  [[     (
D3     1        s     u  ==
C3     1        s     u  ==
Bf2    1        s     u  ]]     )
measure 30
C3     2        e     u
rest   2        e
C4     2        e     d
rest   2        e
D3     1        s     u  [[     (
C3     1        s     u  ==
Bf2    1        s     u  ==
A2     1        s n   u  ]]     )
measure 31
Bf2    2        e     u
rest   2        e
Bf3    2        e     d
rest   2        e
Ef3    2        e     d
rest   2        e
measure 32
F3     2        e     d  [      (
Ef3    2        e     d  =      )
Ef3    2        e     d  =      (
D3     2        e     d  =      )
D3     2        e     d  =      (
C3     2        e     d  ]      )
measure 33
Bf2    2        e     u
rest   2        e
D3     2        e     d
rest   2        e
Bf2    2        e     u
rest   2        e
measure 34
G2     2        e     u
rest   2        e
G3     2        e     d
rest   2        e
F3     2        e     d
rest   2        e
measure 35
Ef3    2        e     d
rest   2        e
C3     2        e     u
rest   2        e
Ef3    2        e     d
rest   2        e
measure 36
D3     2        e     d
rest   2        e
F3     2        e     d
rest   2        e
G3     2        e     d
rest   2        e
measure 37
C3     2        e     u
rest   2        e
Ef3    2        e     d
rest   2        e
F3     2        e     d
rest   2        e
measure 38
Bf2    2        e     u
rest   2        e
Bf3    2        e     d
rest   2        e
Af3    2        e     d         +
rest   2        e
measure 39
G3     2        e     d
rest   2        e
B3     2        e n   d
rest   2        e
G3     2        e     d
rest   2        e
measure 40
C3     2        e     u
rest   2        e
Ef3    2        e     d
rest   2        e
B2     2        e n   u
rest   2        e
measure 41
C3     2        e     u
rest   2        e
C4     2        e     d
rest   2        e
Bf3    2        e     d
rest   2        e
measure 42
A3     2        e n   d
rest   2        e
F3     2        e     d
rest   2        e
A3     2        e     d
rest   2        e
measure 43
Bf3    2        e     d
rest   2        e
Ef3    2        e     d
rest   2        e
F3     2        e     d
rest   2        e
measure 44
Bf2    2        e     u         f
rest   2        e
D3     2        e     d
rest   2        e
Bf2    2        e     u
rest   2        e
measure 45
Ef3    2        e     d  [
C4     2        e     d  =
C4     2        e     d  =      (
Bf3    2        e     d  =      )
Bf3    2        e     d  =      (
A3     2        e n   d  ]      )
measure 46
A3     2        e n   d  [      (
G3     2        e     d  =      )
G3     2        e     d  =      (
F3     2        e     d  =      )
F3     2        e     d  =      (
A3     2        e     d  ]      )
measure 47
Bf3    2        e     d
rest   2        e
Ef3    2        e     d
rest   2        e
F3     2        e     d
rest   2        e
measure 48
Bf2    2        e     d  [
Bf3    2        e     d  =      p
Bf3    2        e     d  =      (
Af3    2        e     d  =      )+
Af3    2        e     d  =      (
G3     2        e     d  ]      )
measure 49
G3     2        e     d
rest   2        e
C4     2        e     d
rest   2        e
C3     2        e     u
rest   2        e
measure 50
F2     2        e     u  [      (
Af2    2        e     u  =      )
Af2    2        e     u  =      (
C3     2        e     u  =      )
C3     2        e     u  =      (
F3     2        e     u  ]      )
measure 51
F3     2        e     d
rest   2        e
A3     2        e n   d
rest   2        e
F3     2        e     d
rest   2        e
measure 52
Bf3    2        e     u  [
Bf2    2        e     u  =
Bf2    2        e     u  =      (
Af2    2        e     u  =      )
G2     2        e     u  =      (
F2     2        e     u  ]      )
measure 53
Ef2    2        e     u  [
Ef3    2        e     u  =
Ef3    2        e     u  =      (
D3     2        e     u  =      )
D3     2        e     u  =      (
C3     2        e     u  ]      )
measure 54
C2     2        e     u  [
C3     2        e     u  =
C3     2        e     u  =      (
Bf2    2        e     u  =      )
Bf2    2        e     u  =      (
Af2    2        e     u  ]      )
measure 55
Af2    2        e     u
rest   2        e
F2     2        e     u
rest   2        e
Bf2    2        e     u
rest   2        e
measure 56
Ef2    2        e     d  [
Ef3    2        e     d  =
Ef3    2        e     d  =      (
G3     2        e     d  =      )
G3     2        e     d  =      (
Bf3    2        e     d  ]      )
measure 57
Bf3    2        e     d
rest   2        e
Bf2    2        e     u
rest   2        e
Bf3    2        e     d
rest   2        e
measure 58
Ef3    2        e     d
rest   2        e
G3     2        e     d
rest   2        e
Ef3    2        e     d
rest   2        e
measure 59
E3     2        e n   d
rest   2        e
G3     2        e     d
rest   2        e
C3     2        e     u
rest   2        e
measure 60
F2     2        e     u
rest   2        e
Af2    2        e     u
rest   2        e
C3     2        e     u
rest   2        e
measure 61
F2     2        e     u
rest   2        e
F3     2        e     d
rest   2        e
Ef3    2        e     d
rest   2        e
measure 62
D3     2        e     d
rest   2        e
Bf2    2        e     u
rest   2        e
D3     2        e     d
rest   2        e
measure 63
Ef3    2        e     d
rest   2        e
Af2    2        e     u
rest   2        e
Bf2    2        e     u
rest   2        e
measure 64
Ef2    2        e     u  [      (f
G2     2        e     u  =      )
G2     2        e     u  =      (
Af2    2        e     u  =      )
Af2    2        e     u  =      (
Bf2    2        e     u  ]      )
measure 65
Bf2    2        e     u
rest   2        e
Bf3    2        e     d
rest   2        e
Bf2    2        e     u
rest   2        e
measure 66
Ef3    2        e     d
rest   2        e
G2     2        e     u
rest   2        e
Ef2    2        e     u
rest   2        e
measure 67
Af2    2        e     u
rest   2        e
F2     2        e     u
rest   2        e
Bf2    2        e     u
rest   2        e
measure 68
Ef2    4        q     u         F
S C8:F4
rest   4        q
rest   4        q
measure 69
C3     2        e     d  [      p
C4     2        e     d  =
C4     2        e     d  =      (
Bf3    2        e     d  =      )
Bf3    2        e     d  =      (
Af3    2        e     d  ]      )
measure 70
Af2    2        e     d  [
Af3    2        e     d  =
Af3    2        e     d  =      (
G3     2        e     d  =      )
G3     2        e     d  =      (
F3     2        e     d  ]      )
measure 71
F3     2        e     d
rest   2        e
D3     2        e     d
rest   2        e
F3     2        e     d
rest   2        e
measure 72
G2     2        e     u  [      (
A2     2        e n   u  =      )
A2     2        e     u  =      (
B2     2        e n   u  =      )
B2     2        e     u  =      (
C3     2        e     u  ]      )
measure 73
C3     2        e     d  [
C4     2        e     d  =
C4     2        e     d  =      (
Bf3    2        e     d  =      )
Bf3    2        e     d  =      (
A3     2        e n   d  ]      )
measure 74
A2     2        e n   d  [
A3     2        e n   d  =
A3     2        e     d  =      (
G3     2        e     d  =      )
G3     2        e     d  =      (
F#3    2        e #   d  ]      )
measure 75
F#3    2        e #   d  [      (
G3     2        e     d  =      )
G3     2        e     d  =      (
Ef3    2        e     d  =      )
Ef3    2        e     d  =      (
D3     2        e     d  ]      )
measure 76
D3     2        e     d  [      (
E3     2        e n   d  =      )
E3     2        e     d  =      (
F#3    2        e #   d  =      )
F#3    2        e     d  =      (
G3     2        e     d  ]      )
measure 77
G2     2        e     u
rest   2        e
C3     2        e     u
rest   2        e
A2     2        e n   u
rest   2        e
measure 78
F2     2        e     u
rest   2        e
D3     2        e     d
rest   2        e
Bf2    2        e     u
rest   2        e
measure 79
G2     2        e     u
rest   2        e
Ef3    2        e     d
rest   2        e
C3     2        e     u
rest   2        e
measure 80
A2     2        e n   u
rest   2        e
C3     2        e     u
rest   2        e
A2     2        e     u
rest   2        e
measure 81
F#2    2        e #   u  [      (
C3     2        e     u  =      )
C3     2        e     u  =      (
A2     2        e n   u  =      )
A2     2        e     u  =      (
F#2    2        e     u  ]      )
measure 82
D2     2        e     u
rest   2        e
F#2    2        e #   u
rest   2        e
D2     2        e     u
rest   2        e
measure 83
G2     2        e     u
rest   2        e
C3     2        e     u
rest   2        e
D3     2        e     d
rest   2        e
measure 84
G2     2        e     u         f
rest   2        e
G3     2        e     d
rest   2        e
G2     2        e     u
rest   2        e
measure 85
A2     2        e n   u  [      (
Bf2    2        e     u  =      )
Bf2    2        e     u  =      (
C3     2        e     u  =      )
C3     2        e     u  =      (
D3     2        e     u  ]      )
measure 86
D3     2        e     d  [      (
E3     2        e n   d  =      )
E3     2        e     d  =      (
F#3    2        e #   d  =      )
F#3    2        e     d  =      (
G3     2        e     d  ]      )
measure 87
G3     2        e     d  [      (
Ef3    2        e     d  =      )
Ef3    2        e     d  =      (
C3     2        e     d  =      )
D3     2        e     d  =
D2     2        e     d  ]
measure 88
G2     2        e     u  [      (
Bf2    2        e     u  =      )
Bf2    2        e     u  =      (p
D3     2        e     u  =      )
D3     2        e     u  =      (
F#3    2        e #   u  ]      )
measure 89
G3     2        e     u  [
G2     2        e     u  =
G2     2        e     u  =      (
F2     2        e     u  =      )
F2     2        e     u  =      (
Ef2    2        e     u  ]      )
measure 90
Ef2    2        e     u  [
Ef3    2        e     u  =
Ef3    2        e     u  =      (
D3     2        e     u  =      )
D3     2        e     u  =      (
C3     2        e     u  ]      )
measure 91
C3     2        e     u
rest   2        e
C4     2        e     d
rest   2        e
C3     2        e     u
rest   2        e
measure 92
F3     2        e     u  [      (
C3     2        e     u  =      )
C3     2        e     u  =      (
Af2    2        e     u  =      )
Af2    2        e     u  =      (
F2     2        e     u  ]      )
measure 93
F2     2        e     d  [
F3     2        e     d  =
F3     2        e     d  =      (
Ef3    2        e     d  =      )
Ef3    2        e     d  =      (
D3     2        e     d  ]      )
measure 94
D2     2        e     u  [
D3     2        e     u  =
D3     2        e     u  =      (
C3     2        e     u  =      )
C3     2        e     u  =      (
B2     2        e n   u  ]      )
measure 95
B2     2        e n   u  [      (
C3     2        e     u  =      )
C3     2        e     u  =      (
Af2    2        e     u  =      )+
Af2    2        e     u  =      (
G2     2        e     u  ]      )
measure 96
G2     2        e     u  [      (
A2     2        e n   u  =      )
A2     2        e     u  =      (
B2     2        e n   u  =      )
B2     2        e     u  =      (
C3     2        e     u  ]      )
measure 97
C3     2        e     u
rest   2        e
F2     2        e     u
rest   2        e
Af2    2        e     u
rest   2        e
measure 98
Bf2    2        e     u
rest   2        e
Ef2    2        e     u
rest   2        e
G2     2        e     u
rest   2        e
measure 99
Af2    2        e     u
rest   2        e
D2     2        e     u
rest   2        e
F2     2        e     u
rest   2        e
measure 100
G2     2        e     d  [
G3     2        e     d  =
Af3    2        e     d  =      (
G3     2        e     d  =      )
F3     2        e     d  =      (
Ef3    2        e     d  ]      )
measure 101
D3     2        e     d  [      (
F3     2        e     d  =      )
F3     2        e     d  =      (
D3     2        e     d  =      )
D3     2        e     d  =      (
B2     2        e n   d  ]      )
measure 102
G2     2        e     u
rest   2        e
B2     2        e n   u
rest   2        e
G2     2        e     u
rest   2        e
measure 103
Ef2    2        e     u
rest   2        e
F2     2        e     u
rest   2        e
G2     2        e     u
rest   2        e
measure 104
C2     2        e     u  [
C3     2        e     u  =      f
C3     2        e     u  =      (
D3     2        e     u  =      )
D3     2        e     u  =      (
Ef3    2        e     u  ]      )
*               B   39  Dal Segno
mheavy2         A
S C0:d
/END
/eof
'''

bachContrapunctus1_part1 = '''378
1080  1
Bach Gesells
chaft xxv,1

4 1
78 -1 16 4
2 2 0 0 31
measure 1
rest 16
measure 2
rest 16
measure 3
rest 16
measure 4
rest 16
measure 5
A4    8
D5    8
measure 6
C5    8
A4    8
measure 7
G#4   8
A4    4
B4    4
measure 8
C5   10
D5    2
C5    2
Bf4   2
measure 9
A4    2
D4    2
D5    8
C#5   4
measure 10
D5    2
A4    2
C5    6
A4    2
Bf4   4-
measure 11
Bf4   2
E4    2
A4   12-
measure 12
A4    2
C5    4
B4    2
C5    8-
measure 13
C5    2
D4    2
C5    6
A4    2
B4    4-
measure 14
B4    4
A4    2
G#4   2
A4    8
measure 15
B4    8
C5    4
D5    4
measure 16
G4    2
Bf4   2
A4    6
Bf4   2
A4    2
G4    2-
measure 17
G4    2
E4    2
F4    2
D4    2
Bf4   8-
measure 18
Bf4   2
G4    2
A4    4
D5    8-
measure 19
D5    2
B4    2
C5    4
F5    8-
measure 20
F5    2
D5    2
E5    4
A4    4
D5    4-
measure 21
D5    2
B4    2
C5    4
F4    4
Bf4   4
measure 22
A4    8
D4    4
G4    4-
measure 23
G4    2
E4    2
F4    2
D5    2
E4    8-
measure 24
E4    2
D4    2
A4    8
G4    4
measure 25
A4    8
rest  8
measure 26
rest 16
measure 27
rest 16
measure 28
rest 16
measure 29
A4    8
E5    8
measure 30
C5    8
A4    8
measure 31
G#4   8
A4    4
B4    4
measure 32
C5   10
D5    2
C5    2
Bf4   2
measure 33
A4    4
rest  8
A4    4-
measure 34
A4    2
C5    2
Bf4   2
A4    2
Bf4   2
A4    2
G4    2
F#4   2
measure 35
G4    6
Bf4   2
E4    6
F#4   2
measure 36
G4    6
E4    2
C#4   6
A4    2
measure 37
D4    6
F4    2
E4    6
C5    2
measure 38
F4    6
A4    2
G4    6
E5    2
measure 39
A4    6
C5    2
B4    6
G5    2
measure 40
C#5   8
D5    4
E5    4-
measure 41
E5    2
C#5   2
D5   10
E5    2
measure 42
F5    2
E5    2
G5    6
F5    2
E5    2
D5    2
measure 43
C#5   2
A4    2
D5    6
B4    2
C5    4-
measure 44
C5    4
Bf4   4
A4    4
rest  4
measure 45
rest 16
measure 46
rest 16
measure 47
rest 16
measure 48
rest 16
measure 49
E5    8
A5    8
measure 50
F5    8
D5    8
measure 51
C#5   8
D5    4
E5    4
measure 52
F5   10
G5    2
F5    2
E5    2
measure 53
D5    6
E5    2
C#5   4
D5    2
F5    2
measure 54
Bf4  10
Bf4   2
A4    2
G4    2
measure 55
F4    8
Bf4   8
measure 56
A4   12
E5    4-
measure 57
E5    2
C#5   2
D5    2
E5    2
F5    2
D5    2
G5    4-
measure 58
G5    2
E5    2
A5    2
G5    2
F5    2
E5    2
D5    2
C#5   2
measure 59
D5    2
C5    2
Bf4   2
A4    2
G4    8-
measure 60
G4    2
E4    2
F4    2
D4    2
A4    8-
measure 61
A4    2
F#4   2
G4    2
Bf4   2
C5    8-
measure 62
C5    2
A4    2
Bf4   2
D5    2
Ef5   4
D5    4
measure 63
C#5   4
A5    6
D5    2
G5    4-
measure 64
G5    2
C#5   2
F5    6
D5    2
E5    4-
measure 65
E5    2
C#5   2
D5    6
B4    2
C5    4-
measure 66
C5    4
Bf4   4
A4    6
A4    2
measure 67
D5    2
F5    2
E5    2
G5    2
F5    2
E5    2
D5    4-
measure 68
D5    2
F5    4
E5    2
F5    2
D5    2
E5    4-
measure 69
E5    2
D5    2
C5    2
B4    2
C5    6
A5    2
measure 70
G5    2
F#5   2
G5    2
Bf5   2
C#5   4
rest  4
measure 71
rest  8
D5    4
rest  4
measure 72
rest  8
D5    8-
measure 73
D5   10
B4    2
C#5   4
measure 74
D5    6
C5    2
Bf4   6
A4    2
measure 75
D4    8
rest  2
G4    2
A4    2
C5    2-
measure 76
C5    2
Bf4   2
C5    2
Ef5   4
D5    2
F#5   2
A5    2-
measure 77
A5    2
G5    1
A5    1
Bf5   2
C#5   2
D5    8-
measure 78
D5   16
END
@@(C) 2002 Center for Computer Assisted Research in the Humanities.
@@ID: {bach/bg/canon/1080/stage1/01/01}
@@TIMESTAMP: DEC/26/2001 [md5sum:d80ab3630544155fa0cbe1001e3966e8]
'''

bachContrapunctus1_part2 = '''381
1080  1
Bach Gesells
chaft xxv,1

4 2
78 -1 8 2
2 2 0 0 31
measure 1
D4    4
A4    4
measure 2
F4    4
D4    4
measure 3
C#4   4
D4    2
E4    2
measure 4
F4    5
G4    1
F4    1
E4    1
measure 5
D4    2
E4    2
F4    2
G4    2
measure 6
A4    2
A3    1
B3    1
C4    1
A3    1
F4    2-
measure 7
F4    1
B3    1
E4    3
F4    1
E4    1
D4    1
measure 8
E4    2
F#4   2
G4    4-
measure 9
G4    2
F4    2
E4    4
measure 10
D4    3
E4    1
F4    3
D4    1
measure 11
G4    3
G4    1
F4    1
E4    1
D4    1
C#4   1
measure 12
D4    2
G4    4
C4    2
measure 13
F4    3
E4    1
F4    3
G#3   1
measure 14
E4    6
D4    1
C4    1
measure 15
D4    1
F4    1
E4    1
D4    1
C4    2
rest  2
measure 16
rest  8
measure 17
rest  8
measure 18
rest  8
measure 19
rest  8
measure 20
rest  8
measure 21
rest  8
measure 22
rest  8
measure 23
D4    4
A4    4
measure 24
F4    4
D4    4
measure 25
C#4   4
D4    2
E4    2
measure 26
F4    5
G4    1
F4    1
E4    1
measure 27
D4    2
G4    3
E4    1
F4    2
measure 28
E4    2
A4    3
F#4   1
G4    2
measure 29
F#4   3
D5    1
G#4   4
measure 30
A4    2
rest  1
A3    1
C4    2
A3    2
measure 31
D4    2
F4    2
E4    2
D4    2
measure 32
C4    2
A4    4
D4    2
measure 33
E4    2
A4    3
G4    1
F4    1
E4    1
measure 34
D4    8-
measure 35
D4    1
D4    1
G4    3
G4    1
C4    2-
measure 36
C4    1
A3    1
Bf3   2
A3    4-
measure 37
A3    1
F3    1
G3    2
C4    4-
measure 38
C4    1
A3    1
B3    2
E4    4-
measure 39
E4    1
C#4   1
D4    2
G4    4-
measure 40
G4    1
A4    1
Bf4   2
A4    4-
measure 41
A4    5
F4    1
G4    2
measure 42
A4    3
Bf4   1
A4    2
G4    2-
measure 43
G4    2
F4    1
D4    1
A4    3
G4    1
measure 44
F#4   1
D4    1
G4    3
E4    1
F4    2-
measure 45
F4    1
D4    1
G4    3
E4    1
A4    2-
measure 46
A4    1
F4    1
Bf4   3
G4    1
A4    2-
measure 47
A4    1
F4    1
G4    4
F4    1
D4    1
measure 48
A4    4
D5    4-
measure 49
D5    1
C#5   1
B4    1
C#5   1
D5    1
A4    1
E5    2-
measure 50
E5    1
A4    1
D5    2
rest  1
F4    1
dele  0
Bf4   2-
measure 51
Bf4   1
E4    1
A4    3
G4    1
F4    1
E4    1
measure 52
D4    1
A4    1
D5    1
B4    1
G4    1
E4    1
C5    2-
measure 53
C5    2
Bf4   2
A4    4
measure 54
G4    3
F4    1
E4    4-
measure 55
E4    2
D4    1
C#4   1
D4    2
G4    2-
measure 56
G4    3
F4    1
E4    3
E4    1
measure 57
A4    6
G4    1
Bf4   1
measure 58
A4    5
G4    1
F4    1
E4    1
measure 59
D4    6
E4    2
measure 60
A3    2
rest  4
Ef4   2
measure 61
D4    4
rest  2
F#4   2
measure 62
G4    1
F#4   1
G4    2
rest  2
Bf4   2-
measure 63
Bf4   1
A4    1
F5    1
D5    1
B4    2
E5    1
C#5   1
measure 64
A4    2
D5    1
A4    1
Bf4   3
G4    1
measure 65
A4    3
F4    1
E4    3
G4    1
measure 66
F#4   1
D4    1
G4    3
E4    1
F4    2-
measure 67
F4    1
D5    1
C5    5
C5    1
measure 68
Bf4   1
A4    1
G#4   2
A4    3
E4    1
measure 69
A4    2
G4    5
C5    1
measure 70
A4    2
G4    4
rest  2
measure 71
rest  4
A4    2
rest  2
measure 72
rest  4
B4    4
measure 73
A4    7
G4    1
measure 74
F#4   1
G4    1
A4    3
G4    1
C5    2-
measure 75
C5    1
F#4   1
G4    1
Bf4   1
Ef4   4
measure 76
D4    2
A3    2
Bf3   2
C4    2
measure 77
D4    2
G3    3
Bf4   1
A4    1
G4    1-
measure 78
G4    1
F#4   1
E4    1
G4    1
F#4   4
END
@@(C) 2002 Center for Computer Assisted Research in the Humanities.
@@ID: {bach/bg/canon/1080/stage1/01/02}
@@TIMESTAMP: DEC/26/2001 [md5sum:84760083c9c0c52fe99f6582c991f517]
'''


#-------------------------------------------------------------------------------
# raw data for direct translation tests

#-------------------------------------------------------------------------------

ALL  = [bach_cantata5_mvmt3]



def get(contentRequest):
    '''Get test material by type of content

    >>> None
    '''
    pass



#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def xtestBasic(self):
        from music21 import musedata
        from music21.musedata import translate

        af = musedata.MuseDataFile()

        for tf in ALL:
            ah = af.readstr(tf)
            environLocal.printDebug([ah.getTitle()])
            s = translate.museDataToStreamScore(ah)
            # run musicxml processing to look for internal errors
            out = s.musicxml

if __name__ == "__main__":
    music21.mainTest(Test)



#------------------------------------------------------------------------------
# eof

