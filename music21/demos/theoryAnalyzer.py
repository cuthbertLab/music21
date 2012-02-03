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

from music21 import common
from music21 import converter
from music21 import corpus
from music21 import interval
from music21 import voiceLeading
from music21 import roman
from music21 import chord
from music21 import key
import string

import unittest


class TheoryAnalyzer(object):
    '''
    A Theory Analyzer is an object used for analyzing musical theory elements in scores. 
    It can identify, store, label, and output various counterpoint-related features 
    in a score (parallel fifths, harmonic intervals, melodic intervals, etc.)
    
    A Theory Analyzer must be passed a score containing parts with single voices 
    (no harmonies/chords within a part (yet!)).
    
    >>> from music21 import *
    >>> p = corpus.parse('bwv66.6')
    >>> ta = TheoryAnalyzer(p)
    '''
    
    def __init__(self, theoryScore, keyMeasureMap={}):
        self._theoryScore = theoryScore
        self._vlqCache = {} #Voice Leading Quartet
        self._tnlsCache = {} #Three Note Linear Segment
        self._tbtlsCache = {} #Two By Three Linear Segment Cache
        
        self.verticalSlices = self.getVerticalSlices()
        self.verticalSliceTriplets = self.getVerticalSliceTriplets()

        self.resultDict = {} #dictionary storing the results of any identification method queries
       
        self.keyMeasureMap = keyMeasureMap
        
    def _getkeyMeasureMap(self):
        return self._keyMeasureMap

    def _setkeyMeasureMap(self, keyMeasureMap):
        if isinstance(keyMeasureMap, dict):
            for measureNumber in keyMeasureMap.iterkeys():
                if not common.isNum(measureNumber):
                    raise TheoryAnalyzerException('got a measure number that is not an integer: %s', measureNumber)
            for keyValue in keyMeasureMap.itervalues():
                if common.isStr(keyValue):
                    try:
                        key.Key(key.convertKeyStringToMusic21KeyString(keyValue))
                    except: 
                        raise TheoryAnalyzerException('got a key signature string that is not supported: %s', keyValue)                               
                else:
                    try:
                        keyValue.isClassOrSubclass('Key')
                    except:   
                        raise TheoryAnalyzerException('got a key signature that is not a string or music21 key signature object: %s', keyValue)
            self._keyMeasureMap = keyMeasureMap
        else:
            raise TheoryAnalyzerException('keyMeasureMap must be a dictionary, not : %s', keyMeasureMap)
        

    keyMeasureMap = property(_getkeyMeasureMap, _setkeyMeasureMap, doc = '''
        specify the key of the theoryScore by measure in a dictionary correlating measure number to key, such as
        {1:'C', 2:'D', 3:'B-',5:'g'}. optionally pass in the music21 key object or the key string. 
        Check the music xml to verify measure numbers; pickup measures are usually 0.
    
        >>> from music21 import *
        >>> from music21.demos import theoryAnalyzer
        >>> s = stream.Score()
        >>> ta = TheoryAnalyzer(s)

        >>> ta.keyMeasureMap = {'1':'C'}
        Traceback (most recent call last):
        TheoryAnalyzerException: ('got a measure number that is not an integer: %s', '1')
        >>> ta.keyMeasureMap = {1:'a key'}
        Traceback (most recent call last):
        TheoryAnalyzerException: ('got a key signature string that is not supported: %s', 'a key')
        >>> ta.keyMeasureMap = {1:'C'}

        ''')     
        
    def keyAtMeasure(self, measureNumber):
        '''
        uses keyMeasureMap to return music21 key object. If keyMeasureMap not specified,
        returns key analysis of theory score as a whole. 
        
        >>> from music21 import *
        >>> from music21.demos import theoryAnalyzer
        >>> s = stream.Score()
        >>> ta = TheoryAnalyzer(s)
        >>> ta.keyMeasureMap = {1:'C', 2:'G', 4:'a', 7:'C'}
        >>> ta.keyAtMeasure(3)
        <music21.key.Key of G major>
        >>> ta.keyAtMeasure(7)
        <music21.key.Key of C major>
        
        OMIT_FROM_DOCS
        
        >>> ta.keyMeasureMap = {1:'G', 7:'D', 9:'F'}
        >>> ta.keyAtMeasure(8)
        <music21.key.Key of D major>
        >>> ta.keyAtMeasure(10)
        <music21.key.Key of F major>
        
        '''
        
        if self.keyMeasureMap:
            for dictKey in sorted(self.keyMeasureMap.iterkeys(), reverse=True):
                if measureNumber >= dictKey:                             
                    if common.isStr(self.keyMeasureMap[dictKey]):
                        return key.Key(key.convertKeyStringToMusic21KeyString(self.keyMeasureMap[dictKey]))
                    else:
                        return self.keyMeasureMap[dictKey]
            if measureNumber == 0: #just in case of a pickup measure
                if 1 in self.keyMeasureMap.keys():
                    return key.Key(key.convertKeyStringToMusic21KeyString(self.keyMeasureMap[1]))
            else:
                return self._theoryScore.analyze('key')
        else:
            return self._theoryScore.analyze('key')
        
    def getVerticalSlices(self):
        '''
        returns a list of a list of the :class:`~music21.voiceLeading.VerticalSlice` objects in)
        the Theory Analyzer's score. Note that it uses the combined rhythm of the parts 
        to determine what vertical slices to take.
        
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
            contentDict = {}
            partNum= 0
            for part in self._theoryScore.parts:
                
                el = part.flat.getElementAtOrBefore(c.offset,classList=['Note','Rest', 'Chord', 'Harmony'])
                if el.isClassOrSubclass(['Note', 'Chord', 'Harmony']):
                    contentDict[partNum] = el                    
                else:
                    #TODO: currently rests are stored as None...change to store them as music21 Rests soon
                    contentDict[partNum] = None # rests are stored as None...change to store them as Rests soon
                partNum+=1
            vs = voiceLeading.VerticalSlice(contentDict)
            vsList.append(vs)
               
        return vsList
    
    #  Intervals
    
    def getHarmonicIntervals(self, partNum1, partNum2):
        '''
        returns a list of all the harmonic intervals occurring between the two specified parts.
        
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
            
            nUpper = verticalSlice.noteFromPart(partNum1)
            nLower = verticalSlice.noteFromPart(partNum2)
            
            if nLower is None or nUpper is None:
                hIntv = None
            else:
                hIntv = interval.notesToInterval(nLower, nUpper)
            
            hInvList.append(hIntv)
                    
        return hInvList
    
    
    def getMelodicIntervals(self, partNum):
        '''
        returns a list of all the melodic intervals in the specified part.
        
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
        '''
        returns a list of notes present in the score. If Rests are present, appends None to the list
        '''
        noteList = []
        noteOrRestList = self._theoryScore.parts[partNum].flat.getElementsByClass(['Note','Rest'])
        for nr in noteOrRestList:
            if nr.isClassOrSubclass(['Note']):
                n = nr
            else:
                n = None
            
            noteList.append(n)
                    
        return noteList

    
    def getVLQs(self, partNum1, partNum2):
        '''
        extracts and returns a list of the :class:`~music21.voiceLeading.VoiceLeadingQuartet` 
        objects present between partNum1 and partNum2 in the score
        
        >>> from music21 import *
        >>> from music21.demos import theoryAnalyzer
        >>> sc = stream.Score()
        >>> part0 = stream.Part()
        >>> part0.append(note.Note('c4'))
        >>> part0.append(note.Note('g4'))
        >>> part0.append(note.Note('c5'))
        >>> sc.insert(part0)
        >>> part1 = stream.Part()
        >>> part1.append(note.Note('d4'))
        >>> part1.append(note.Note('e4'))
        >>> part1.append(note.Note('f5'))
        >>> sc.insert(part1)
        >>> ta = TheoryAnalyzer(sc)
        >>> len(ta.getVLQs(0,1))
        2
        '''
        # Caches the list of VLQs once they have been computed
        # for a specified set of partNums
        vlqCacheKey = str(partNum1) + "," + str(partNum2)
        
        if vlqCacheKey in self._vlqCache.keys():
            return self._vlqCache[vlqCacheKey]
        
        vlqList = []
        for (i, verticalSlice) in enumerate(self.verticalSlices[:-1]):
            nextVerticalSlice = self.verticalSlices[i + 1]
            
            v1n1 = verticalSlice.noteFromPart(partNum1)
            v1n2 = nextVerticalSlice.noteFromPart(partNum1)
            
            v2n1 = verticalSlice.noteFromPart(partNum2)
            v2n2 = nextVerticalSlice.noteFromPart(partNum2)
            
            vlq = voiceLeading.VoiceLeadingQuartet(v1n1,v1n2,v2n1,v2n2, key=self.keyAtMeasure(v1n1.measureNumber))
            vlqList.append(vlq)
            
            self._vlqCache[vlqCacheKey] = vlqList
        
        return vlqList

    def getThreeNoteLinearSegments(self, partNum):
        '''
        extracts and returns a list of the :class:`~music21.voiceLeading.ThreeNoteLinearSegment` 
        objects present in partNum in the score
        
        >>> from music21 import *
        >>> from music21.demos import theoryAnalyzer
        >>> sc = stream.Score()
        >>> part0 = stream.Part()
        >>> part0.append(note.Note('c4'))
        >>> part0.append(note.Note('g4'))
        >>> part0.append(note.Note('c5'))
        >>> part0.append(note.Note('c6'))
        >>> sc.insert(part0)
        >>> ta = TheoryAnalyzer(sc)
        >>> len(ta.getThreeNoteLinearSegments(0))
        2
        >>> ta.getThreeNoteLinearSegments(0)[1]
        <music21.voiceLeading.ThreeNoteLinearSegment n1=<music21.note.Note G> n2=<music21.note.Note C> n3=<music21.note.Note C> 

        '''
        # Caches the list of TNLS once they have been computed
        # for a specified partNum
        
        tnlsCacheKey = str(partNum)
        
        if tnlsCacheKey in self._tnlsCache.keys():
            return self._tnlsCache[tnlsCacheKey]
        else:
            self._tnlsCache[tnlsCacheKey] = self.getLinearSegments(partNum, 3)
        
        return self._tnlsCache[tnlsCacheKey]

    def getLinearSegments(self, partNum, lengthLinearSegment):
        '''
        extracts and returns a list of all the linear segments in the piece at 
        the partNum specified, the length of which specified by lengthLinearSegment: 
        Currently Supported: :class:`~music21.voiceLeading.ThreeNoteLinearSegment` 
        
        >>> from music21 import *
        >>> from music21.demos import theoryAnalyzer
        >>> sc = stream.Score()
        >>> part0 = stream.Part()
        >>> part0.append(note.Note('c4'))
        >>> part0.append(note.Note('g4'))
        >>> part0.append(note.Note('c5'))
        >>> part0.append(note.Note('c6'))
        >>> sc.insert(part0)
        >>> ta = TheoryAnalyzer(sc)
        >>> len(ta.getLinearSegments(0,3))
        2
        '''
        linearSegments = []
        for i in range(0, len(self.verticalSlices)-lengthLinearSegment+1):
            notes = []
            for n in range(0,lengthLinearSegment):
                notes.append(self.verticalSlices[i+n].noteFromPart(partNum))           
            
            if lengthLinearSegment == 3:
                tnls = voiceLeading.ThreeNoteLinearSegment()
                tnls.n1 = notes[0]
                tnls.n2 = notes[1]
                
                tnls.n3 = notes[2]
                linearSegments.append(tnls)

        return linearSegments


    def getVerticalSliceTriplets(self):
        '''
        extracts and returns a list of the :class:`~music21.voiceLeading.VerticalSliceTriplet` 
        objects present in the score
        
        >>> from music21 import *
        >>> from music21.demos import theoryAnalyzer
        >>> sc = stream.Score()
        >>> part0 = stream.Part()
        >>> part1 = stream.Part()
        >>> part0.append(note.Note('c4'))
        >>> part0.append(note.Note('g4'))
        >>> part0.append(note.Note('c5'))
        >>> part1.append(note.Note('e4'))
        >>> part1.append(note.Note('f4'))
        >>> part1.append(note.Note('a5'))
        >>> sc.insert(part0)
        >>> sc.insert(part1)
        >>> ta = TheoryAnalyzer(sc)
        >>> len(ta.getVerticalSliceTriplets())
        1
        >>> ta.getVerticalSliceTriplets()[0]
        <music21.voiceLeading.VerticalSliceTriplet vs1=<music21.voiceLeading.VerticalSlice contentDict={0: <music21.note.Note C>, 1: <music21.note.Note E>}   vs2=<music21.voiceLeading.VerticalSlice contentDict={0: <music21.note.Note G>, 1: <music21.note.Note F>}   vs3=<music21.voiceLeading.VerticalSlice contentDict={0: <music21.note.Note C>, 1: <music21.note.Note A>}   

        
        '''

        verticalSliceTriplets = []
        for i in range(0, len(self.verticalSlices)-2):
            currentVerticalSlice = self.verticalSlices[i]
            nextVerticalSlice = self.verticalSlices[i+1]
            nextNextVerticalSlice = self.verticalSlices[i+2]
            vst = voiceLeading.VerticalSliceTriplet(currentVerticalSlice, nextVerticalSlice, nextNextVerticalSlice)
            verticalSliceTriplets.append(vst)
        return verticalSliceTriplets


#    def getTwoByThreeLinearSegments(self, partNum1, partNum2):
#        tbtlsCacheKey = str(partNum1) + "," + str(partNum2)
#        if tbtlsCacheKey in self._tbtlsCache.keys():
#            return self._tbtlsCache[tbtlsCacheKey]
#        else:      
#            matrixList = []
#
#            ls1List = self.getThreeNoteLinearSegments(partNum1)
#            ls2List = self.getThreeNoteLinearSegments(partNum2)
#            
#            for ls1, ls2 in zip(ls1List, ls2List):
#                m = voiceLeading.TwoByThreeMatrix(ls1, ls2)
#              
#                matrixList.append(m)
#                
#            self._tbtlsCache[tbtlsCacheKey] = matrixList
#            return matrixList
        
    
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
    
    def _identifyBasedOnVLQ(self, partNum1, partNum2, color, dictKey, testFunction, textFunction, startIndex=0, endIndex = None):
        '''
        startIndex is the first VLQ in the list to start with (0 is default). endIndex is the first VLQ in list not to search 
        (length of VLQ list is default), meaning default values are to search the entire vlqList
        '''
        if dictKey not in self.resultDict.keys():
            self.resultDict[dictKey] = []
        
        if partNum1 == None or partNum2 == None:
            for (partNum1,partNum2) in self.getAllPartNumPairs():
                self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction, startIndex, endIndex)
        else:
            vlqList = self.getVLQs(partNum1, partNum2)
            
            if endIndex == None and startIndex >=0:
                endIndex = len(vlqList)
            for vlq in vlqList[startIndex:endIndex]:
                if testFunction(vlq) is not False: # True or value
                    tr = VLQTheoryResult(vlq)
                    tr.value = testFunction(vlq)
                    tr.text = textFunction(vlq, partNum1, partNum2)
                    tr.value = textFunction(vlq, partNum1, partNum2)

                    if color is not None:
                        tr.color(color)
                    self.resultDict[dictKey].append(tr)
                    
    def _identifyBasedOnHarmonicInterval(self, partNum1, partNum2, color, dictKey, testFunction, textFunction, valueFunction=None):
        if valueFunction == None:
            valueFunction = testFunction
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
                    tr.value = valueFunction(hIntv)
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
            nList = self.getNotes(partNum)
            
            for n in nList:
                if testFunction(n) is not False: # True or value
                    tr = NoteTheoryResult(n)
                    tr.value = testFunction(n)
                    tr.text = textFunction(n, partNum)
                    if color is not None:
                        tr.color(color)
                    self.resultDict[dictKey].append(tr)
                       
    def _identifyBasedOnVerticalSlice(self, color, dictKey, testFunction, textFunction, responseOffsetMap=[]):
        if dictKey not in self.resultDict.keys():
            self.resultDict[dictKey] = []             
        for vs in self.verticalSlices:
            if responseOffsetMap and vs.offset(leftAlign=True) not in responseOffsetMap:
                continue
            if testFunction(vs) is not False:
                tr = VerticalSliceTheoryResult(vs)
                tr.value = testFunction(vs)
                tr.text = textFunction(vs, testFunction(vs))
                if color is not None: 
                    tr.color(color)
                self.resultDict[dictKey].append(tr)
    
    def _identifyBasedOnVerticalSliceTriplet(self, partNumToIdentify, color, dictKey, testFunction, textFunction):
        if dictKey not in self.resultDict.keys():
            self.resultDict[dictKey] = []             

        if partNumToIdentify == None:
            for partNum in range(0,len(self._theoryScore.parts)):
                self._identifyBasedOnVerticalSliceTriplet(partNum, color, dictKey, testFunction, textFunction)
        else:
            for vs in self.verticalSliceTriplets:
                if testFunction(vs, partNumToIdentify) is not False:
                    tr = VerticalSliceTripletTheoryResult(vs, partNumToIdentify)
                    tr.text = textFunction(vs, partNumToIdentify)
                    if color is not None: 
                        tr.color(color)
                    self.resultDict[dictKey].append(tr)
    
    def _identifyBasedOnThreeNoteLinearSegment(self, partNum, color, dictKey, testFunction, textFunction):
        if dictKey not in self.resultDict.keys():
            self.resultDict[dictKey] = []             

        if partNum == None:
            for partNum in range(0,len(self._theoryScore.parts)):
                self._identifyBasedOnThreeNoteLinearSegment(partNum, color, dictKey, testFunction, textFunction)
        else:
            tnlsList = self.getThreeNoteLinearSegments(partNum)

            for tnls in tnlsList:
                if testFunction(tnls) is not False:
                    tr = ThreeNoteLinearSegmentTheoryResult(tnls)
                    tr.value = testFunction(tnls)
                    tr.text = textFunction(tnls, partNum)
                    if color is not None: 
                        tr.color(color)
                    self.resultDict[dictKey].append(tr)
  
#    def _identifyBasedOnTwoByThreeLinearSegment(self, partNum1, partNum2, partNumToIdentify, color, dictKey, testFunction, textFunction):
#        if dictKey not in self.resultDict.keys():
#            self.resultDict[dictKey] = []             
#
#        if partNum1 == None or partNum2 == None:
#            for partNum in range(0,len(self._theoryScore.parts)):
#                self._identifyBasedOnTwoByThreeLinearSegment(partNum1, partNum2, partNumToIdentify, color, dictKey, testFunction, textFunction)
#        else:
#            tbtlsList = self.getTwoByThreeLinearSegments(partNum1, partNum2)
#
#            for tbtls in tbtlsList:
#                if testFunction(tbtls, partNumToIdentify) is not False:
#                    tr = TwoByThreeLinearSegmentTheoryResult(tbtls, partNumToIdentify)
#                    #tr.value = testFunction(tbtls, partNum)
#                    tr.text = textFunction(tbtls, partNumToIdentify)
#                    if color is not None: 
#                        tr.color(color)
#                    self.resultDict[dictKey].append(tr)

               
    # Theory Errors using VLQ template
    
    def identifyParallelFifths(self, partNum1 = None, partNum2 = None, color = None, dictKey = 'parallelFifths'):
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
        'Parallel fifth in measure 1: Part 1 moves from D to E while part 2 moves from G to A'
        '''
        testFunction = lambda vlq: vlq.parallelFifth()
        textFunction = lambda vlq, pn1, pn2: "Parallel fifth in measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey,testFunction,textFunction)
        
    def identifyParallelOctaves(self, partNum1 = None, partNum2 = None, color = None, dictKey = 'parallelOctaves'):
        '''
        Identifies parallel octaves (calls :meth:`~music21.voiceLeading.parallelOctave`) between 
        two parts (if specified) or between all possible pairs of parts (if not specified) 
        and stores the resulting list of VLQTheoryResult objects in self.resultDict['parallelOctaves']. 
        Optionally, a color attribute may be specified to color all corresponding notes in the score.
        '''
        
        testFunction = lambda vlq: vlq.parallelOctave()
        textFunction = lambda vlq, pn1, pn2: "Parallel octave in measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifyParallelUnisons(self, partNum1 = None, partNum2 = None, color = None,dictKey = 'parallelUnisons'):
        '''
        Identifies parallel unisons (calls :meth:`~music21.voiceLeading.parallelUnison`) between 
        two parts (if specified) or between all possible pairs of parts (if not specified) 
        and stores the resulting list of VLQTheoryResult objects in self.resultDict['parallelUnisons']. 
        Optionally, a color attribute may be specified to color all corresponding notes in the score.
        '''
        
        testFunction = lambda vlq: vlq.parallelUnison()
        textFunction = lambda vlq, pn1, pn2: "Parallel unison in measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifyHiddenFifths(self, partNum1 = None, partNum2 = None, color = None,dictKey = 'hiddenFifths'):
        '''
        Identifies hidden fifths (calls :meth:`~music21.voiceLeading.hiddenFifth`) between 
        two parts (if specified) or between all possible pairs of parts (if not specified) 
        and stores the resulting list of VLQTheoryResult objects in self.resultDict['hiddenFifths']. 
        Optionally, a color attribute may be specified to color all corresponding notes in the score.
        '''
        
        testFunction = lambda vlq: vlq.hiddenFifth()
        textFunction = lambda vlq, pn1, pn2: "Hidden fifth in measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifyHiddenOctaves(self, partNum1 = None, partNum2 = None, color = None,dictKey = 'hiddenOctaves'):
        '''
        Identifies hidden octaves (calls :meth:`~music21.voiceLeading.hiddenOctave`) between 
        two parts (if specified) or between all possible pairs of parts (if not specified) 
        and stores the resulting list of VLQTheoryResult objects in self.resultDict['hiddenOctaves']. 
        Optionally, a color attribute may be specified to color all corresponding notes in the score.
        '''
        
        testFunction = lambda vlq: vlq.hiddenOctave()
        textFunction = lambda vlq, pn1, pn2: "Hidden octave in measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifyImproperResolutions(self, partNum1 = None, partNum2 = None, color = None,dictKey = 'improperResolution'):
        '''
        Identifies improper resolutions of dissonant intervals (calls :meth:`~music21.voiceLeading.improperResolution`) 
        between two parts (if specified) or between all possible pairs of parts (if not specified) 
        and stores the resulting list of VLQTheoryResult objects in self.resultDict['improperResolution']. 
        Optionally, a color attribute may be specified to color all corresponding notes in the score.
        '''
        
        testFunction = lambda vlq: vlq.improperResolution()
        textFunction = lambda vlq, pn1, pn2: "Improper resolution of " + vlq.vIntervals[0].simpleNiceName +" in measure " + str(vlq.v1n1.measureNumber) +": "\
                 + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                 + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name + " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifyLeapNotSetWithStep(self, partNum1 = None, partNum2 = None, color = None,dictKey = 'LeapNotSetWithStep'):
        '''
        Identifies a leap/skip in one voice not set with a step in the other voice 
        (calls :meth:`~music21.voiceLeading.leapNotSetWithStep`) 
        between two parts (if specified) or between all possible pairs of parts (if not specified) 
        and stores the resulting list of VLQTheoryResult objects in self.resultDict['leapNotSetWithStep']. 
        Optionally, a color attribute may be specified to color all corresponding notes in the score.
        '''
        
        testFunction = lambda vlq: vlq.leapNotSetWithStep()
        textFunction = lambda vlq, pn1, pn2: "Leap not set with step in measure " + str(vlq.v1n1.measureNumber) +": "\
                 + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                 + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name + " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
    
    def identifyOpensIncorrectly(self, partNum1 = None, partNum2 = None, color = None,dictKey = 'opensIncorrectly'):
        '''
        Identifies if the piece opens correctly; calls :meth:`~music21.voiceLeading.opensIncorrectly`
        
        '''
        
        testFunction = lambda vlq: vlq.opensIncorrectly()
        textFunction = lambda vlq, pn1, pn2: "Opening harmony is not in style"
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction, startIndex = 0, endIndex = 1)
        
    def identifyClosesIncorrectly(self, partNum1 = None, partNum2 = None, color = None,dictKey = 'closesIncorrectly'):
        '''
        Identifies if the piece closes correctly; calls :meth:`~music21.voiceLeading.closesIncorrectly`
        '''
        testFunction = lambda vlq: vlq.closesIncorrectly() 
        textFunction = lambda vlq, pn1, pn2: "Closing harmony is not in style"
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction, startIndex=-1)    

    # Using the Three Note Linear Segment Template
    def identifyCouldBePassingTone(self, partNum = None, color = None, dictKey = 'possiblePassingTone'):
        testFunction = lambda tnls: tnls.couldBePassingTone()
        textFunction = lambda tnls, pn: tnls.n2.name + ' in part ' + str(pn+1) + ' identified as a possible passing tone '
        self._identifyBasedOnThreeNoteLinearSegment(partNum, color, dictKey, testFunction, textFunction)

    # Using the Vertical Slice Triplet Template
    def identifyUnaccentedPassingTones(self, partNumToIdentify = None, color = None, dictKey = 'unaccentedPassingTone'):
        testFunction = lambda vst, pn: vst.hasUnaccentedPassingTone(pn)
        textFunction = lambda vst, pn: 'PRINT IDENTIFIED PASSING TONE' + ' in part ' + str(pn+1) + ' identified as an unaccented passing tone '
        self._identifyBasedOnVerticalSliceTriplet(partNumToIdentify, color, dictKey, testFunction, textFunction)

    def identifyUnaccentedNeighborTones(self, partNumToIdentify = None, color = None, dictKey = 'unaccentedNeighborTone'):
        testFunction = lambda vst, pn: vst.hasUnaccentedNeighborTone(pn)
        textFunction = lambda vst, pn: 'PRINT IDENTIFIED NEIGHBOR TONE' + ' in part ' + str(pn+1) + ' identified as an unaccented passing tone '
        self._identifyBasedOnVerticalSliceTriplet(partNumToIdentify, color, dictKey, testFunction, textFunction)


    def identifyDissonantHarmonicIntervals(self, partNum1 = None, partNum2 = None, color = None, dictKey = 'dissonantHarmonicIntervals'):
        '''
        Identifies dissonant harmonic intervals (calls :meth:`~music21.interval.isConsonant`) 
        between the two parts (if specified) or between all possible pairs of parts (if not specified) 
        and stores the resulting list of IntervalTheoryResultObject objects in self.resultDict['dissonantHarmonicIntervals']. 
        Optionally, a color attribute may be specified to color all corresponding notes in the score.
        '''
        testFunction = lambda hIntv: hIntv is not None and not hIntv.isConsonant()
        textFunction = lambda hIntv, pn1, pn2: "Dissonant harmonic interval in measure " + str(hIntv.noteStart.measureNumber) +": " \
                     + str(hIntv.simpleNiceName) + " from " + str(hIntv.noteStart.name) + " to " + str(hIntv.noteEnd.name) \
                     + " between part " + str(pn1 + 1) + " and part " + str(pn2 + 1)
        self._identifyBasedOnHarmonicInterval(partNum1, partNum2, color, dictKey, testFunction, textFunction)

#
#    def identifyNotInStyleDissonantIntervals(self, partNum1 = None, partNum2 = None, color = None, dictKey = 'dissonantHarmonicIntervals'):
#        '''
#        Identifies dissonant harmonic intervals that are not passing tones or neighbor tones
#        
#        '''
#        testFunction = lambda hIntv: hIntv is not None and not hIntv.isConsonant()
#        
#        textFunction = lambda hIntv, pn1, pn2: "Dissonant harmonic interval in measure " + str(hIntv.noteStart.measureNumber) +": " \
#                     + str(hIntv.niceName) + " from " + str(hIntv.noteStart.name) + " to " + str(hIntv.noteEnd.name) \
#                     + " between part " + str(pn1 + 1) + " and part " + str(pn2 + 1)
#        self._identifyBasedOnHarmonicInterval(partNum1, partNum2, color, dictKey, testFunction, textFunction)

    def identifyDissonantMelodicIntervals(self, partNum = None, color = None, dictKey = 'dissonantMelodicIntervals'):
        '''
        Identifies dissonant melodic intervals (A2, A4, d5, m7, M7) in the part (if specified) 
        or for all parts (if not specified) and stores the resulting list of 
        IntervalTheoryResultObject objects in self.resultDict['dissonantMelodicIntervals']. 
        Optionally, a color attribute may be specified to color all corresponding notes in the score.
        '''
        testFunction = lambda mIntv: mIntv is not None and mIntv.simpleName in ["A2","A4","d5","m7","M7"]
        textFunction = lambda mIntv, pn: "Dissonant melodic interval in part " + str(pn + 1) + " measure " + str(mIntv.noteStart.measureNumber) +": "\
                     + str(mIntv.simpleNiceName) + " from " + str(mIntv.noteStart.name) + " to " + str(mIntv.noteEnd.name)
        self._identifyBasedOnMelodicInterval(partNum, color, dictKey, testFunction, textFunction)                
    
    def identifyTonicAndDominantRomanNumerals(self, color = None, dictKey = 'romanNumerals', responseOffsetMap = []):
        '''
        Identifies the roman numerals in the piece by iterating throgh the vertical slices and figuring
        out which roman numeral best corresponds to that vertical slice. Optionally specify the responseOffsetMap
        which limits the resultObjects returned to only those with verticalSlice's.offset(leftAlign=True) included
        in the list. For example, if only roman numerals were to be written for the vertical slice at offset 0, 6, and 7
        in the piece, pass responseOffsetMap = [0,6,7]
        '''
        def testFunction(vs):
            noteList = vs.noteList
            if not None in noteList:
                inChord = chord.Chord(noteList)
                pitchNameList = []
                for x in noteList:
                    pitchNameList.append(x.pitch.name)
                inKey = self.keyAtMeasure(noteList[0].measureNumber)
                chordBass = noteList[-1]
                inChord.bass(chordBass.pitch)
                oneRoot =  inKey.pitchFromDegree(1)
                fiveRoot = inKey.pitchFromDegree(5)
                oneChordIdentified = False
                fiveChordIdentified = False
                if oneRoot.name in pitchNameList:
                    oneChordIdentified = True
                elif fiveRoot.name in pitchNameList:
                    fiveChordIdentified = True
                else:
                    oneRomanChord = roman.RomanNumeral('I7', inKey).pitches
                    fiveRomanChord = roman.RomanNumeral('V7', inKey).pitches
                    
                    onePitchNameList = []
                    for x in oneRomanChord:
                        onePitchNameList.append(x.name)
                    
                    fivePitchNameList = []
                    for x in fiveRomanChord:
                        fivePitchNameList.append(x.name)                    
                    
                    oneMatches = len(set(onePitchNameList) & set(pitchNameList))
                    fiveMatches = len(set(fivePitchNameList) & set(pitchNameList))
                    if  oneMatches > fiveMatches and oneMatches > 0:
                        oneChordIdentified = True
                    elif oneMatches < fiveMatches and fiveMatches > 0:
                        fiveChordIdentified = True
                    else:
                        return False
                    
                if oneChordIdentified:
                    rootScaleDeg = common.toRoman(1)
                    if inKey.mode == 'minor':
                        rootScaleDeg = rootScaleDeg.lower()
                    else:
                        rootScaleDeg = rootScaleDeg.upper()
                    inChord.root(oneRoot)
                elif fiveChordIdentified:
                    rootScaleDeg = common.toRoman(5)
                    inChord.root(fiveRoot)
                else:
                    return False
                try:
                    if inChord.inversionName() != 53:
                        rn = rootScaleDeg + str(inChord.inversionName())
                    else:
                        rn = rootScaleDeg
                except:
                    rn = rootScaleDeg
                return rn
            else:
                return False
           
        def textFunction(vs, rn):
            notes = ''
            for n in vs.noteList:
                notes+= n.name + ','
            notes = notes[:-1]
            return "Roman Numeral of " + notes + ' is ' + rn
        self._identifyBasedOnVerticalSlice(color, dictKey, testFunction, textFunction, responseOffsetMap=responseOffsetMap)                
    
    def identifyRomanNumerals(self, color = None, dictKey = 'romanNumerals', responseOffsetMap = []):
        '''
        Identifies the roman numerals in the piece by iterating throgh the vertical slices and figuring
        out which roman numeral best corresponds to that vertical slice. (calls :meth:`~music21.roman.fromChordAndKey`)
        
        Optionally specify the responseOffsetMap which limits the resultObjects returned to only those with 
        verticalSlice's.offset(leftAlign=True) included in the list. For example, if only roman numerals
        were to be written for the vertical slice at offset 0, 6, and 7 in the piece, pass responseOffsetMap = [0,6,7]
        '''
        def testFunction(vs, responseOffsetMap=[]):
            noteList = vs.noteList

            if not None in noteList:
                inChord = chord.Chord(noteList)
                inChord.bass(noteList[-1])
                inKey = self.keyAtMeasure(noteList[0].measureNumber)
                rn = roman.fromChordAndKey(inChord, inKey)
                return rn
            else:
                return False
           
        def textFunction(vs, rn):
            notes = ''
            for n in vs.noteList:
                notes+= n.name + ','
            notes = notes[:-1]
            return "Roman Numeral of " + notes + ' is ' + rn
        self._identifyBasedOnVerticalSlice(color, dictKey, testFunction, textFunction, responseOffsetMap=responseOffsetMap)                
    
    # Other Theory Properties to Identify:
    
    # Theory Properties using VLQ template
        
    def identifyObliqueMotion(self, partNum1 = None, partNum2 = None, color = None):
        dictKey = 'obliqueMotion'
        testFunction = lambda vlq: vlq.obliqueMotion()
        textFunction = lambda vlq, pn1, pn2: "Oblique motion in measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifySimilarMotion(self, partNum1 = None, partNum2 = None, color = None):
        dictKey = 'similarMotion'
        testFunction = lambda vlq: vlq.similarMotion()
        textFunction = lambda vlq, pn1, pn2: "Similar motion in measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifyParallelMotion(self, partNum1 = None, partNum2 = None, color = None):
        dictKey = 'parallelMotion'
        testFunction = lambda vlq: vlq.parallelMotion()
        textFunction = lambda vlq, pn1, pn2: "Parallel motion in measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifyContraryMotion(self, partNum1 = None, partNum2 = None, color = None):
        dictKey = 'contraryMotion'
        testFunction = lambda vlq: vlq.contraryMotion()
        textFunction = lambda vlq, pn1, pn2: "Contrary motion in measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifyOutwardContraryMotion(self, partNum1 = None, partNum2 = None, color = None):
        dictKey = 'outwardContraryMotion'
        testFunction = lambda vlq: vlq.outwardContraryMotion()
        textFunction = lambda vlq, pn1, pn2: "Outward contrary motion in measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifyInwardContraryMotion(self, partNum1 = None, partNum2 = None, color = None):
        dictKey = 'inwardContraryMotion'
        testFunction = lambda vlq: vlq.inwardContraryMotion()
        textFunction = lambda vlq, pn1, pn2: "Inward contrary motion in measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifyAntiParallelMotion(self, partNum1 = None, partNum2 = None, color = None):
        dictKey = 'antiParallelMotion'
        testFunction = lambda vlq: vlq.antiParallelMotion()
        textFunction = lambda vlq, pn1, pn2: "Anti-parallel motion in measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)

    # More Properties

    def identifyHarmonicIntervals(self, partNum1 = None, partNum2 = None, color = None, dictKey = 'harmonicIntervals'):
        testFunction = lambda hIntv: hIntv.generic.undirected if hIntv is not None else False
        textFunction = lambda hIntv, pn1, pn2: "harmonic interval between" + hIntv.noteStart.name + ' and ' + hIntv.noteEnd.name + \
                     ' between parts ' + str(pn1 + 1) + ' and ' + str(pn2) + ' is ' + str(hIntv.niceName)
        def valueFunction(self, hIntv):
            augordimIntervals = ['A4','d5']
            if hIntv.simpleName in augordimIntervals:
                return hIntv.simpleName
            else:
                value = hIntv.generic.undirected
                while value > 9:
                    value -= 7
                return value
        self._identifyBasedOnHarmonicInterval(partNum1, partNum2, color, dictKey, testFunction, textFunction, valueFunction)
        
    def identifyScaleDegrees(self, partNum = None, color = None, dictKey = 'scaleDegrees'):
        testFunction = lambda n:  (str(self.keyAtMeasure(n.measureNumber).getScale().getScaleDegreeFromPitch(n.pitch)) ) if n is not None else False
        textFunction = lambda n, pn: "scale degree"
        self._identifyBasedOnNote(partNum, color, dictKey, testFunction, textFunction)
            
    def identifyMotionType(self, partNum1 = None, partNum2 = None, color = None, dictKey = 'motionType'):
        testFunction = lambda vlq: vlq.motionType()
        textFunction = lambda vlq, pn1, pn2: (vlq.motionType() + ' Motion at '+ str(vlq.v1n1.measureNumber) +": " \
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name)  if vlq.motionType() != "No Motion" else 'No motion'
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    # Combo Methods
    
    def identifyCommonPracticeErrors(self, partNum1,partNum2,dictKey='commonPracticeErrors'):
        '''
        wrapper class that calls all identify methods for common-practice counterpoint errors, 
        assigning a color identifier to each
        
        ParallelFifths = red, ParallelOctaves = orange, HiddenFifths = yellow, HiddenOctaves = green, 
        ParallelUnisons = blue, ImproperResolutions = purple, LeapNotSetWithStep = white, 
        DissonantHarmonicIntervals = magenta, DissonantMelodicIntervals = cyan
        '''
        self.identifyParallelFifths(partNum1, partNum2, dictKey = dictKey, color='red')
        self.identifyParallelOctaves(partNum1, partNum2, dictKey = dictKey, color='yellow')
        self.identifyHiddenFifths(partNum1, partNum2, dictKey = dictKey, color='orange')
        self.identifyHiddenOctaves(partNum1, partNum2, dictKey = dictKey, color='green')
        self.identifyParallelUnisons(partNum1, partNum2, dictKey = dictKey, color='blue')
        self.identifyImproperResolutions(partNum1, partNum2, dictKey = dictKey, color='purple')
        #self.identifyLeapNotSetWithStep(partNum1, partNum2, dictKey = dictKey, color='white')
        #self.identifyDissonantHarmonicIntervals(partNum1, partNum2, dictKey = dictKey, color='magenta')
        self.identifyDissonantMelodicIntervals(partNum1,dictKey = dictKey, color='cyan')  
        self.identifyOpensIncorrectly(partNum1, partNum2,dictKey = dictKey, color='brown')
        #self.identifyClosesIncorrectly(partNum1, partNum2,dictKey = dictKey, color='gray')              
    
    # Output Methods
                
    def getResultsString(self, typeList=None):
        '''
        returns string of all results found by calling all identify methods on the TheoryAnalyzer score
        '''
        resultStr = ""
        for resultType in self.resultDict.keys():
            if typeList is None or resultType in typeList:
                resultStr+=resultType+": \n"
                for result in self.resultDict[resultType]:
                    resultStr += result.text
                    resultStr += "\n"
                
        return resultStr
    
    def getHTMLResultsString(self, typeList=None):
        '''
        returns string of all results found by calling all identify methods on the TheoryAnalyzer score
        '''
        resultStr = ""
        for resultType in self.resultDict.keys():
            if typeList is None or resultType in typeList:
                resultStr+="<b>"+resultType+"</B>: <br /><ul>"
                for result in self.resultDict[resultType]:
                    resultStr += "<li style='color:"+result.currentColor+"'><b>"+string.replace(result.text,':',"</b>:<span style='color:black'>")+"</span></li>"
                resultStr += "</ul><br />"
                
        return resultStr
            
            
    def colorResults(self, color='red', typeList=None):
        '''
        colors the notes of all results found by calling all identify methods on Theory Analyzer.
        Optionally specify a color.
        '''
        for resultType in self.resultDict.keys():
            if typeList is None or resultType in typeList:
                for result in self.resultDict[resultType]:
                    result.color(color)
            
    def show(self):
        '''
        show the score, usually after running some identify and color routines
        '''
        self._theoryScore.show()
                

class TheoryAnalyzerException(music21.Music21Exception):
    pass

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
        self.currentColor = ""
        
    def color(self,color):
        self.color = color

# VLQ Theory Result Object

class VLQTheoryResult(TheoryResult):
    def __init__(self, vlq):
        TheoryResult.__init__(self)
        self.vlq = vlq
        
    def color(self, color='red'):
        self.currentColor = color
        self.vlq.v1n1.color = color
        self.vlq.v1n2.color = color
        self.vlq.v2n1.color = color
        self.vlq.v2n2.color = color
        
    def offset(self):
        offset = self.vlq.v1n2.offset
        if self.vlq.v2n2.offset > offset:
            offset = self.vlq.v2n2.offset
        return offset

# Interval Theory Result Object
                  
class IntervalTheoryResult(TheoryResult):
    def __init__(self, intv):
        TheoryResult.__init__(self)
        self.intv = intv
        
    def color(self, color='red'):
        self.currentColor = color
        self.intv.noteStart.color = color
        self.intv.noteEnd.color = color
        
    def offset(self):
        offset = self.intv.noteStart.offset
        if self.intv.noteEnd.offset > offset:
            offset = self.intv.noteEnd.offset
        return offset
        
# Note Theory Result Object
                  
class NoteTheoryResult(TheoryResult):
    def __init__(self, n):
        TheoryResult.__init__(self)
        self.n = n
        
    def color(self, color='red'):
        self.currentColor  = color
        self.n.color = color
            
