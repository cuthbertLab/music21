#-------------------------------------------------------------------------------
# Name:         abc.base.py
# Purpose:      music21 classes for dealing with abc data
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
Objects and tools for processing ABC data. 

'''

import music21
import unittest


try:
    import StringIO # python 2 
except:
    from io import StringIO # python3 (also in python 2.6+)


from music21 import common
from music21 import environment
_MOD = 'abc.base.py'
environLocal = environment.Environment(_MOD)





# Field name            header tune elsewhere Used by Examples and notes
# ==========            ====== ==== ========= ======= ==================
# A:area                yes                           A:Donegal, A:Bampton
# B:book                yes         yes       archive B:O'Neills
# C:composer            yes                           C:Trad.
# D:discography         yes                   archive D:Chieftans IV
# E:elemskip            yes    yes                    see Line Breaking
# F:file name                         yes               see index.tex
# G:group               yes         yes       archive G:flute
# H:history             yes         yes       archive H:This tune said to ...
# I:information         yes         yes       playabc
# K:key                 last   yes                    K:G, K:Dm, K:AMix
# L:default note length yes    yes                    L:1/4, L:1/8
# M:meter               yes    yes  yes               M:3/4, M:4/4
# N:notes               yes                           N:see also O'Neills - 234
# O:origin              yes         yes       index   O:I, O:Irish, O:English
# P:parts               yes    yes                    P:ABAC, P:A, P:B
# Q:tempo               yes    yes                    Q:200, Q:C2=200
# R:rhythm              yes         yes       index   R:R, R:reel
# S:source              yes                           S:collected in Brittany
# T:title               second yes                    T:Paddy O'Rafferty
# W:words                      yes                    W:Hey, the dusty miller
# X:reference number    first                         X:1, X:2
# Z:transcription note  yes                           Z:from photocopy

# K - key; the key signature should be  specified  with  a  capital
# letter  which  may  be  followed  by  a  # or b for sharp or flat

# M - meter; apart from the normal meters, e.g.   M:6/8  or  M:4/4,
# the   symbols  M:C  and  M:C|  give  common  time  and  cut  time
# respectively.

# Finally  note  that
# any line beginning with a letter in the range A-Z and immediately
# followed by a : is interpreted as a field


# Each meter automatically sets a default note length and a  single
# letter in the range A-G, a-g will generate a note of this length.

# default meter length
# For example, in 3/4 the default note length is an eighth note and
# so  the  input  DEF  represents  3 eighth notes. The default note
# length can be calculated by computing the meter as a decimal;  if
# it  is  less than 0.75 the default is a sixteenth note, otherwise
# it is an eighth note. 


# durations
# Notes of differing lengths can be obtained by  simply  putting  a
# multiplier  after the letter. Thus in 2/4, A or A1 is a sixteenth
# note, A2 an eighth note, A3 a dotted eighth note,  A4  a  quarter
# note,  A6 a dotted quarter note, A7 a double dotted quarter note,
# A8 a half note, A12 a dotted half note, A14 a double dotted  half
# note,  A15  a triple dotted half note and so on, whilst in 3/4, A
# is an eighth note, A2 a quarter note, A3 a dotted  quarter  note,
# A4 a half note, ...
# 
# To get shorter notes, either divide them - e.g. in 3/4, A/2 is  a
# sixteenth  note,  A/4  is  a  thirty-second  note - or change the
# default note length with the L:  field.   Alternatively,  if  the
# music has a broken rhythm, e.g. dotted eighth note/sixteenth note
# pairs, use broken rhythm markers (see below).  Note  that  A/  is
# shorthand for A/2.



# broken rhythms
# To
# support this abc notation uses a > to mean `the previous note  is
# dotted, the next note halved' and < to mean `the previous note
# 
#   L:1/16
#   a3b cd3 a2b2c2d2
# 
#   L:1/8
#   a3/2b/2 c/2d3/2 abcd
# 
#   L:1/8
#   a>b c<d abcd

# typlets
# These can be simply coded with the notation (2ab  for  a  duplet,
# (3abc  for  a triplet or (4abcd for a quadruplet, etc., up to (9.
# The musical meanings are:
# 
# 
#  (2 2 notes in the time of 3
#  (3 3 notes in the time of 2
#  (4 4 notes in the time of 3


# beams
# To group notes together under one beam  they  should  be  grouped
# together without spaces.

# bars
#  | bar line
#  |] thin-thick double bar line
#  || thin-thin double bar line
#  [| thick-thin double bar line
#  :| left repeat
#  |: right repeat
#  :: left-right repeat

# accidentals
# The symbols ^ = and _  are  used  (before  a  note)  to  generate
# respectively  a  sharp,  natural or flat. Double sharps and flats
# are available with ^^ and __ respectively.



# To change key, meter, or default note length, simply put in a new
# line with a K: M: or L: field, e.g.
#   ed|cecA B2ed|cAcA E2ed|cecA B2ed|c2A2 A2:|
#   K:G
#   AB|cdec BcdB|ABAF GFE2|cdec BcdB|c2A2 A2:|
# 
# To do this without generating a new line of music, put a \ at the
# end of the first line, i.e.
#   E2E EFE|E2E EFG|\
#   M:9/8
#   A2G F2E D2|]


# You can tie two notes together either across or within a bar with
# a  - symbol, e.g. abc-|cba or abc-cba.  More general slurs can be
# put in with () symbols.  Thus (DEFG) puts a slur  over  the  four
# notes.


# Grace notes can be written by enclosing  them  in  curly  braces,
# {}.  For  example,  a  taorluath  on  the Highland pipes would be
# written  {GdGe}.

# accents
# Staccato marks (a small dot above or below the note head) can  be
# generated  by  a  dot before the note, i.e. a staccato triplet is
# written as (3.a.b.c


# Chords (i.e. more than one note head on a  single  stem)  can  be
# coded  with [] symbols around the notes, e.g. [CEGc] produces the
# chord  of  C  major.  They  can  be  grouped   in   beams,   e.g.
# [d2f2][ce][df]

# Guitar chords can be put in under the melody  line  by  enclosing
# the  chord  in  inverted  commas,  e.g.  "Am7"A2D2 . See the tune
# `William and Nancy' in English.abc for an example.

# Tie symbols, -, should come immediately after a  note  group  but
# may  be  followed  by  a space, i.e. =G,2- . Open and close chord
# symbols, [], should enclose entire  note  sequences  (except  for
# guitar  chords),  i.e.  "C"[CEGc]  or "Gm7"[.=G,^c'] and open and
# close   slur   symbols,   (),   should    do    likewise,    i.e.
# "Gm7"(v.=G,2~^c'2)


# A % symbol will cause the remainder  of  any  input  line  to  be
# ignored. The file English.abc contains plenty of examples.



class ABCObject(object):
    def __init__(self, src):
        self.src = src # store source character sequence

class ABCMetadataObject(ABCObject):

    # given a logical unit, create an object
    # may be a chord, notes, metadata, bars
    def __init__(self, src):
        ABCObject__init__(self, src)

class ABCNotationObject(ABCObject):

    # given a logical unit, create an object
    # may be a chord, notes, bars

    def __init__(self, src):
        ABCObject__init__(self, src)

        self.inBar = None
        self.inBeam = None
        self.inSlur = None
        self.inGrace = None

        self.isChord = None
        # provide default duration from handler
        self.durationDefault = None
        # store if a broken symbol applies 
        self.brokenSymbol = None
        # store where the broken symbol was found
        self.brokenSymbolPosition = None 


class ABCHandler(object):

    # divide elements of a character stream into objects and handle
    # store in a list, and pass global information to compontns
    def __init__(self):
        self._objStream = []


    def walk(self, str):
        '''Walk the abc string, creating objects and backtracking along the way.
        '''
            
        for i in range(len(str)):
            if i > 0:
                charPrev = str[i-1]
            else:      
                charPrev = None

            # get last char previous non-white; do not start with current
            # -1 goes to index 0
            charPrevNotSpace = None
            for j in range(i-1, -1, -1):
                if not str[j].isspace():
                    charPrevNotSpace = str[j]
                    break

            charThis = str[i]

            if i < len(str)-1:
                charNext = str[i+1]
            else:      
                charNext = None

            charNextNotSpace = None
            for j in range(i, len(str)):
                if not str[j].isspace():
                    charNextNotSpace = str[j]
                    break

#             environLocal.printDebug(['charPrevNotSpace', repr(charPrevNotSpace), 
#                           'charPrevious', repr(charPrev), 
#                           'charThis', repr(charThis), 
#                           'charNext', repr(charNext), 
#                           'charNextNotSpace', repr(charNextNotSpace)]) 

    


class ABCFile(object):
    '''
    ABC File access

    '''
    
    def __init__(self): 
        pass

    def open(self, filename): 
        '''Open a file for reading
        '''
        self.file = open(filename, 'r') 

    def openFileLike(self, fileLike):
        '''Assign a file-like object, such as those provided by StringIO, as an open file object.

        >>> fileLikeOpen = StringIO.StringIO()
        '''
        self.file = fileLike
    
    def __repr__(self): 
        r = "<ABCFile>" 
        return r 
    
    def close(self): 
        self.file.close() 
    
    def read(self): 
        self.readstr(self.file.read()) 
    
    def readstr(self, str): 
        handler = ABCHandler()
        handler.walk(str)
    
#     def write(self): 
#         ws = self.writestr()
#         self.file.write(ws) 
#     
#     def writestr(self): 
#         pass










#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):
        from music21.abc import testFiles

        tf = testFiles.mysteryReel
        af = ABCFile()
        af.readstr(tf)


if __name__ == "__main__":
    music21.mainTest(Test)








