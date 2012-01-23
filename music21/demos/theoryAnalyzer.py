#
# Theory Analyzer
#
# framework for analyzing theory in scores (parallel fifths, harmonic intervals, etc.)
#
# Beth Hadley and Lars Johnson
# January 22, 2012

import music21

from music21 import converter
from music21 import corpus
from music21 import interval
from music21 import voiceLeading

import unittest

class TheoryAnalyzer(object): # Should this be a music21 object? We think no.
    
    def __init__(self, theoryScore):
        self._theoryScore = theoryScore
        self._vlqCache = {}
        self.resultDict = {}
        self.key = self._theoryScore.analyze('key')
        
        self.verticalSlices = self.getVerticalSlices()
        
    # Vertical Slices
    
    def getVerticalSlices(self):
        '''
        >>> from music21 import *
        >>> from music21.demos import theoryAnalyzer
        >>> sc = stream.Score()
        >>> part1 = stream.Part()
        >>> part1.append(note.Note('c4'))
        >>> part1.append(note.Note('d4'))
        >>> part2 = stream.Part()
        >>> part2.append(note.Note('a4'))
        >>> part2.append(note.Note('b4'))
        >>> sc.insert(part1)
        >>> sc.insert(part2)
        >>> ta = TheoryAnalyzer(sc)
        >>> len(ta.verticalSlices)
        2
        '''
        vsList = []
        
        chordifiedSc = self._theoryScore.chordify()
        for c in chordifiedSc.flat.getElementsByClass('Chord'):
            nList = []
            for part in self._theoryScore.parts:
                el = part.flat.getElementAtOrBefore(c.offset,classList=['Note','Rest'])
                if el.isClassOrSubclass(['Note']):
                    nList.append(el)                    
                else:
                    nList.append(None)
            vs = VerticalSliceOfNotes(nList)
            
            vsList.append(vs)
                
        return vsList
    
    #  Intervals
    
    def getHarmonicIntervals(self, partNum1, partNum2):
        hInvList = []
        for verticalSlice in self.verticalSlices:
            
            nUpper = verticalSlice.getNote(partNum1)
            nLower = verticalSlice.getNote(partNum2)
            
            if nLower is None or nUpper is None:
                hIntv = None
            else:
                hIntv = interval.notesToInterval(nLower, nUpper)
            
            hInvList.append(hIntv)
                    
        return hInvList
    
    def getAllHarmonicIntervals(self):
        hInvList = []
        numParts = len(self._theoryScore.parts)
        for partNum1 in range(0, numParts-1):
            for partNum2 in range(partNum1 + 1, numParts):
                hInvList += self.getHarmonicIntervals(partNum1,partNum2)
        
        return hInvList
    
    def getMelodicIntervals(self, partNum):
        mInvList = []
        noteList = self._theoryScore.parts[partNum].flat.getElementsByClass(['Note','Rest'])
        for (i,n1) in enumerate(noteList[:-1]):
            n2 = noteList[i + 1]
            
            if n1.isClassOrSubclass(['Note']) and n2.isClassOrSubclass(['Note']):
                mIntv = interval.notesToInterval(n1, n2)
            else:
                mIntv = None
            
            mInvList.append(mIntv)
                    
        return mInvList
    
    # VLQs
    
    def getVLQs(self, partNum1, partNum2):
        vlqCacheKey = str(partNum1) + "," + str(partNum2)
        
        if vlqCacheKey in self._vlqCache.keys():
            return self._vlqCache[vlqCacheKey]
        
        vlqList = []
        for (i, verticalSlice) in enumerate(self.verticalSlices[:-1]):
            nextVerticalSlice = self.verticalSlices[i + 1]
            
            v1n1 = verticalSlice.getNote(partNum1)
            v1n2 = nextVerticalSlice.getNote(partNum1)
            
            v2n1 = verticalSlice.getNote(partNum2)
            v2n2 = nextVerticalSlice.getNote(partNum2)
            
            vlq = voiceLeading.VoiceLeadingQuartet(v1n1,v1n2,v2n1,v2n2, key=self.key)
            vlqList.append(vlq)
            
            self._vlqCache[vlqCacheKey] = vlqList
        
        return vlqList
            
    def getAllVLQs(self):
        vlqList = []
        numParts = len(self._theoryScore.parts)
        for partNum1 in range(0, numParts-1):
            for partNum2 in range(partNum1 + 1, numParts):
                vlqList += self.getVLQs(partNum1,partNum2)
        
        return vlqList

    # Helper for identifying across all parts - used for recursion in identify functions

    def getAllPartNumPairs(self):
        partNumPairs = []
        numParts = len(self._theoryScore.parts)
        for partNum1 in range(0, numParts-1):
            for partNum2 in range(partNum1 + 1, numParts):
                partNumPairs.append((partNum1,partNum2))
        
        return partNumPairs

    
    # Template for analysis based on VLQs
    
    def _identifyBasedOnVLQ(self, partNum1, partNum2, color, dictKey, testFunction, textFunction):
        if dictKey not in self.resultDict.keys():
            self.resultDict[dictKey] = []
        
        if partNum1 == None or partNum2 == None:
            for (partNum1,partNum2) in self.getAllPartNumPairs():
                self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        else:
            vlqList = self.getVLQs(partNum1, partNum2)
            
            for vlq in vlqList:
                if testFunction(vlq):
                    tr = VLQTheoryResult(vlq)
                    tr.text = textFunction(vlq, partNum1, partNum2)
                    if color is not None:
                        tr.color(color)
                    self.resultDict[dictKey].append(tr)
                    
    # Theory Errors using VLQ template
    
    def identifyParallelFifths(self, partNum1 = None, partNum2 = None, color = None):
        dictKey = 'parallelFifths'
        testFunction = lambda vlq: vlq.parallelFifth()
        textFunction = lambda vlq, pn1, pn2: "Parallel fifth at measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey,testFunction,textFunction)
        
    def identifyParallelOctaves(self, partNum1 = None, partNum2 = None, color = None):
        dictKey = 'parallelOctaves'
        testFunction = lambda vlq: vlq.parallelOctave()
        textFunction = lambda vlq, pn1, pn2: "Parallel octave at measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifyParallelUnisons(self, partNum1 = None, partNum2 = None, color = None):
        dictKey = 'parallelUnisons'
        testFunction = lambda vlq: vlq.parallelUnison()
        textFunction = lambda vlq, pn1, pn2: "Parallel unison at measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifyHiddenFifths(self, partNum1 = None, partNum2 = None, color = None):
        dictKey = 'hiddenFifths'
        testFunction = lambda vlq: vlq.hiddenFifth()
        textFunction = lambda vlq, pn1, pn2: "Hidden fifth at measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifyHiddenOctaves(self, partNum1 = None, partNum2 = None, color = None):
        dictKey = 'hiddenOctaves'
        testFunction = lambda vlq: vlq.hiddenOctave()
        textFunction = lambda vlq, pn1, pn2: "Hidden octave at measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifyImproperResolutions(self, partNum1 = None, partNum2 = None, color = None):
        dictKey = 'improperResolution'
        testFunction = lambda vlq: vlq.improperResolution()
        textFunction = lambda vlq, pn1, pn2: "Improper resolution of " + vlq.vIntervals[0].niceName +" at measure " + str(vlq.v1n1.measureNumber) +": "\
                 + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                 + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name + " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifyLeapNotSetWithStep(self, partNum1 = None, partNum2 = None, color = None):
        dictKey = 'identifyLeapNotSetWithStep'
        testFunction = lambda vlq: vlq.leapNotSetWithStep()
        textFunction = lambda vlq, pn1, pn2: "Leap not set with step at measure " + str(vlq.v1n1.measureNumber) +": "\
                 + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                 + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name + " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
    
    # Theory Errors not using VLQ (therefore, not using template)      
                    
    def identifyDissonantHarmonicIntervals(self, partNum1 = None, partNum2 = None, color = None):
        if 'dissonantHarmonicIntervals' not in self.resultDict.keys():
            self.resultDict['dissonantHarmonicIntervals'] = []
        
        if partNum1 == None or partNum2 == None:
            for (partNum1,partNum2) in self.getAllPartNumPairs():
                self.identifyDissonantHarmonicIntervals(partNum1, partNum2, color = color)
        else:
            hIntvList = self.getHarmonicIntervals(partNum1, partNum2)
            
            for hIntv in hIntvList:
                if hIntv is not None and not hIntv.isConsonant():
                    tr = IntervalTheoryResultObject(hIntv)
                    tr.text = "Dissonant harmonic interval in measure " + str(hIntv.noteStart.measureNumber) +": " \
                     + str(hIntv.niceName) + " from " + str(hIntv.noteStart.name) + " to " + str(hIntv.noteEnd.name) \
                     + " between part " + str(partNum1 + 1) + " and part " + str(partNum2 + 1)
                    if color is not None:
                        tr.color(color)
                    self.resultDict['dissonantHarmonicIntervals'].append(tr)
                
    def identifyDissonantMelodicIntervals(self, partNum = None, color = None):
        if 'dissonantMelodicIntervals' not in self.resultDict.keys():
            self.resultDict['dissonantMelodicIntervals'] = []
        
        if partNum == None:
            for partNum in range(0, len(self._theoryScore.parts)):
                self.identifyDissonantMelodicIntervals(partNum,color = color)
        else:
            mIntvList = self.getMelodicIntervals(partNum)
            
            for mIntv in mIntvList:
                if mIntv is not None and mIntv.simpleName in ["A2","A4","d5","m7","M7"]:
                    tr = IntervalTheoryResultObject(mIntv)
                    tr.text = "Dissonant melodic interval in part " + str(partNum + 1) + " measure " + str(mIntv.noteStart.measureNumber) +": "\
                     + str(mIntv.niceName) + " from " + str(mIntv.noteStart.name) + " to " + str(mIntv.noteEnd.name)
                    if color is not None:
                        tr.color(color)
                    self.resultDict['dissonantMelodicIntervals'].append(tr)
                
    
    # Other Theory Properties to Identify:
    
    # Theory Properties using VLQ template
        
    def identifyNoMotion(self, partNum1 = None, partNum2 = None, color = None):
        dictKey = 'noMotion'
        testFunction = lambda vlq: vlq.noMotion()
        textFunction = lambda vlq, pn1, pn2: "No motion at measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifyObliqueMotion(self, partNum1 = None, partNum2 = None, color = None):
        dictKey = 'obliqueMotion'
        testFunction = lambda vlq: vlq.obliqueMotion()
        textFunction = lambda vlq, pn1, pn2: "Oblique motion at measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifySimilarMotion(self, partNum1 = None, partNum2 = None, color = None):
        dictKey = 'similarMotion'
        testFunction = lambda vlq: vlq.similarMotion()
        textFunction = lambda vlq, pn1, pn2: "Similar motion at measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifyParallelMotion(self, partNum1 = None, partNum2 = None, color = None):
        dictKey = 'parallelMotion'
        testFunction = lambda vlq: vlq.parallelMotion()
        textFunction = lambda vlq, pn1, pn2: "Parallel motion at measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifyContraryMotion(self, partNum1 = None, partNum2 = None, color = None):
        dictKey = 'contraryMotion'
        testFunction = lambda vlq: vlq.contraryMotion()
        textFunction = lambda vlq, pn1, pn2: "Contrary motion at measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifyOutwardContraryMotion(self, partNum1 = None, partNum2 = None, color = None):
        dictKey = 'outwardContraryMotion'
        testFunction = lambda vlq: vlq.outwardContraryMotion()
        textFunction = lambda vlq, pn1, pn2: "Outward contrary motion at measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifyInwardContraryMotion(self, partNum1 = None, partNum2 = None, color = None):
        dictKey = 'inwardContraryMotion'
        testFunction = lambda vlq: vlq.inwardContraryMotion()
        textFunction = lambda vlq, pn1, pn2: "Inward contrary motion at measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifyAntiParallelMotion(self, partNum1 = None, partNum2 = None, color = None):
        dictKey = 'antiParallelMotion'
        testFunction = lambda vlq: vlq.antiParallelMotion()
        textFunction = lambda vlq, pn1, pn2: "Anti-parallel motion at measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
                    
    # Output Methods

    def printResults(self, typeList=None):
        for resultType in self.resultDict.keys():
            print resultType+":"
            if typeList is None or type in typeList:
                for result in self.resultDict[resultType]:
                    print result.text
                print ""
                
    def getResultsString(self, typeList=None):
        resultStr = ""
        for resultType in self.resultDict.keys():
            if typeList is None or type in typeList:
                for result in self.resultDict[resultType]:
                    resultStr += result.text + "\n"
                resultStr += "\n"
                
        return resultStr
            
    def colorResults(self, color='red', typeList=None):
        for resultType in self.resultDict.keys():
            if typeList is None or type in typeList:
                for result in self.resultDict[resultType]:
                    result.color(color)
            
    def show(self):
        self._theoryScore.show()
                