class VerticalSliceTheoryResult(TheoryResult):            
    def __init__(self, vs): 
        TheoryResult.__init__(self)
        self.vs = vs
        
    def color(self, color ='red'):
        for n in self.vs.noteList:
            n.color = color
            
class ThreeNoteLinearSegmentTheoryResult(TheoryResult):            
    def __init__(self, tnls): 
        TheoryResult.__init__(self)
        self.tnls = tnls
        
    def color(self, color ='red'):
        #self.tnls.n1.color = color
        self.tnls.n2.color = color
        #self.tnls.n3.color = color
            
#class TwoByThreeLinearSegmentTheoryResult(TheoryResult):            
#    def __init__(self, tbtls, partNumToColor = None): 
#        TheoryResult.__init__(self)
#        self.tbtls = tbtls
#        self.partNumToColor = partNumToColor
#        
#    def color(self, color ='red'):
#        if self.partNumToColor == 0:
#            self.tbtls.tnls1.n2.color = color
#        elif self.partNumToColor == 1:
#            self.tbtls.tnls1.n2.color = color
  
class VerticalSliceTripletTheoryResult(TheoryResult):
    def __init__(self, vst, partNumToColor = None): 
        TheoryResult.__init__(self)
        self.vst = vst
        self.partNumToColor = partNumToColor

    def color(self, color ='red'):
        if self.partNumToColor != None:
            self.vst.tnlsList[self.partNumToColor].n2.color = color 
# ------------------------------------------------------------

class Test(unittest.TestCase):
    
    def runTest(self):
        pass
        
class TestExternal(unittest.TestCase):
    
    def runTest(self):
        pass 
    
    def demo(self):

        #s = converter.parse('C:/Users/bhadley/Dropbox/Music21Theory/WWNortonWorksheets/WWNortonXMLFiles/XML11_worksheets/S11_1_II_cleaned.xml')
        s = converter.parse('/Users/larsj/Dropbox/Music21Theory/WWNortonWorksheets/WWNortonXMLFiles/XML11_worksheets/S11_1_II_cleaned.xml')
#        s = converter.parse('C:/Users/bhadley/Dropbox/Music21Theory/WWNortonWorksheets/WWNortonXMLFiles/XML11_worksheets/S11_3_A.xml')
        #s = converter.parse('C:/Users/bhadley/Dropbox/Music21Theory/TestFiles/FromServer/11_3_A_1.xml')
        #s = converter.parse('/Users/larsj/Dropbox/Music21Theory/TestFiles/TheoryAnalyzer/TATest.xml')
#        s = converter.parse('C:/Users/bhadley/Dropbox/Music21Theory/TestFiles/TheoryAnalyzer/TATest.xml')
        #s = corpus.parse('bwv7.7')
        
        ta = TheoryAnalyzer(s)
        #ta.keyMeasureMap = {1:'C', 2:'D', 3:'Bb', 4:'c', 5:'g',6:'e',7:'G'}
        ta.keyMeasureMap = {1:'C',3:'d',4:'F',5:'G',6:'e',7:'g',8:'B-',9:'A-',10:'E',11:'f',12:'c#'}

        #ta.key = music21.key.Key('D')
        #ta.getTwoByThreeLinearSegments(0,1)
        #ta.identifyParallelFifths(color='red')
        #ta.identifyParallelOctaves(color='orange')
        #ta.identifyHiddenFifths(color='yellow')
        #ta.identifyHiddenOctaves(color='green')
        #ta.identifyParallelUnisons(color='blue')
        #ta.identifyImproperResolutions(color='purple')
        #ta.identifyLeapNotSetWithStep(color='white')
        #ta.identifyDissonantHarmonicIntervals(color='magenta')
        #ta.identifyDissonantMelodicIntervals(color='cyan')
        #ta.identifyMotionType()
        #ta.identifyScaleDegrees()
#        ta.identifyHarmonicIntervals()
        #ta.identifyOpensIncorrectly()

        rom = [0,6,7,8]
        ta.identifyTonicAndDominantRomanNumerals()

        #ta.identifyClosesIncorrectly()
        #ta.identifyUnaccentedPassingTones(color = 'red')
        #ta.identifyUnaccentedNeighborTones(color = 'yellow')
#        ta.identifyRomanNumerals()
        
#        ta.identifyObliqueMotion()
#        ta.identifySimilarMotion()
#        ta.identifyParallelMotion()
#        ta.identifyContraryMotion()
#        ta.identifyOutwardContraryMotion()
#        ta.identifyInwardContraryMotion()
#        ta.identifyAntiParallelMotion()

        for vsResult in ta.resultDict['romanNumerals']:
            vsResult.vs.lyric = str(vsResult.value)

        print ta.getResultsString()
        ta.show()
        #for n in ta._theoryScore.flat.notes:
        #    print 'h', n.color

    
if __name__ == "__main__":

    music21.mainTest(Test)
    
#    te = TestExternal()
#    te.demo()
    