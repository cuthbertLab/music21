'''
    The temporary home of all music21 theory checking methods that interface with 
    a museScore plugin to provide feedback to students and teachers.
    
    This project is under developmental status.
    
    Lars's Edit
    This is an update - Beth
    This is Lars's Update - Lars
'''

import music21
import unittest

from music21 import corpus

'''
Triad Exercise Assignment:
http://ocw.mit.edu/courses/music-and-theater-arts/21m-301-harmony-and-counterpoint-i-spring-2005/assignments/asgnmnt3_triads.pdf

Instructions:
Determine whether each collection of notes is a triad.
If it is a triad, identify the root and quality (d, m, M) of the triad.
If it's not a triad, simply write "X" below that collection of notes.
'''

#-------------------------------------------------------------------------------

# Don't call an attribute "stream", because there is a very important module named "stream"
def checkTriadExercise(music21Stream, studentAnswers):
    c = music21Stream.chordify().getElementsByClass('Chord')
    outputCheck = []
    cnt = 0
    for x, answerTuple in zip(c, studentAnswers):
        cnt = cnt + 1
        if x.isTriad():
            if x.isMajorTriad():
                boolType = 'M' == answerTuple[1]
            elif x.isMinorTriad():
                boolType = 'm' == answerTuple[1]
            elif x.isAugmentedTriad():
                boolType = 'A' == answerTuple[1]
            elif x.isDiminishedTriad():
                boolType =  'd' == answerTuple[1]
            else:
                # Avoid extraneous print statements...use warnings or throw an exception.
                print "NOT IDENTIFIED BY MUSIC21 - FAIL"
            outputCheck.append((x.root().name == answerTuple[0], boolType))
        else:
            outputCheck.append((answerTuple[0] == 'X', answerTuple[0] == 'X'))
            
    return outputCheck

# music21 has its own Exception class, which every Exception in music21 should extend.
class CheckerException(music21.Music21Exception):
    pass
    
#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass

if __name__ == "__main__":
    #music21.mainTest(Test)
    studentAnswers = [('E-', 'm'), ('D', 'M'), ('X', ''), ('X', ''), ('B', 'd'), 
                      ('G', 'M'), ('F#','M'),('C','m'),('X', ''),('D-', 'M'), ('G#', 'm'),
                      ('X', 'X'), ('E', 'd'), ('E', 'M'), ('X',''), ('B','m'), ('A', 'M'), 
                      ('X',''), ('X',''), ('B-', 'd'), ('G')]
    checkTriadExercise(corpus.parse('theoryExercises/triadExercise.xml'), studentAnswers)
    #checkTriadExercise(music21.converter.parse('C:/Users/bhadley/Documents/ex1.xml'), studentAnswers)

#------------------------------------------------------------------------------
# eof