# Vertical Slice Object

class VerticalSliceOfNotes(object):
    
    def __init__(self,noteList):
        self._noteList = noteList
        
    def getNote(self,partNum):
        return self._noteList[partNum]
    
    def __repr__(self):
        for (i,n) in enumerate(self._noteList):
            print str(i) + ": " + str(n)
    
# Theory Result Object

class TheoryResult(object):
    
    def __init__(self):
        self.text = ""
        
    def color(self,color):
        pass

# VLQ Theory Result Object

class VLQTheoryResult(TheoryResult):
    def __init__(self, vlq):
        TheoryResult.__init__(self)
        self.vlq = vlq
        
    def color(self, color='red'):
        self.vlq.v1n1.color = color
        self.vlq.v1n2.color = color
        self.vlq.v2n1.color = color
        self.vlq.v2n2.color = color

# Interval Theory Result Object
                  
class IntervalTheoryResultObject(TheoryResult):
    def __init__(self, intv):
        TheoryResult.__init__(self)
        self.intv = intv
        
    def color(self, color='red'):
        self.intv.noteStart.color = color
        self.intv.noteEnd.color = color
            
            
# ------------------------------------------------------------

class Test(unittest.TestCase):
    
    def runTest(self):
        pass
        
class TestExternal(unittest.TestCase):
    
    def runTest(self):
        pass 
    
    def demo(self):
        s = converter.parse('/Users/larsj/Dropbox/Music21Theory/TestFiles/TheoryAnalyzer/TATest.xml')
#        s = converter.parse('C:/Users/bhadley/Dropbox/Music21Theory/TestFiles/TheoryAnalyzer/TATest.xml')
        ta = TheoryAnalyzer(s)

        
        ta.identifyParallelFifths(color='red')
        ta.identifyParallelOctaves(color='orange')
        ta.identifyHiddenFifths(color='yellow')
        ta.identifyHiddenOctaves(color='green')
        ta.identifyParallelUnisons(color='blue')
        ta.identifyImproperResolutions(color='purple')
        ta.identifyLeapNotSetWithStep(color='white')
        ta.identifyDissonantHarmonicIntervals(color='magenta')
        ta.identifyDissonantMelodicIntervals(color='cyan')

        ta.printResults()
        ta.show()
        
    
if __name__ == "__main__":
    music21.mainTest(Test)
    
#    te = TestExternal()
#    te.demo()

    