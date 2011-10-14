# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         smt2011.py
# Purpose:      Demonstrations for the SMT 2011 demo
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


from music21 import environment, corpus

_MOD = 'demo/smt2011.py'
environLocal = environment.Environment(_MOD)





def ex01():
    # beethoven
    #s1 = corpus.parse('opus18no1/movement3.xml')
    #s1.show()


    # has lots of triplets toward end
    # viola not coming in as alto clef
#     s2 = corpus.parse('haydn/opus17no1/movement3.zip')
#     s2.show()

    s2 = corpus.parse('haydn/opus17no2/movement3.zip')
    # works well; some triplets are missing but playback correctly
    s2Chordified = s2.measures(1, 25).chordify()
    s2Chordified.show()



if __name__ == '__main__':
    ex01()

