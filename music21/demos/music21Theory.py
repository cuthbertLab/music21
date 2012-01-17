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

# Beth's Triad Checker - Method to solve a single excercise Developed before break.

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

#    studentAnswers = [('E-', 'm'), ('D', 'M'), ('X', ''), ('X', ''), ('B', 'd'), 
#                      ('G', 'M'), ('F#','M'),('C','m'),('X', ''),('D-', 'M'), ('G#', 'm'),
#                      ('X', 'X'), ('E', 'd'), ('E', 'M'), ('X',''), ('B','m'), ('A', 'M'), 
#                      ('X',''), ('X',''), ('B-', 'd'), ('G', 'm')]




#-------------------------------------------------------------------------------

# Jose's Triad Checker 

# information about individual exercises should be correlated with student, computer answers to make showing errors easier.
# include chord itself and bar number, for instance.

# A different plan of attack for checker software.
# Beth, Lars: E-mail me if you have any questions. Feel free to play around with it.

# music21 has its own Exception class, which every Exception in music21 should extend.
class CheckerException(music21.Music21Exception):
    pass

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

#-------------------------------------------------------------------------------

# Example of solving specific assignment from book 11.1.* (Lars)

# The exercise asks students to identify the scale degrees, the interval between parts, and 
# the harmonic motion.

# To facilitate labeling, the xml of the exercise includes "marker" parts with dummy ("x notehead") notes 
# to indicate where the student should respond rather than having many question marks or underscores
# Students' responses are lyrics on those parts

# Each method is passed the complete stream sc, and the indexes of various parts (markerPart, topPart, etc...)
# allowing the methods to check slight variations on the same assignment (A vs. B-D)
# Incorrect responses are marked in red, although other output formats would be straightforward to implement

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
    # Checks whether lyrics of marker part matches motion in upper and lower parts before that marker
    prevMarker = note.Note()
    prevMarker.offset = 0
    for nMarker in sc.parts[markerPart].flat.getElementsByClass('Note'):
        # Use uses the offset of the previous marker to determine which notes to compare
        # could be set to different value if desired
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
            #nMarker.color = 'green' # For testing
            pass
        prevMarker = nMarker

# Each Exercise from the book

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

# Starting method to automatically add the marker parts -- Not functional
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

# Examples of checking for Counterpoint Errors as shown in the checklist from chapter 9

# Melodic Intervals - leap/skip is not et with a step in the other part (Letter L)

def createEditorialMelodicIntervals(music21Stream):
    '''Generates intervalList and intervalORList.'''

    for part in music21Stream.parts:
        notes = part.flat.notes
        currentObject = notes[1]
        while currentObject != None and not isinstance(currentObject, music21.bar.Barline):
            previousObject = currentObject.previous()
            if isinstance(currentObject, note.Note) and isinstance(previousObject, note.Note):
                currentObject.editorial.melodicInterval = interval.notesToInterval(previousObject, currentObject)
            currentObject = currentObject.next()
    for x in music21Stream.flat.notes:
        print x, x.editorial.melodicInterval 

def labelEditorialMotion(music21Stream):
    '''Generates intervalList and intervalORList.'''

    for part in music21Stream.parts:
        notes = part.flat.notes
        currentObject = notes[1]
        notes[0].editorial.misc['motion'] = None
        while currentObject != None and not isinstance(currentObject, music21.bar.Barline):
            previousObject = currentObject.previous()
            if isinstance(currentObject, music21.note.Note) and isinstance(previousObject, music21.note.Note):
                thisInterval = interval.Interval(previousObject, currentObject)
                if thisInterval.generic.isDiatonicStep:
                    currentObject.editorial.misc['motion'] = 'step'
                elif thisInterval.generic.isSkip:
                    currentObject.editorial.misc['motion'] = 'skip'
                else:
                    currentObject.editorial.misc['motion'] = 'unison'
                currentObject.lyric = currentObject.editorial.misc['motion']
            else:
                currentObject.editorial.misc['motion'] = None
            currentObject = currentObject.next()
        

    for noteObj in music21Stream.flat.getElementsByClass('Note'):
        print noteObj
        try:
            noteObj.editorial.misc['motion']
        except:
            noteObj.editorial.misc['motion'] = ''
        
    return music21Stream 


