####
# methods for checking wwnorton theory assignments
# 
# Beth Hadley and Lars Johnson
# January 24, 2012
#
# WORK IN PROGRESS

import music21

from music21 import converter
from music21 import stream
from music21 import instrument
from music21 import note
from music21.demos import theoryAnalyzer

import unittest
import copy

class wwnortonExercise(object):
    ''' wwnortonExercise is a base class for all wwwnorton exercises '''
    def __init__(self):
        self.xmlFileDirectory = "/xmlfiles/"
        self.xmlFilename = ""
        self.title = ""
        self.instructions = ""
        self.additionalQuestionInstructions = ""
        self.additionalQuestion = ""
        
        self.studentExerciseErrorDict = {}

        
        self.originalExercise = stream.Stream()
        self.modifiedExercise = stream.Stream()
        self.studentExercise = stream.Stream()
        self.textResultString = ""
        self.pn = {}
        
    def checkExercise(self, questionAnswer = ""):
        pass
    
    def addAuxillaryParts(self):
        pass
    
    def loadOriginalExercise(self):
        self.originalExercise = converter.parse(self.xmlFileDirectory + self.xmlFilename)
        self.modifiedExercise = copy.deepcopy(self.originalExercise)
        self.addAuxillaryParts()

    def manuallyLoadOriginalExercise(self,sc):
        self.originalExercise = sc
        self.modifiedExercise = copy.deepcopy(self.originalExercise)
        self.addAuxillaryParts()
        
    def loadStudentExercise(self,sc):
        for n in sc.flat.getElementsByClass('Note'):
            n.color = 'black'
        self.studentExercise = sc
        
    
    def getBlankExercise(self):
        return self.blankExercise
    
    def _partOffsetsToPartIndecies(self):
        for (i,el) in enumerate(self.modifiedExercise.elements):
            el.offset = i
        #self.modifiedExercise.show('text')
        
    def _partOffsetsToZero(self):
        for (i,el) in enumerate(self.modifiedExercise.elements):
            el.offset = 0
        #self.modifiedExercise.show('text')

    def _updatepn(self,newPartNum,direction):
        for partName in self.pn.keys():
            existingPartNum = self.pn[partName]
            if existingPartNum > newPartNum:
                shiftedPartNum = existingPartNum + 1
            elif existingPartNum == newPartNum and direction =="above":
                shiftedPartNum = existingPartNum + 1
            else:
                shiftedPartNum = existingPartNum
            self.pn[partName] = shiftedPartNum   

    def addMarkerPartFromExisting(self, existingPartName, newPartName, newPartTitle="", direction = "below", rhythmType="copy",color = None):
        partNum = self.pn[existingPartName]
        
        self._partOffsetsToPartIndecies()
        
        existingPart = self.modifiedExercise.parts[partNum]
        existingPartOffset = existingPart.offset
        if rhythmType == "chordify":
            existingPart = self.originalExercise.chordify()
        newPart = copy.deepcopy(existingPart.getElementsByClass('Measure'))
        firstNote = True
        inst = instrument.Instrument()

        for  m in newPart:
            previousNotRestContents = copy.deepcopy(m.getElementsByClass('NotRest'))
            measureDuration = m.duration.quarterLength
            
            m.removeByClass(['GeneralNote']) # includes rests
            m.removeByClass(['Dyanmic'])
            m.removeByClass(['Stream']) # get voices or sub-streams
            m.removeByClass(['Dynamic']) 
            m.removeByClass(['Expression']) 
            m.removeByClass(['KeySignature']) 
            
            if rhythmType == "quarterNotes":
                for i in range(int(measureDuration)):
                    markerNote = note.Note('c4')
                    markerNote.notehead = 'x'
                    markerNote.quarterLength = 1
                    if color is not None:
                        markerNote.color = color
                    if firstNote:
                        markerNote.lyric = '>'
                        firstNote = False
                    m.append(markerNote)
            else:
                for oldNotRest in previousNotRestContents:
                    markerNote = note.Note('c4')
                    markerNote.offset = oldNotRest.offset
                    markerNote.notehead = 'x'
                    markerNote.quarterLength = oldNotRest.quarterLength
                    if color is not None:
                        markerNote.color = color
                    if firstNote:
                        markerNote.lyric = '>'
                        firstNote = False
                    m.insert(oldNotRest.offset, markerNote)
        inst.instrumentName = newPartTitle
        newPart.insert(0,inst)        
        for ks in newPart.flat.getElementsByClass('KeySignature'):
            ks.sharps = 0
        for c in newPart.flat.getElementsByClass('Clef'):
            c.sign = "C"
            c.line = 3
        self._updatepn(partNum,direction=direction)
        if direction == "above":
            insertLoc = existingPartOffset - 0.5
            self.pn[newPartName] = partNum
        elif direction == "below" or direction is None:
            insertLoc = existingPartOffset + 0.5
            self.pn[newPartName] = partNum + 1
        self.modifiedExercise.insert(insertLoc,newPart)
        #self.modifiedExercise.show('text')
        # Somehow needed for sorting...
        self.modifiedExercise._reprText()
        self._partOffsetsToZero()
        return newPart
    
    def compareMarkerLyricAnswer(self,ta,taKey,markerPartName,offsetFunc,lyricFunc,errorKey=None):
        markerPart = self.studentExercise.parts[self.pn[markerPartName]]
        
        totalNumber = 0
        numberCorrect = 0
        
        for resultObj in ta.resultDict[taKey]:
            offset = offsetFunc(resultObj)
            correctLyric = lyricFunc(resultObj)
            markerNote = markerPart.flat.getElementAtOrBefore(offset,classList={'Note'})
            if markerNote is None or markerNote.offset != offset:
                print "No Marker"
                continue
            
            totalNumber += 1
            if markerNote.lyric == str(correctLyric):
                numberCorrect += 1
            else:
                # RECORD ERROR
                #markerNote.lyric = markerNote.lyric + "->" + str(correctLyric)
                markerNote.color = 'red'
        if errorKey is not None:
            self.studentExerciseErrorDict[errorKey] = (numberCorrect, totalNumber)
            
    def getErrorDictPercentagesResultString(self):
        resultStr = ""
        overallCorrect = 0
        overallTotal = 0
        for dictKey in self.studentExerciseErrorDict.keys():
            (numCorrect,numTotal) = self.studentExerciseErrorDict[dictKey]
            overallCorrect += numCorrect
            overallTotal += numTotal
            if numTotal == 0:
                percent = "NA"
            else:
                percent = int( numCorrect * 100.0 / numTotal)
            resultStr += dictKey+": "+ str(numCorrect)+"/"+str(numTotal) + " ("+str(percent)+"%)\n"
            
        if overallTotal == 0:
            overallPercent = "NA"
        else:
            overallPercent = int( overallCorrect * 100.0 / overallTotal)
        resultStr += "\nOverall: "+ str(overallCorrect)+"/"+str(overallTotal) + " ("+str(overallPercent)+"%)"
        return resultStr
                
                
    def showStudentExercise(self):
        self.studentExercise.show()
             
    def show(self):
        self.modifiedExercise.show()
               

