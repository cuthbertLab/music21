# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         Theory Analyzer.py
# Purpose:      Framework for analyzing music theory aspects of a score
#
# Authors:      Lars Johnson
#               Beth Hadley
#
# Copyright:    (c) 2009-2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import music21

from music21 import converter
from music21 import corpus
from music21 import interval
from music21 import voiceLeading

import unittest

class TheoryAnalyzer(object):
    '''
    A Theory Analyzer is an object used for analyzing musical theory elements in scores. 
    It can identify, store, label and output various counterpoint-related features 
    in a score (parallel fifths, harmonic intervals, melodic intervals, etc.)
    
    A Theory Analyzer must be passed a score containing parts with single voices 
    (no harmonies/chords within a part...).
    
    >>> from music21 import *
    >>> p = corpus.parse('bwv66.6')
    >>> ta = TheoryAnalyzer(p)
    >>> ta.key
    <music21.key.Key of F# minor>
    '''
    
    def __init__(self, theoryScore):
        self._theoryScore = theoryScore
        self._vlqCache = {}
        self.resultDict = {}
        self.key = self._theoryScore.analyze('key')
        
        self.verticalSlices = self.getVerticalSlices()
        
    # Vertical Slices
    
    def getVerticalSlices(self):
        '''
        Gets a list of the vertical slices of the Theory Analyzer's score. Note that it uses the
        combined rhythm of the parts to determine what vertical slices to take.
        
        >>> from music21 import *
        >>> from music21.demos import theoryAnalyzer
        >>> n1 = note.Note('c5')
        >>> n1.quarterLength = 4
        >>> n2 = note.Note('f4')
        >>> n2.quarterLength = 2
        >>> n3 = note.Note('g4')
        >>> n3.quarterLength = 2
        >>> sc = stream.Score()
        >>> part0 = stream.Part()
        >>> part0.append(n1)
        >>> part1 = stream.Part()
        >>> part1.append(n2)
        >>> part1.append(n3)
        >>> sc.insert(part0)
        >>> sc.insert(part1)
        >>> ta = TheoryAnalyzer(sc)
        >>> len(ta.getVerticalSlices())
        2
        '''
        vsList = []
        
        # If speed is an issue, could try using offset maps...
        chordifiedSc = self._theoryScore.chordify()
        for c in chordifiedSc.flat.getElementsByClass('Chord'):
            nList = []
            for part in self._theoryScore.parts:
                el = part.flat.getElementAtOrBefore(c.offset,classList=['Note','Rest'])
                if el.isClassOrSubclass(['Note']):
                    nList.append(el)                    
                else:
                    nList.append(None)
            vs = VerticalSlice(nList)
            
            vsList.append(vs)
                
        return vsList
    
    #  Intervals
    
    def getHarmonicIntervals(self, partNum1, partNum2):
        '''
        Gets a list of all the harmonic intervals occurring between the two specified parts.
        
        >>> from music21 import *
        >>> from music21.demos import theoryAnalyzer
        >>> sc = stream.Score()
        >>> part0 = stream.Part()
        >>> part0.append(note.Note('e4'))
        >>> part0.append(note.Note('d4'))
        >>> part1 = stream.Part()
        >>> part1.append(note.Note('a3'))
        >>> part1.append(note.Note('b3'))
        >>> sc.insert(part0)
        >>> sc.insert(part1)
        >>> ta = TheoryAnalyzer(sc)
        >>> len(ta.getHarmonicIntervals(0,1))
        2
        >>> ta.getHarmonicIntervals(0,1)[0].name
        'P5'
        >>> ta.getHarmonicIntervals(0,1)[1].name
        'm3'
        '''
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
    
    
    def getMelodicIntervals(self, partNum):
        '''
        Gets a list of all the melodic intervals in the specified part.
        
        >>> from music21 import *
        >>> from music21.demos import theoryAnalyzer
        >>> sc = stream.Score()
        >>> part0 = stream.Part()
        >>> part0.append(note.Note('c4'))
        >>> part0.append(note.Note('g4'))
        >>> part0.append(note.Note('c5'))
        >>> sc.insert(part0)
        >>> ta = TheoryAnalyzer(sc)
        >>> len(ta.getMelodicIntervals(0))
        2
        >>> ta.getMelodicIntervals(0)[0].name
        'P5'
        >>> ta.getMelodicIntervals(0)[1].name
        'P4'
        '''
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
    
    def getNotes(self, partNum):
        noteList = []
        noteOrRestList = self._theoryScore.parts[partNum].flat.getElementsByClass(['Note','Rest'])
        for nr in noteOrRestList:
            if nr.isClassOrSubclass(['Note']):
                n = nr
            else:
                n = None
            
            noteList.append(n)
                    
        return noteList
    
    # VLQs are Voice Leading Quartets as found in voiceLeading.py
    
    def getVLQs(self, partNum1, partNum2):
        '''
        Gets a list of all the melodic intervals in the specified part.
        
        >>> from music21 import *
        >>> from music21.demos import theoryAnalyzer
        >>> sc = stream.Score()
        >>> part0 = stream.Part()
        >>> part0.append(note.Note('c4'))
        >>> part0.append(note.Note('g4'))
        >>> part0.append(note.Note('c5'))
        >>> sc.insert(part0)
        >>> ta = TheoryAnalyzer(sc)
        >>> len(ta.getMelodicIntervals(0))
        2
        >>> ta.getMelodicIntervals(0)[0].name
        'P5'
        >>> ta.getMelodicIntervals(0)[1].name
        'P4'
        '''
        # Caches the list of VLQs once they have been computed
        # for a specified set of partNums
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

    # Helper for identifying across all parts - used for recursion in identify functions

    def getAllPartNumPairs(self):
        '''
        Gets a list of all possible pairs of partNumbers:
        tuples (partNum1, partNum2) where 0 <= partNum1 < partnum2 < numParts
        
        >>> from music21 import *
        >>> from music21.demos import theoryAnalyzer
        >>> sc = stream.Score()
        >>> part0 = stream.Part()
        >>> part0.append(note.Note('c5'))
        >>> part1 = stream.Part()
        >>> part1.append(note.Note('g4'))
        >>> part2 = stream.Part()
        >>> part2.append(note.Note('c4'))
        >>> sc.insert(part0)
        >>> sc.insert(part1)
        >>> sc.insert(part2)
        >>> ta = TheoryAnalyzer(sc)
        >>> len(ta.getAllPartNumPairs())
        3
        >>> ta.getAllPartNumPairs()[0]
        (0, 1)
        >>> ta.getAllPartNumPairs()[1]
        (0, 2)
        >>> ta.getAllPartNumPairs()[2]
        (1, 2)
        '''
        partNumPairs = []
        numParts = len(self._theoryScore.parts)
        for partNum1 in range(0, numParts-1):
            for partNum2 in range(partNum1 + 1, numParts):
                partNumPairs.append((partNum1,partNum2))
        
        return partNumPairs

    
    # Template for analysis based on VLQs
    
    def _identifyBasedOnVLQ(self, partNum1, partNum2, color, dictKey, testFunction, textFunction    , valueFunction = None):
        if dictKey not in self.resultDict.keys():
            self.resultDict[dictKey] = []
        
        if partNum1 == None or partNum2 == None:
            for (partNum1,partNum2) in self.getAllPartNumPairs():
                self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        else:
            vlqList = self.getVLQs(partNum1, partNum2)
            
            for vlq in vlqList:
                if testFunction(vlq) is not False: # True or value
                    tr = VLQTheoryResult(vlq)
                    tr.value = testFunction(vlq)
                    tr.text = textFunction(vlq, partNum1, partNum2)
                    if color is not None:
                        tr.color(color)
                    self.resultDict[dictKey].append(tr)
                    
    def _identifyBasedOnHarmonicInterval(self, partNum1, partNum2, color, dictKey, testFunction, textFunction):
        if dictKey not in self.resultDict.keys():
            self.resultDict[dictKey] = []
        
        if partNum1 == None or partNum2 == None:
            for (partNum1,partNum2) in self.getAllPartNumPairs():
                self._identifyBasedOnHarmonicInterval(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        else:
            hIntvList = self.getHarmonicIntervals(partNum1, partNum2)
            
            for hIntv in hIntvList:
                if testFunction(hIntv) is not False: # True or value
                    tr = IntervalTheoryResult(hIntv)
                    tr.value = testFunction(hIntv)
                    tr.text = textFunction(hIntv, partNum1, partNum2)
                    if color is not None:
                        tr.color(color)
                    self.resultDict[dictKey].append(tr)
                    
    def _identifyBasedOnMelodicInterval(self, partNum, color, dictKey, testFunction, textFunction):
        if dictKey not in self.resultDict.keys():
            self.resultDict[dictKey] = []
        
        if partNum == None:
            for partNum in range(0, len(self._theoryScore.parts)):
                self._identifyBasedOnMelodicInterval(partNum, color, dictKey, testFunction, textFunction)
        else:
            mIntvList = self.getMelodicIntervals(partNum)
            
            for mIntv in mIntvList:
                if testFunction(mIntv) is not False: # True or value
                    tr = IntervalTheoryResult(mIntv)
                    tr.value = testFunction(mIntv)
                    tr.text = textFunction(mIntv, partNum)
                    if color is not None:
                        tr.color(color)
                    self.resultDict[dictKey].append(tr)
                    
    def _identifyBasedOnNote(self, partNum, color, dictKey, testFunction, textFunction):
        if dictKey not in self.resultDict.keys():
            self.resultDict[dictKey] = []
        
        if partNum == None:
            for partNum in range(0, len(self._theoryScore.parts)):
                self._identifyBasedOnNote(partNum, color, dictKey, testFunction, textFunction)
        else:
            nList = self.getNotesList(partNum)
            
            for n in nList:
                if testFunction(n) is not False: # True or value
                    tr = NoteTheoryResult(n)
                    tr.value = testFunction(n)
                    tr.text = textFunction(n, partNum)
                    if color is not None:
                        tr.color(color)
                    self.resultDict[dictKey].append(tr)
                       
    # Theory Errors using VLQ template
    
    def identifyParallelFifths(self, partNum1 = None, partNum2 = None, color = None):
        '''
        Identifies parallel fifths (calls :meth:`~music21.voiceLeading.parallelFifth`) between 
        two parts (if specified) or between all possible pairs of parts (if not specified) 
        and stores the resulting list of VLQTheoryResult objects in self.resultDict['parallelFifths']. 
        Optionally, a color attribute may be specified to color all corresponding notes in the score.
        
        >>> from music21 import *
        >>> from music21.demos import theoryAnalyzer
        >>> sc = stream.Score()
        >>> part0 = stream.Part()
        >>> p0measure1 = stream.Measure(number=1)
        >>> p0measure1.append(note.Note('c5'))
        >>> p0measure1.append(note.Note('d5'))
        >>> p0measure1.append(note.Note('e5'))
        >>> p0measure1.append(note.Note('g5'))
        >>> part0.append(p0measure1)
        >>> part1 = stream.Part()
        >>> p1measure1 = stream.Measure(number=1)
        >>> p1measure1.append(note.Note('c4'))
        >>> p1measure1.append(note.Note('g4'))
        >>> p1measure1.append(note.Note('a4'))
        >>> p1measure1.append(note.Note('c4'))
        >>> part1.append(p1measure1)
        >>> sc.insert(part0)
        >>> sc.insert(part1)
        >>> ta = TheoryAnalyzer(sc)
        >>> ta.identifyParallelFifths()
        >>> len(ta.resultDict['parallelFifths'])
        2
        >>> ta.resultDict['parallelFifths'][0].text
        'Parallel fifth at measure 1: Part 1 moves from D to E while part 2 moves from G to A'
        '''
        dictKey = 'parallelFifths'
        testFunction = lambda vlq: vlq.parallelFifth()
        textFunction = lambda vlq, pn1, pn2: "Parallel fifth at measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey,testFunction,textFunction)
        
    def identifyParallelOctaves(self, partNum1 = None, partNum2 = None, color = None):
        '''
        Identifies parallel octaves (calls :meth:`~music21.voiceLeading.parallelOctave`) between 
        two parts (if specified) or between all possible pairs of parts (if not specified) 
        and stores the resulting list of VLQTheoryResult objects in self.resultDict['parallelOctaves']. 
        Optionally, a color attribute may be specified to color all corresponding notes in the score.
        '''
        dictKey = 'parallelOctaves'
        testFunction = lambda vlq: vlq.parallelOctave()
        textFunction = lambda vlq, pn1, pn2: "Parallel octave at measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifyParallelUnisons(self, partNum1 = None, partNum2 = None, color = None):
        '''
        Identifies parallel unisons (calls :meth:`~music21.voiceLeading.parallelUnison`) between 
        two parts (if specified) or between all possible pairs of parts (if not specified) 
        and stores the resulting list of VLQTheoryResult objects in self.resultDict['parallelUnisons']. 
        Optionally, a color attribute may be specified to color all corresponding notes in the score.
        '''
        dictKey = 'parallelUnisons'
        testFunction = lambda vlq: vlq.parallelUnison()
        textFunction = lambda vlq, pn1, pn2: "Parallel unison at measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifyHiddenFifths(self, partNum1 = None, partNum2 = None, color = None):
        '''
        Identifies hidden fifths (calls :meth:`~music21.voiceLeading.hiddenFifth`) between 
        two parts (if specified) or between all possible pairs of parts (if not specified) 
        and stores the resulting list of VLQTheoryResult objects in self.resultDict['hiddenFifths']. 
        Optionally, a color attribute may be specified to color all corresponding notes in the score.
        '''
        dictKey = 'hiddenFifths'
        testFunction = lambda vlq: vlq.hiddenFifth()
        textFunction = lambda vlq, pn1, pn2: "Hidden fifth at measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifyHiddenOctaves(self, partNum1 = None, partNum2 = None, color = None):
        '''
        Identifies hidden octaves (calls :meth:`~music21.voiceLeading.hiddenOctave`) between 
        two parts (if specified) or between all possible pairs of parts (if not specified) 
        and stores the resulting list of VLQTheoryResult objects in self.resultDict['hiddenOctaves']. 
        Optionally, a color attribute may be specified to color all corresponding notes in the score.
        '''
        dictKey = 'hiddenOctaves'
        testFunction = lambda vlq: vlq.hiddenOctave()
        textFunction = lambda vlq, pn1, pn2: "Hidden octave at measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifyImproperResolutions(self, partNum1 = None, partNum2 = None, color = None):
        '''
        Identifies improper resolutions of dissonant intervals (calls :meth:`~music21.voiceLeading.improperResolution`) 
        between two parts (if specified) or between all possible pairs of parts (if not specified) 
        and stores the resulting list of VLQTheoryResult objects in self.resultDict['improperResolution']. 
        Optionally, a color attribute may be specified to color all corresponding notes in the score.
        '''
        dictKey = 'improperResolution'
        testFunction = lambda vlq: vlq.improperResolution()
        textFunction = lambda vlq, pn1, pn2: "Improper resolution of " + vlq.vIntervals[0].niceName +" at measure " + str(vlq.v1n1.measureNumber) +": "\
                 + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                 + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name + " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifyLeapNotSetWithStep(self, partNum1 = None, partNum2 = None, color = None):
        '''
        Identifies a leap/skip in one voice not set with a step in the other voice 
        (calls :meth:`~music21.voiceLeading.leapNotSetWithStep`) 
        between two parts (if specified) or between all possible pairs of parts (if not specified) 
        and stores the resulting list of VLQTheoryResult objects in self.resultDict['leapNotSetWithStep']. 
        Optionally, a color attribute may be specified to color all corresponding notes in the score.
        '''
        dictKey = 'LeapNotSetWithStep'
        testFunction = lambda vlq: vlq.leapNotSetWithStep()
        textFunction = lambda vlq, pn1, pn2: "Leap not set with step at measure " + str(vlq.v1n1.measureNumber) +": "\
                 + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                 + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name + " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
    
    # Theory Errors not using VLQ (therefore, not using template)      

    def identifyDissonantHarmonicIntervals(self, partNum1 = None, partNum2 = None, color = None, dictKey = 'dissonantHarmonicIntervals'):
        '''
        Identifies dissonant harmonic intervals (calls :meth:`~music21.interval.isConsonant`) 
        between the two parts (if specified) or between all possible pairs of parts (if not specified) 
        and stores the resulting list of IntervalTheoryResultObject objects in self.resultDict['dissonantHarmonicIntervals']. 
        Optionally, a color attribute may be specified to color all corresponding notes in the score.
        '''
        testFunction = lambda hIntv: hIntv is not None and not hIntv.isConsonant()
        textFunction = lambda hIntv, pn1, pn2: "Dissonant harmonic interval in measure " + str(hIntv.noteStart.measureNumber) +": " \
                     + str(hIntv.niceName) + " from " + str(hIntv.noteStart.name) + " to " + str(hIntv.noteEnd.name) \
                     + " between part " + str(pn1 + 1) + " and part " + str(pn2 + 1)
        self._identifyBasedOnHarmonicInterval(partNum1, partNum2, color, dictKey, testFunction, textFunction)

    def identifyDissonantMelodicIntervals(self, partNum = None, color = None, dictKey = 'dissonantHarmonicIntervals'):
        '''
        Identifies dissonant melodic intervals (A2, A4, d5, m7, M7) in the part (if specified) 
        or for all parts (if not specified) and stores the resulting list of 
        IntervalTheoryResultObject objects in self.resultDict['dissonantMelodicIntervals']. 
        Optionally, a color attribute may be specified to color all corresponding notes in the score.
        '''
        testFunction = lambda mIntv: mIntv is not None and mIntv.simpleName in ["A2","A4","d5","m7","M7"]
        textFunction = lambda mIntv, pn: "Dissonant melodic interval in part " + str(pn + 1) + " measure " + str(mIntv.noteStart.measureNumber) +": "\
                     + str(mIntv.niceName) + " from " + str(mIntv.noteStart.name) + " to " + str(mIntv.noteEnd.name)
        self._identifyBasedOnMelodicInterval(partNum, color, dictKey, testFunction, textFunction)                
    
    # Other Theory Properties to Identify:
    
    # Theory Properties using VLQ template
        
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

    # More Properties

    def identifyHarmonicIntervals(self, partNum1 = None, partNum2 = None, color = None, dictKey = 'harmonicIntervals'):
        testFunction = lambda hIntv: hIntv.generic.undirected
        textFunction = lambda hIntv, pn1, pn2: "harmonic interval"
        self._identifyBasedOnHarmonicInterval(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifyScaleDegrees(self, partNum = None, color = None, dictKey = 'scaleDegrees'):
        testFunction = lambda n: str(self.key.getScale().getScaleDegreeFromPitch(n.pitch))
        textFunction = lambda n, pn: "scale degree"
        self._identifyBasedOnNote(partNum, color, dictKey, testFunction, textFunction)
            
    # Combo Methods
    
    def identifyCommonPracticeErrors(self):
        '''
        wrapper class that calls all identify methods for common-practice counterpoint errors, 
        assigning a color identifier to each
        
        ParallelFifths = red, ParallelOctaves = orange, HiddenFifths = yellow, HiddenOctaves = green, 
        ParallelUnisons = blue, ImproperResolutions = purple, LeapNotSetWithStep = white, 
        DissonantHarmonicIntervals = magenta, DissonantMelodicIntervals = cyan
        '''
        self.identifyParallelFifths(color='red')
        self.identifyParallelOctaves(color='orange')
        self.identifyHiddenFifths(color='yellow')
        self.identifyHiddenOctaves(color='green')
        self.identifyParallelUnisons(color='blue')
        self.identifyImproperResolutions(color='purple')
        self.identifyLeapNotSetWithStep(color='white')
        self.identifyDissonantHarmonicIntervals(color='magenta')
        self.identifyDissonantMelodicIntervals(color='cyan')                
    
    # Output Methods
                
    def getResultsString(self, typeList=None):
        '''
        returns string of all results found by calling all identify methods on the TheoryAnalyzer score
        '''
        resultStr = ""
        for resultType in self.resultDict.keys():
            print resultType+":"
            if typeList is None or type in typeList:
                for result in self.resultDict[resultType]:
                    resultStr += result.text + "\n"
                resultStr += "\n"
                
        return resultStr
            
    def colorResults(self, color='red', typeList=None):
        '''
        colors the notes of all results found by calling all identify methods on Theory Analyzer.
        Optionally specify a color.
        '''
        for resultType in self.resultDict.keys():
            if typeList is None or type in typeList:
                for result in self.resultDict[resultType]:
                    result.color(color)
            
    def show(self):
        '''
        show the score, usually after running some identify and color routines
        '''
        self._theoryScore.show()
                
# Vertical Slice Object

class VerticalSlice(object):
    ''' A vertical slice of notes represents a list of notes that occur
    simultaneously in a score
    '''
    
    def __init__(self,noteList):
        self._noteList = noteList
        
    def getNote(self,partNum):
        return self._noteList[partNum]
    
    def __repr__(self):
        for (i,n) in enumerate(self._noteList):
            print str(i) + ": " + str(n)
    
# Theory Result Object

class TheoryResult(object):
    '''
    A TheoryResult object is used to store information about the results
    of the theory analysis. Includes references to the original elements
    in the score and a textual description of the error. Uses subclasses
    corresponding to the different types of objects determining the result
    '''
    
    def __init__(self):
        self.text = ""
        self.value = ""
        
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
                  
class IntervalTheoryResult(TheoryResult):
    def __init__(self, intv):
        TheoryResult.__init__(self)
        self.intv = intv
        
    def color(self, color='red'):
        self.intv.noteStart.color = color
        self.intv.noteEnd.color = color
        
# Note Theory Result Object
                  
class NoteTheoryResult(TheoryResult):
    def __init__(self, n):
        TheoryResult.__init__(self)
        self.n = n
        
    def color(self, color='red'):
        self.n.color = color
            
            
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
#        s = corpus.parse('bwv7.7')
        
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
        
#        ta.identifyObliqueMotion()
#        ta.identifySimilarMotion()
#        ta.identifyParallelMotion()
#        ta.identifyContraryMotion()
#        ta.identifyOutwardContraryMotion()
#        ta.identifyInwardContraryMotion()
#        ta.identifyAntiParallelMotion()

        print ta.getResultsString()
        ta.show()
        
    
if __name__ == "__main__":
#    music21.mainTest(Test)
    
    te = TestExternal()
    te.demo()
    