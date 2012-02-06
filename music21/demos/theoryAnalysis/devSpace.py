'''
    just a developmental space to house random code snipets and developmental routines
    becoming obsolete as we build our theoryAnalyzer....
'''
import music21
from music21 import *
from music21 import voiceLeading
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
    for nMarker in sc.parts[markerPart].flat.getElementsByClass('Note'):
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

# Melodic Intervals - leap/skip is not set with a step in the other part (Letter L)

def labelEditorialMotion(music21Stream):
    '''labels the editorial object on each note with the type of melodic motion 
    (step, skip, or unison) that note makes with the previous note'''
    '''
    for part in music21Stream.parts:
        part.flat.attachMelodicIntervals()
    for note in music21Stream.flat.notes:
        thisInterval = note.editorial.melodicInterval
        if thisInterval.generic.isDiatonicStep:
            note.editorial.misc['motion'] = 'step'
        elif thisInterval.generic.isSkip:
            note.editorial.misc['motion'] = 'skip'
        elif thisInterval.generic.undirected == 1:
            note.editorial.misc['motion'] = 'unison'
        else:
            note.editorial.misc['motion'] = 'None'
    else:
        currentObject.editorial.misc['motion'] = None
       ''' 
        
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
                #currentObject.lyric = currentObject.editorial.misc['motion']
            else:
                currentObject.editorial.misc['motion'] = None
            currentObject = currentObject.next()
        
    for noteObj in music21Stream.flat.getElementsByClass('Note'):
        try:
            noteObj.editorial.misc['motion']
        except:
            noteObj.editorial.misc['motion'] = ''
        
    return music21Stream 


    


# ---------

# Harmonic Intervals are consonant (Letter J)

# Ex: addHarmonicIntervalEditorials(sc.parts[0],sc.parts[1])

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



# -----------------------------------------------------------------------------
# Checker routines for Assignment 11.3, Writing a note-to-note counterpoint in eighteenth-century style
# A. Above a given bass line


def checkVoiceLeadingQuartets(music21Score):
    '''

    '''
    k =  music21Score.analyze('key')
    
    previousSlice = None
    first = True
    for music21Obj in music21Score.parts[0].flat.notes:
        print 'this', music21Obj
        if first:
            previousSlice = getVerticalSlice(music21Obj, music21Score)
            first = False
            continue
        s2 = getVerticalSlice(music21Obj, music21Score)
        currentNotes = s2.flat.getElementsByClass(note.Note)
        #currentNotes.show('text')
        previousNotes = previousSlice.flat.getElementsByClass(note.Note)
        #previousNotes.show('text')

        # [ n1  n2  ]
        # [ m1  m2  ]
        
        #print previousNotes[0], ' ', currentNotes[0]
        #print previousNotes[1], ' ', currentNotes[1]
        
        n1 = previousNotes[0]
        n2 = currentNotes[0]
        m1 = previousNotes[1]
        m2 = currentNotes[1]
        
        v = voiceLeading.VoiceLeadingQuartet(copy.deepcopy(n1), copy.deepcopy(n2), copy.deepcopy(m1), copy.deepcopy(m2))
        v.key = k
        #if v.resolvesCorrectly(k) == False:
        #    n1.color = 'red'
        #    n2.color = 'red'
        #    m1.color = 'red'
        #    m2.color = 'red'
        #if v.leapSetWithSkip() == False:
        #    n1.color = 'blue'
        #    n2.color = 'blue'
        ##    m1.color = 'blue'
        #   m2.color = 'blue'
        print v.vIntervals[1]
        if not v.vIntervals[1].isConsonant() and not v.resolvesCorrectly():
            n2.color = 'yellow'
            m2.color = 'yellow'
        
        n2.lyric = v.vIntervals[1].simpleName
        
        previousSlice = s2
    
    music21Score.show()
        
def getVerticalSlice(music21Obj, scoreFromNote):
    '''

    '''
    
    
    
    #scoreFromNote1 = music21Obj.getAllContextsByClass(stream.Score) #EXTREMELY UNRELIABLE AND VERY PRONE TO ERROR>>>>GRRRRR
    
    verticalSlice = stream.Score()
    offsetOfPitchToIdentify =  music21Obj.getOffsetBySite(scoreFromNote.flat)

    for part in scoreFromNote.parts:
        foundObj = part.flat.getElementAtOrBefore(offsetOfPitchToIdentify, classList=['Pitch', 'Note', 'Chord', 'Rest', 'Harmony'])
        #print 'found', foundObj
        ks = foundObj.getContextByClass(key.KeySignature)
        ts = foundObj.getContextByClass(meter.TimeSignature)
        cl = foundObj.getContextByClass(clef.Clef)
        p = stream.Part()
        if cl:
            p.append(cl)
        if ks:
            p.append(ks)
        if ts:
            p.append(ts)
        p.append(foundObj)
        verticalSlice.insert(p)
    #print 'vs', verticalSlice.show('text')
    #verticalSlice.show()
    return verticalSlice

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass

class TestExternal(unittest.TestCase):
    
    def runTest(self):
        pass

    #def locateChecklistL(self):
    #    studentExercise = converter.parse('C:/Users/bhadley/Dropbox/Music21Theory/CounterpointExamplesCh9/9.4.A.xml')
    #    studentExercise2 = labelEditorialMotion(studentExercise)
    #    locateLeapNotSetWithSkip(studentExercise2)

    def check11_3(self):
        studentExercise = converter.parse('C:/Users/bhadley/Dropbox/Music21Theory/WWNortonWorksheets/WWNortonXMLFiles/XML11_worksheets/sampleStudentResponses/11_3.xml')
        #studentExercise.show('text')
        checkVoiceLeadingQuartets(studentExercise)

if __name__ == "__main__":
    music21.mainTest(Test)

    #from music21.demos import music21Theory
    #test = music21Theory.TestExternal()
    #test.check11_3()
#------------------------------------------------------------------------------
# eof