# EX 11.1.I (A->D)
class ex11_1_I(wwnortonExercise):
    def __init__(self, letter="A"):
        wwnortonExercise.__init__(self)
        self.xmlFilename = '11_1_I_'+str(letter)+'.xml'
        self.title = "Excercise 11.1.I."+str(letter)+" Chorale Melody Settings"
        self.instructions = "Here are the soprano and bass parts for a setting by J. S. Bach of the first phrase of an anonymous \
chorale melody (composed in (1539). Write the scale degrees for the melody above the first staff. Then, \
sing or play each of these. Label the harmonic intervals between the staves, and examine the counterpoint. In the blanks above the staff, \
mark the type of motion from beat to beat: contrary (C), oblique (O), similar (S), or parallel (P). Circle and label any dissonant passing \
or neighbor tones."
        self.pn['part1'] = 0
        self.pn['part2'] = 1
        self.loadOriginalExercise()
        
    def addAuxillaryParts(self):
        self.addMarkerPartFromExisting('part1', newPartName='p1ScaleDegrees',newPartTitle="1. Scale Degrees", direction = "above")
        self.addMarkerPartFromExisting('part1', newPartName='motionType',newPartTitle="2. Motion Type", rhythmType="quarterNotes", direction = "above")
        self.addMarkerPartFromExisting('part1', newPartName='harmIntervals',newPartTitle="3. Harmonic Intervals", rhythmType='chordify', direction = "below")
        
    def checkExercise(self, questionAnswer = ""):
        ta = theoryAnalyzer.TheoryAnalyzer(self.studentExercise)
        ta.identifyMotionType(self.pn['part1'],self.pn['part2'],dictKey='motionType')
        ta.identifyScaleDegrees(self.pn['part1'],dictKey='p1ScaleDegrees')
        ta.identifyHarmonicIntervals(self.pn['part1'],self.pn['part2'],dictKey='harmIntervals')
        
        
        scaleDegreeOffsetFunc = lambda resultObj: resultObj.n.offset
        scaleDegreeLyricTextFunc = lambda resultObj: resultObj.value
        
        self.compareMarkerLyricAnswer(ta,taKey='p1ScaleDegrees',\
                                markerPartName='p1ScaleDegrees',\
                                offsetFunc = scaleDegreeOffsetFunc,\
                                lyricFunc = scaleDegreeLyricTextFunc,
                                errorKey = "Scale Degrees")
        
        motionTypeOffsetFunc = lambda resultObj: resultObj.offset()
        motionTypeLyricTextFunc = lambda resultObj: resultObj.value[0]
        
        self.compareMarkerLyricAnswer(ta,taKey='motionType',\
                                markerPartName='motionType',\
                                offsetFunc = motionTypeOffsetFunc,\
                                lyricFunc = motionTypeLyricTextFunc,
                                errorKey = "Motion Type")
        
        harmonicIntervalOffsetFunc = lambda resultObj: resultObj.offset()
        
        def harmonicIntervalLyricTextFunc(resultObj): 
            value = resultObj.value
            while value > 9:
                value -= 7
            return value
        
        self.compareMarkerLyricAnswer(ta,taKey='harmIntervals',\
                                markerPartName='harmIntervals',\
                                offsetFunc = harmonicIntervalOffsetFunc,\
                                lyricFunc = harmonicIntervalLyricTextFunc,
                                errorKey = "Harmonic Intervals")

        self.textResultString = self.getErrorDictPercentagesResultString()

    