#Leap or skip (difference?) is not set with a step in the other part
def locateAbundantLeaps(music21Stream):

    #find skips in part1, verify steps are in part 2

    listOfNotes1 = music21Stream.parts[0].flat.getElementsByClass(music21.note.Note)
    for note in editorial.getObjectsWithEditorial(listOfNotes1, 'motion', 'skip'):
        noteInOtherPart = music21Stream.parts[1].flat.getElementAtOrBefore(note.offset, classList=['Note'])
        if noteInOtherPart.editorial.misc['motion'] != 'step' and noteInOtherPart.editorial.misc['motion'] != 'unison':
            note.color = 'red'
            noteInOtherPart.color = 'red'
            note.previous().color = 'red'
            noteInOtherPart.previous().color = 'red'
    listOfNotes2 = music21Stream.parts[1].flat.getElementsByClass(music21.note.Note)
    for note in editorial.getObjectsWithEditorial(listOfNotes2, 'motion', 'skip'):
        noteInOtherPart = music21Stream.parts[0].flat.getElementAtOrBefore(note.offset, classList=['Note'])
        if noteInOtherPart.editorial.misc['motion'] != 'step' and noteInOtherPart.editorial.misc['motion'] != 'unison':
            note.color = 'red'
            note.previous().color = 'red'
            noteInOtherPart.color = 'red'
            noteInOtherPart.previous().color = 'red'
            
    music21Stream.show()
    
    
'''
    iL = []
    iORL = []
    for i in range(0, self.totalNotes - 1):
        n1 = self.notesAndRests[i]
        n2 = self.notesAndRests[i+1]
        if n1 is None or n2 is None:
            raise StreamException("Some reason a NoneType is Here...")
        if n1.isRest == True or n2.isRest == True:
            iL.append(None)
            if n1.isRest == False:
                n3 = self.noteFollowingNote(n2, allowRests = False)
                if n3 is not None:
                    int1 = interval.notesToInterval(n1, n3)
                    n1.editorial.melodicIntervalOverRests = int1
                    iORL.append(int1)
        else:
            try:
                int1 = interval.notesToInterval(n1, n2)
            except:
                int1 = interval.notesToInterval(n1, n2)
            iL.append(int1)
            iORL.append(int1)
            n1.editorial.melodicInterval = int1
            n1.editorial.melodicIntervalOverRests = int1
    self.__intervalList = iL
    self.__intervalORList = iORL
'''



# ---------

# Harmonic Intervals are consonant (Letter J)


CONSONANT_INTERVALS = ["P1","m3","M3","P5","m6","M6"]

def addHarmonicIntervalEditorials(topPart, bottomPart):
    '''Assigns the .editorial.harmonicInterval attribute of each note to an interval object
    representing the interval between the bottom part and the top part'''
    # Note: Uses chordify to accommodate different rhythms
    # The harmonicInterval assigned to each note is the interval
    # occurring when the note sounds
    s = stream.Stream()
    s.append(topPart)
    s.append(bottomPart)
    for c in s.chordify().flat.getElementsByClass('Chord'):
        topNote = topPart.flat.getElementAtOrBefore(c.offset,classList={'Note'})
        bottomNote = bottomPart.flat.getElementAtOrBefore(c.offset,classList={'Note'})
        intv = interval.notesToInterval(bottomNote,topNote)
        if(topNote.offset == c.offset):
            topNote.editorial.harmonicInterval = copy.deepcopy(intv)
        if(bottomNote.offset == c.offset):
            bottomNote.editorial.harmonicInterval = copy.deepcopy(intv)
            
# Samples of what to do with these harmonic interval editorials:

# Assign as lyrics / print
def labelBasedOnHarmonicIntervalsEditorial(sc):
    for n in sc.flat.getElementsByClass('Note'):
        n.lyric = n.editorial.harmonicInterval.name
        print n.editorial.harmonicInterval  

# Check for dissonances and highlight red
def highlightDissonances(sc):
    for n in sc.flat.getElementsByClass('Note'):
        if n.editorial.harmonicInterval.simpleName not in CONSONANT_INTERVALS:
            n.color = 'red'

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass

class TextExternal(unittest.TestCase):
    
    def runTest(self):
        pass




if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof