'''
    The temporary home of all music21 theory checking methods that interface with 
    a museScore plugin to provide feedback to students and teachers.
    
    This project is under developmental status.
    
    Lars's Edit
    This is an update - Beth
    This is Lars's Update - Lars
'''
import music21
from music21 import *

import itertools
import unittest

import copy
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
    c = music21Stream.chordify().flat.getElementsByClass('Chord')
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

# information about individual exercises should be correlated with student, computer answers to make showing errors easier.
# include chord itself and bar number, for instance.

# A different plan of attack for checker software.
# Beth, Lars: E-mail me if you have any questions. Feel free to play around with it.

quality = {'diminished': ['diminished','d'],
           'major': ['major','M'],
           'minor': ['minor','m']}

def checkExercise(music21Stream, studentAnswers):
    correctSols = solveExercise(music21Stream)
    return itertools.imap(checkSolution, correctSols, studentAnswers)

def checkSolution(correctSoln, studentSoln):
    if correctSoln[0] is True: # If collection of notes is a triad
        if studentSoln[0] == "X": # Misidentified as not a triad
            return "is triad"
        identifiedRoot = (correctSoln[1] == studentSoln[0])
        try:
            identifiedQuality = (studentSoln[1] in quality[correctSoln[2]])
        except KeyError:
            raise CheckerException("Quality of chord beyond assignment requirements.")
        if identifiedRoot and identifiedQuality:
            return True
        return (identifiedRoot, identifiedQuality)
    if correctSoln[0] is False: # If collection of notes is not a triad
        if studentSoln[0] == "X":
            return True
        return "is not triad" # Misidentified as a triad

def solveExercise(music21Stream):
    allChords = music21Stream.chordify().flat.getElementsByClass('Chord')
    return itertools.imap(solveChord, allChords)

def solveChord(music21Chord):
    return (music21Chord.isTriad(), music21Chord.root().name, music21Chord.quality)

def checkScaleDegrees(sc,scorePart,markerPart):
    exerciseScale = sc.parts[scorePart].flat.getElementsByClass('KeySignature')[0].getScale()

    # Check whether lyrics of marker part match scale degrees of score part at that offset
    for nMarker in sc.parts[markerPart].flat.getElementsByClass('Note'):
        n = sc.parts[scorePart].flat.getElementAtOrBefore(nMarker.offset,classList={'Note'})
      

        if nMarker.lyric != str(exerciseScale.getScaleDegreeFromPitch(n.pitch)):
            nMarker.color = 'red'
            nMarker.lyric += "->"+str(exerciseScale.getScaleDegreeFromPitch(n.pitch))
        else:
            nMarker.color='black'

def checkIntervalDegrees(sc,upperPart, lowerPart, markerPart):
    # Checks whether lyrics of marker part matches interval between lower part and upper part 
    for nMarker in sc.chordify().getElementsByClass('Chord'):
        nLower = sc.parts[lowerPart].flat.getElementAtOrBefore(nMarker.offset,classList={'Note'})
        nUpper = sc.parts[upperPart].flat.getElementAtOrBefore(nMarker.offset,classList={'Note'})
        intv = interval.notesToInterval(nLower,nUpper).generic.undirected
        while intv >= 9:
            intv -= 7
        if nMarker.lyric != str(intv):
            nMarker.lyric += "->"+str(intv)
            nMarker.color = 'red'
        else:
            nMarker.color ='black'
            
def checkMovement(sc,upperPart, lowerPart, markerPart):
    # Checks whether lyrics of marker part matches motion before that offset in marker part
    prevMarker = note.Note()
    prevMarker.offset = 0
    for nMarker in sc.parts[markerPart].flat.getElementsByClass('Note'):
        offsetDiff = nMarker.offset - prevMarker.offset
        n2Upper = sc.parts[upperPart].flat.getElementAtOrBefore(nMarker.offset,classList={'Note'})
        n1Upper = sc.parts[upperPart].flat.getElementAtOrBefore(nMarker.offset - offsetDiff,classList={'Note'})

        n2Lower = sc.parts[lowerPart].flat.getElementAtOrBefore(nMarker.offset,classList={'Note'})
        n1Lower = sc.parts[lowerPart].flat.getElementAtOrBefore(nMarker.offset - offsetDiff,classList={'Note'})

        vlq = voiceLeading.VoiceLeadingQuartet(n1Upper,n2Upper,n1Lower,n2Lower)
       
        if vlq.contraryMotion():
            if nMarker.lyric == "C":
                nMarker.color = 'black'
            else:
                nMarker.color = 'red'
                nMarker.lyric += "->C"
        elif vlq.obliqueMotion():
            if nMarker.lyric == "O":
                nMarker.color = 'black'
            else:
                nMarker.color = 'red'
                nMarker.lyric += "->O"
        elif vlq.parallelMotion():
            if nMarker.lyric == "P":
                nMarker.color = 'black'
            else:
                nMarker.color = 'red'
                nMarker.lyric += "->P"
        elif vlq.similarMotion():
            if nMarker.lyric == "S":
                nMarker.color = 'black'
            else:
                nMarker.color = 'red'
                nMarker.lyric += "->S"
        else:
            nMarker.color = 'green' # For testing
        prevMarker = nMarker

def ex_11_1_A(sc):
    checkScaleDegrees(sc,1,0)
    checkIntervalDegrees(sc,1, 2, 3)
    checkMovement(sc,1,2,4)

def ex_11_1_B(sc):
    checkIntervalDegrees(sc,0, 1, 2)
    checkMovement(sc,0,1,3)

def ex_11_1_C(sc):
    checkIntervalDegrees(sc,0, 1, 2)
    checkMovement(sc,0,1,3)

def ex_11_1_D(sc):
    checkIntervalDegrees(sc,0, 1, 2)
    checkMovement(sc,0,1,3)

    
def askForScaleDegrees(sc, partNumList):
    newStream = stream.Stream()
        
    for i in range(len(sc.parts)):
        if i in partNumList:
            newPart = copy.deepcopy(sc.parts[i])
            newPart[0] = instrument.Woodblock()
            
            for n in newPart.flat.getElementsByClass('Note'):
                n.notehead = 'x'
                n.pitch = pitch.Pitch('b-4')     
            newStream.append(newPart)   
        newStream.append(sc.parts[i])
    
    return newStream
        

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)
#    studentExercise = corpus.parse('theoryExercises/triadExercise.xml')
#    studentAnswers = [('E-', 'm'), ('D', 'M'), ('X', ''), ('X', ''), ('B', 'd'), 
#                      ('G', 'M'), ('F#','M'),('C','m'),('X', ''),('D-', 'M'), ('G#', 'm'),
#                      ('X', 'X'), ('E', 'd'), ('E', 'M'), ('X',''), ('B','m'), ('A', 'M'), 
#                      ('X',''), ('X',''), ('B-', 'd'), ('G', 'm')]
#    print checkTriadExercise(studentExercise, studentAnswers)
#    print list(checkExercise(studentExercise, studentAnswers))
    #checkTriadExercise(music21.converter.parse('C:/Users/bhadley/Documents/ex1.xml'), studentAnswers)

#------------------------------------------------------------------------------
# eof