# EX 11.3.A.* (1-3)
class ex11_3_A(wwnortonExercise):
    def __init__(self,number=1):
        wwnortonExercise.__init__(self)
        self.xmlFilename = '11_3_A_'+str(number)+'.xml'
        self.title = "Excercise 11.3.A."+str(number)+" Writing note-to-note Counterpoint above a given bass line"
        self.instructions = "Examine the bass line to identify the key and mode, then determine which chords \
(V, V7, I, or i, and their inversions) are implied at the beginning and end, and write those Roman numerals in the blanks. \
Write the opening and closing counterpoint, then provide one soprano note for each of the other bass notes. You may use \
chordal dissonances (d5, A4, m7) if they can be resolved correctly; appoach these intervals by common tone or step. Label the harmonic \
intervals between the parts."
        self.additionalQuestionInstructions = "Please enter the key of the piece:"
        self.additionalQuestion = "Key of piece:"
        self.pn['part1'] = 0
        self.pn['part2'] = 1
        self.loadOriginalExercise()
        
    def addAuxillaryParts(self):
        self.addMarkerPartFromExisting('part2', newPartName='harmIntervals',newPartTitle="1. Harmonic Intervals", direction = "below")
        
    def checkExercise(self,additionalAnswer = ""):
        ta = theoryAnalyzer.TheoryAnalyzer(self.studentExercise)
        ta.identifyHarmonicIntervals(self.pn['part1'],self.pn['part2'],dictKey='harmIntervals')
        ta.identifyCommonPracticeErrors(self.pn['part1'],self.pn['part2'],dictKey='Counterpoint Issues')
          
        # KEY IS NOT WORKING!!!!
        if additionalAnswer != str(theoryAnalyzer.TheoryAnalyzer(self.originalExercise).key.pitchAndMode[0]):
            self.studentExerciseErrorDict['Key Identification'] = (0, 1) 
            self.textResultString += "Sorry, This exercise is not in the key of "+additionalAnswer+"->"+str(ta.key.pitchAndMode[0])+"\n\n"
        else:
            self.textResultString += "Good job. This exercise is in the key of "+additionalAnswer+"\n\n"
            self.studentExerciseErrorDict['Key Identification'] = (1, 1)   
              
        self.textResultString += ta.getResultsString(['Counterpoint Issues'])
        
        harmonicIntervalOffsetFunc = lambda resultObj: resultObj.offset()
        
        def harmonicIntervalLyricTextFunc(resultObj): 
            value = resultObj.value
            while value > 9:
                value -= 7
            return value
        
        self.compareMarkerLyricAnswer(ta,taKey='harmIntervals',\
                                markerPartName='harmIntervals',\
                                offsetFunc = harmonicIntervalOffsetFunc,\
                                lyricFunc = harmonicIntervalLyricTextFunc,
                                errorKey = "Harmonic Intervals")
        
        

        self.textResultString += self.getErrorDictPercentagesResultString()
        

# ------------------------------------------------------------

class Test(unittest.TestCase):
    
    def runTest(self):
        pass
        
class TestExternal(unittest.TestCase):
    
    def runTest(self):
        pass
    
    def demo(self):
        ex = ex11_3_A()
#        ex.show()
        sc = converter.parse('/Users/larsj/Dropbox/Music21Theory/TestFiles/Exercises/11_3_A_1_completed.xml')
        ex.show()
        ex.loadStudentExercise(sc)
        ex.checkExercise()
        ex.showStudentExercise()
        
    
if __name__ == "__main__":
    music21.mainTest(Test)
    
#    te = TestExternal()
#    te.demo()
    