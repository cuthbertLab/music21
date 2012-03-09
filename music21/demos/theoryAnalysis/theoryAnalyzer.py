# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         theoryAnalyzer.py
# Purpose:      Framework for analyzing music theory aspects of a score
#
# Authors:      Lars Johnson and Beth Hadley
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

from music21.demos.theoryAnalysis import theoryResult

import string
import unittest
from sets import Set

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
    
    demonstrate features of entire class
    
    
    
    '''
    
    
    _DOC_ATTR = {
    'resultDict': 'Dictionary storing the results found by calling identify methods on the theoryAnalyzer score',
    }
    
    def __init__(self, theoryScore, keyMeasureMap={}):
        #caching information about stream
        
        self._theoryScore = theoryScore
        self._vlqCache = {} #Voice Leading Quartet
        self._tnlsCache = {} #Three Note Linear Segment
        self._tbtlsCache = {} #Two By Three Linear Segment Cache
        
        self._verticalSlices = self.getVerticalSlices()

        self.resultDict = {} #dictionary storing the results of any identification method queries
       
        self.keyMeasureMap = keyMeasureMap
    
    #---------------------------------------------------------------------------------------
    # Class level methods to deal with class attributes
    
    def removeFromResultDict(self, dictKeys):  
        '''
        remove a a result entry or entries from the resultDict by specifying which key or keyss in the dictionary
        you'd like remove. Pass in a list of dictKeys or just a single dictionary key.
        
        >>> from music21 import *
        >>> s = stream.Score()
        >>> ta = TheoryAnalyzer(s)
        >>> ta.resultDict = {'sampleDictKey': 'sample response', 'h1':'another sample response', 5:'third sample response'}
        >>> ta.removeFromResultDict('sampleDictKey')
        >>> ta.resultDict
        {'h1': 'another sample response', 5: 'third sample response'}
        >>> ta.removeFromResultDict(['h1',5])
        >>> ta.resultDict
        {}
        '''  
        if isinstance(dictKeys, list):
            for dictKey in dictKeys:
                try:
                    del self.resultDict[dictKey]
                except:
                    raise TheoryAnalyzerException('got a dictKey to remove from resultDictionary that wasn''t in the dictionary: %s', dictKey)
        else:
            try:
                del self.resultDict[dictKeys] 
            except:
                raise TheoryAnalyzerException('got a dictKey to remove from resultDictionary that wasn''t in the dictionary: %s', dictKeys)
        
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
        
    #---------------------------------------------------------------------------------------
    # Methods to split the score up into little pieces for analysis
    # The little pieces are all from voiceLeading.py, such as
    # Vertical Slices, VoiceLeadingQuartet, ThreeNoteLinearSegment, and VerticalSliceNTuplet       
        
    def getVerticalSlices(self, classFilterList=['Note', 'Chord', 'Harmony', 'Rest']):
        '''
        returns a list of :class:`~music21.voiceLeading.VerticalSlice` objects in
        the Theory Analyzer's score. Note that it uses the combined rhythm of the parts 
        to determine what vertical slices to take. Default is to return only objects of
        type Note, Chord, Harmony, and Rest.
        
        >>> from music21 import *
        
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
        
        # if elements exist at same offset, return both 
        
        # If speed is an issue, could try using offset maps...
        chordifiedSc = self._theoryScore.chordify()
        for c in chordifiedSc.flat.getElementsByClass('Chord'):
            contentDict = {}
            partNum= 0
            for part in self._theoryScore.parts:
                
                elementStream = part.flat.getElementsByOffset(c.offset,mustBeginInSpan=False, classList=classFilterList)
                #el = part.flat.getElementAtOrBefore(c.offset,classList=['Note','Rest', 'Chord', 'Harmony'])
                
                for el in elementStream.elements:
                    contentDict[partNum] = []
                    #if el.isClassOrSubclass(['Rest']):
                        #TODO: currently rests are stored as None...change to store them as music21 Rests soon
                    #    contentDict[partNum].append(None) # rests are stored as None...change to store them as Rests soon
                    #else:
                    contentDict[partNum].append(el)    
                partNum+=1
            vs = voiceLeading.VerticalSlice(contentDict)
            vsList.append(vs)
               
        return vsList
    
    def getVLQs(self, partNum1, partNum2):
        '''
        extracts and returns a list of the :class:`~music21.voiceLeading.VoiceLeadingQuartet` 
        objects present between partNum1 and partNum2 in the score
        
        >>> from music21 import *
        
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
        for (i, verticalSlice) in enumerate(self._verticalSlices[:-1]):
            nextVerticalSlice = self._verticalSlices[i + 1]
            
            v1n1 = verticalSlice.getObjectsByPart(partNum1, classFilterList=['Note'])
            v1n2 = nextVerticalSlice.getObjectsByPart(partNum1, classFilterList=['Note'])
            
            v2n1 = verticalSlice.getObjectsByPart(partNum2, classFilterList=['Note'])
            v2n2 = nextVerticalSlice.getObjectsByPart(partNum2, classFilterList=['Note'])
            if v1n1 != None and v1n2 != None and v2n1 != None and v2n2 != None:
                vlq = voiceLeading.VoiceLeadingQuartet(v1n1,v1n2,v2n1,v2n2, key=self.keyAtMeasure(v1n1.measureNumber))
                vlqList.append(vlq)
            
            self._vlqCache[vlqCacheKey] = vlqList
        
        return vlqList

    def getThreeNoteLinearSegments(self, partNum):
        '''
        extracts and returns a list of the :class:`~music21.voiceLeading.ThreeNoteLinearSegment` 
        objects present in partNum in the score
        
        >>> from music21 import *
        
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
        <music21.voiceLeading.NObjectLinearSegment objectList=[None, None, None]  

        '''
        # Caches the list of TNLS once they have been computed
        # for a specified partNum
        
        tnlsCacheKey = str(partNum)
        
        if tnlsCacheKey in self._tnlsCache.keys():
            return self._tnlsCache[tnlsCacheKey]
        else:
            self._tnlsCache[tnlsCacheKey] = self.getLinearSegments(partNum, 3)
        
        return self._tnlsCache[tnlsCacheKey]

    def getLinearSegments(self, partNum, lengthLinearSegment, classFilterList=None):
        '''
        extracts and returns a list of all the linear segments in the piece at 
        the partNum specified, the length of which specified by lengthLinearSegment: 
        Currently Supported: :class:`~music21.voiceLeading.ThreeNoteLinearSegment` 
        
        >>> from music21 import *
        >>> sc = stream.Score()
        >>> part0 = stream.Part()
        >>> part0.append(note.Note('c4'))
        >>> part0.append(note.Note('g4'))
        >>> part0.append(note.Note('c5'))
        >>> part0.append(note.Note('c6'))
        >>> sc.insert(part0)
        >>> ta = TheoryAnalyzer(sc)
        >>> len(ta.getLinearSegments(0,3, ['Note']))
        2
        >>> ta.getLinearSegments(0,3, ['Note'])
        [<music21.voiceLeading.ThreeNoteLinearSegment n1=<music21.note.Note C> n2=<music21.note.Note G> n3=<music21.note.Note C> , <music21.voiceLeading.ThreeNoteLinearSegment n1=<music21.note.Note G> n2=<music21.note.Note C> n3=<music21.note.Note C> ]

        >>> sc2 = stream.Score()
        >>> part1 = stream.Part()
        >>> part1.append(chord.Chord(['C','E','G']))
        >>> part1.append(chord.Chord(['G','B','D']))
        >>> part1.append(chord.Chord(['E','G','C']))
        >>> part1.append(chord.Chord(['F','A','C']))
        >>> sc2.insert(part1)
        >>> ta2 = TheoryAnalyzer(sc2)
        >>> len(ta2.getLinearSegments(0,2, ['Chord']))
        3
        >>> ta2.getLinearSegments(0,2, ['Chord'])
        [<music21.voiceLeading.TwoChordLinearSegment objectList=[<music21.chord.Chord C E G>, <music21.chord.Chord G B D>]  , <music21.voiceLeading.TwoChordLinearSegment objectList=[<music21.chord.Chord G B D>, <music21.chord.Chord E G C>]  , <music21.voiceLeading.TwoChordLinearSegment objectList=[<music21.chord.Chord E G C>, <music21.chord.Chord F A C>]  ]
        >>> for x in ta2.getLinearSegments(0,2, ['Chord']):
        ...   print x.rootInterval(), x.bassInterval()
        <music21.interval.ChromaticInterval 7> <music21.interval.ChromaticInterval 2>
        <music21.interval.ChromaticInterval -7> <music21.interval.ChromaticInterval -2>
        <music21.interval.ChromaticInterval 5> <music21.interval.ChromaticInterval 0>


#        >>> sc3 = stream.Score()
#        >>> part2 = stream.Part()
#        >>> part2.append(harmony.ChordSymbol('C'))
#        >>> part2.append(harmony.ChordSymbol('C'))
#        >>> part2.append(harmony.ChordSymbol('C'))
#        >>> sc3.insert(part2)
#        >>> ta3 = TheoryAnalyzer(sc3)
#        >>> len(ta3.getLinearSegments(0,2, ['Harmony']))
#        2
#        >>> ta3.getLinearSegments(0,2, ['Harmony'])
        '''
        linearSegments = []
        for i in range(0, len(self.getVerticalSlices())-lengthLinearSegment+1):
            objects = []
            for n in range(0,lengthLinearSegment):
                objects.append(self.getVerticalSlices()[i+n].getObjectsByPart(partNum, classFilterList))           
            
            if lengthLinearSegment == 3 and 'Note' in self._getTypeOfAllObjects(objects):
                tnls = voiceLeading.ThreeNoteLinearSegment(objects[0], objects[1], objects[2])
                linearSegments.append(tnls)
            elif lengthLinearSegment == 2 and ('Chord' or 'Harmony' in self._getTypeOfAllObjects(objects)):
                tcls = voiceLeading.TwoChordLinearSegment(objects[0], objects[1])
                linearSegments.append(tcls)
            else:
                nols = voiceLeading.NObjectLinearSegment(objects)
                linearSegments.append(nols)
        return linearSegments
    
    def _getTypeOfAllObjects(self, objectList):
        
        setList = []
        for obj in objectList:
            if obj != None:
                setList.append(Set(obj.classes))
        if setList:
            lastSet = setList[0]
            
            for setObj in setList:
                newIntersection = lastSet.intersection(setObj)
                lastSet = setObj
            
            return newIntersection
        else: return []
    
    def getVerticalSliceNTuplets(self, ntupletNum):
        '''
        extracts and returns a list of the :class:`~music21.voiceLeading.VerticalSliceNTuplets` or the 
        corresponding subclass (currenlty only supports triplets) 
        
        >>> from music21 import *
        
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
        >>> len(ta.getVerticalSliceNTuplets(3))
        1
        >>> ta.getVerticalSliceNTuplets(3)[0]
        <music21.voiceLeading.VerticalSliceTriplet listofVerticalSlices=[<music21.voiceLeading.VerticalSlice contentDict={0: [<music21.note.Note C>], 1: [<music21.note.Note E>]}  , <music21.voiceLeading.VerticalSlice contentDict={0: [<music21.note.Note G>], 1: [<music21.note.Note F>]}  , <music21.voiceLeading.VerticalSlice contentDict={0: [<music21.note.Note C>], 1: [<music21.note.Note A>]}  ] 

        '''

        verticalSliceNTuplets = []
        for i in range(0, len(self._verticalSlices)-(ntupletNum-1)):
            verticalSliceList = []
            for countNum in range(i,i+ntupletNum):
                verticalSliceList.append(self._verticalSlices[countNum])
            if ntupletNum == 3:
                vsnt = voiceLeading.VerticalSliceTriplet(verticalSliceList)
            else: 
                vsnt = voiceLeading.VerticalSliceNTuplet(verticalSliceList)
            verticalSliceNTuplets.append(vsnt)
        return verticalSliceNTuplets
    
    
    #---------------------------------------------------------------------------------------
    # Method to split the score up into very very small pieces 
    #(just notes, just harmonic intervals, or just melodic intervals)
    # TODO: consider deleting getNotes method and consider refactoring getHarmonicIntervals()
    # and getMelodicIntervals() to be extracted from a vertical Slice
    
    def getHarmonicIntervals(self, partNum1, partNum2):
        '''
        returns a list of all the harmonic intervals (:class:`~music21.interval.Interval` ) 
        occurring between the two specified parts.
        
        >>> from music21 import *
        
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
        for verticalSlice in self._verticalSlices:
            
            nUpper = verticalSlice.getObjectsByPart(partNum1, classFilterList=['Note'])
            nLower = verticalSlice.getObjectsByPart(partNum2, classFilterList=['Note'])
            
            if nLower is None or nUpper is None:
                hIntv = None
            else:
                hIntv = interval.notesToInterval(nLower, nUpper)
            
            hInvList.append(hIntv)
                    
        return hInvList
    
    
    def getMelodicIntervals(self, partNum):
        '''
        returns a list of all the melodic intervals (:class:`~music21.interval.Interval`) in the specified part.
        
        >>> from music21 import *
        
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
        
        >>> from music21 import *
        >>> sc = stream.Score()
        >>> p = stream.Part()
        >>> p.repeatAppend(note.Note('C'), 3)
        >>> p.append(note.Rest(1.0))
        >>> sc.append(p)
        >>> ta = TheoryAnalyzer(sc)
        >>> ta.getNotes(0)
        [<music21.note.Note C>, <music21.note.Note C>, <music21.note.Note C>, None]

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
    
    #---------------------------------------------------------------------------------------
    # Helper for identifying across all parts - used for recursion in identify functions

    def getAllPartNumPairs(self):
        '''
        Gets a list of all possible pairs of partNumbers:
        tuples (partNum1, partNum2) where 0 <= partNum1 < partnum2 < numParts
        
        >>> from music21 import *
        
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

    
    #---------------------------------------------------------------------------------------
    # Analysis of the theory Analyzer score occurs based on the little segments that the score 
    # can be divided up into. Each little segment has its own template from which the methods
    # can be tested. Each identify method accepts a long list of parameters, as indicated here:
    '''
    - partNum1 is the first part in the VLQ, partNum2 is the second
    - color is the color to mark the VLQ theory result object
    - dictKey is the dictionary key in the resultDict to assign the result objects found to
    - testFunction is the function to test (if not False is returned, a theory Result object is created)
    - textFunction is the function that returns the text as a string to be set as the theory result object's text parameter      
    - startIndex is the first VLQ in the list to start with (0 is default). endIndex is the first VLQ in list not to search 
    (length of VLQ list is default), meaning default values are to search the entire vlqList
    - if editorialDictKey is specified, the elements in the VLQ as specified by editorialMarkList are assigned the editorialValue
    
    '''
    # Template for analysis based on VLQs   
    
    def _identifyBasedOnVLQ(self, partNum1, partNum2, color, dictKey, testFunction, textFunction, \
                            startIndex=0, endIndex = None, editorialDictKey=None,editorialValue=None, editorialMarkList=[]):

        if dictKey not in self.resultDict.keys():
            self.resultDict[dictKey] = []
        
        if partNum1 == None or partNum2 == None:
            for (partNum1,partNum2) in self.getAllPartNumPairs():
                self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction, \
                                         startIndex, endIndex, editorialDictKey, editorialValue, editorialMarkList)
        else:
            vlqList = self.getVLQs(partNum1, partNum2)
            
            if endIndex == None and startIndex >=0:
                endIndex = len(vlqList)
            for vlq in vlqList[startIndex:endIndex]:
                if testFunction(vlq) is not False: # True or value
                    tr = theoryResult.VLQTheoryResult(vlq)
                    tr.value = testFunction(vlq)
                    tr.text = textFunction(vlq, partNum1, partNum2)
                    if editorialDictKey != None:
                        tr.markNoteEditorial(editorialDictKey, editorialValue, editorialMarkList)
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
                self._identifyBasedOnHarmonicInterval(partNum1, partNum2, color, dictKey, testFunction, textFunction, valueFunction=valueFunction)
        else:
            hIntvList = self.getHarmonicIntervals(partNum1, partNum2)
            
            for hIntv in hIntvList:
                if testFunction(hIntv) is not False: # True or value
                    tr = theoryResult.IntervalTheoryResult(hIntv)
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
                    tr = theoryResult.IntervalTheoryResult(mIntv)
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
                    tr = theoryResult.NoteTheoryResult(n)
                    tr.value = testFunction(n)
                    tr.text = textFunction(n, partNum, tr.value)
                    if color is not None:
                        tr.color(color)
                    self.resultDict[dictKey].append(tr)
                       
    def _identifyBasedOnVerticalSlice(self, color, dictKey, testFunction, textFunction, responseOffsetMap=[]):
        if dictKey not in self.resultDict.keys():
            self.resultDict[dictKey] = []             
        for vs in self._verticalSlices:
            if responseOffsetMap and vs.offset(leftAlign=True) not in responseOffsetMap:
                continue
            if testFunction(vs) is not False:
                tr = theoryResult.VerticalSliceTheoryResult(vs)
                tr.value = testFunction(vs)
                tr.text = textFunction(vs, testFunction(vs))
                if color is not None: 
                    tr.color(color)
                self.resultDict[dictKey].append(tr)
    
    def _identifyBasedOnVerticalSliceNTuplet(self, partNumToIdentify, color, dictKey, testFunction, textFunction, \
                                             editorialDictKey=None,editorialValue=None, editorialMarkDict={}, nTupletNum=3):
        if dictKey not in self.resultDict.keys():
            self.resultDict[dictKey] = []             

        if partNumToIdentify == None:
            for partNum in range(0,len(self._theoryScore.parts)):
                self._identifyBasedOnVerticalSliceNTuplet(partNum, color, dictKey, testFunction, textFunction, \
                                                          editorialDictKey=None,editorialValue=None, editorialMarkDict={}, nTupletNum=3)
        else:
            for vsnt in self.getVerticalSliceNTuplets(nTupletNum):
                if testFunction(vsnt, partNumToIdentify) is not False:
                    tr = theoryResult.VerticalSliceNTupletTheoryResult(vsnt, partNumToIdentify)
                    if editorialDictKey != None:
                        tr.markNoteEditorial(editorialDictKey, editorialValue, editorialMarkDict)
                    tr.text = textFunction(vsnt, partNumToIdentify)
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
                    tr = theoryResult.ThreeNoteLinearSegmentTheoryResult(tnls)
                    tr.value = testFunction(tnls)
                    tr.text = textFunction(tnls, partNum)
                    if color is not None: 
                        tr.color(color)
                    self.resultDict[dictKey].append(tr)
  
    #---------------------------------------------------------------------------------------
    # Here are the public-interface methods that users call directly on the theory analyzer score 
    # these methods call the identify template methods above based
                        
    #-------------------------------------------------------------------------------           
    # Theory Errors using VLQ template
    
    def identifyParallelFifths(self, partNum1 = None, partNum2 = None, color = None, dictKey = 'parallelFifths'):
        '''
        Identifies parallel fifths (calls :meth:`~music21.voiceLeading.parallelFifth`) between 
        two parts (if specified) or between all possible pairs of parts (if not specified) 
        and stores the resulting list of VLQTheoryResult objects in self.resultDict['parallelFifths']. 
        Optionally, a color attribute may be specified to color all corresponding notes in the score.
        
        >>> from music21 import *
        
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
        
        >>> from music21 import *
        
        >>> sc = stream.Score()
        >>> part0 = stream.Part()
        >>> p0measure1 = stream.Measure(number=1)
        >>> p0measure1.append(note.Note('c5'))
        >>> p0measure1.append(note.Note('g5'))
        >>> part0.append(p0measure1)
        >>> part1 = stream.Part()
        >>> p1measure1 = stream.Measure(number=1)
        >>> p1measure1.append(note.Note('c4'))
        >>> p1measure1.append(note.Note('g4'))
        >>> part1.append(p1measure1)
        >>> sc.insert(part0)
        >>> sc.insert(part1)
        >>> ta = TheoryAnalyzer(sc)
        >>> ta.identifyParallelOctaves()
        >>> len(ta.resultDict['parallelOctaves'])
        1
        >>> ta.resultDict['parallelOctaves'][0].text
        'Parallel octave in measure 1: Part 1 moves from C to G while part 2 moves from C to G'
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
        
        >>> from music21 import *
        
        >>> sc = stream.Score()
        >>> part0 = stream.Part()
        >>> p0measure1 = stream.Measure(number=1)
        >>> p0measure1.append(note.Note('c5'))
        >>> p0measure1.append(note.Note('d5'))
        >>> p0measure1.append(note.Note('e5'))
        >>> p0measure1.append(note.Note('f5'))
        >>> part0.append(p0measure1)
        >>> part1 = stream.Part()
        >>> p1measure1 = stream.Measure(number=1)
        >>> p1measure1.append(note.Note('c5'))
        >>> p1measure1.append(note.Note('d5'))
        >>> p1measure1.append(note.Note('e5'))
        >>> p1measure1.append(note.Note('f5'))
        >>> part1.append(p1measure1)
        >>> sc.insert(part0)
        >>> sc.insert(part1)
        >>> ta = TheoryAnalyzer(sc)
        >>> ta.identifyParallelUnisons()
        >>> len(ta.resultDict['parallelUnisons'])
        3
        >>> ta.resultDict['parallelUnisons'][2].text
        'Parallel unison in measure 1: Part 1 moves from E to F while part 2 moves from E to F'

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
        
        >>> from music21 import *
        
        >>> sc = stream.Score()
        >>> part0 = stream.Part()
        >>> p0measure1 = stream.Measure(number=1)
        >>> p0measure1.append(note.Note('e5'))
        >>> p0measure1.append(note.Note('d5'))
        >>> part0.append(p0measure1)
        >>> part1 = stream.Part()
        >>> p1measure1 = stream.Measure(number=1)
        >>> p1measure1.append(note.Note('c5'))
        >>> p1measure1.append(note.Note('g4'))
        >>> part1.append(p1measure1)
        >>> sc.insert(part0)
        >>> sc.insert(part1)
        >>> ta = TheoryAnalyzer(sc)
        >>> ta.identifyHiddenFifths()
        >>> len(ta.resultDict['hiddenFifths'])
        1
        >>> ta.resultDict['hiddenFifths'][0].text
        'Hidden fifth in measure 1: Part 1 moves from E to D while part 2 moves from C to G'
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
        
        >>> from music21 import *
        
        >>> sc = stream.Score()
        >>> part0 = stream.Part()
        >>> p0measure1 = stream.Measure(number=1)
        >>> p0measure1.append(note.Note('e4'))
        >>> p0measure1.append(note.Note('f4'))
        >>> part0.append(p0measure1)
        >>> part1 = stream.Part()
        >>> p1measure1 = stream.Measure(number=1)
        >>> p1measure1.append(note.Note('d3'))
        >>> p1measure1.append(note.Note('f3'))
        >>> part1.append(p1measure1)
        >>> sc.insert(part0)
        >>> sc.insert(part1)
        >>> ta = TheoryAnalyzer(sc)
        >>> ta.identifyHiddenOctaves()
        >>> len(ta.resultDict['hiddenOctaves'])
        1
        >>> ta.resultDict['hiddenOctaves'][0].text
        'Hidden octave in measure 1: Part 1 moves from E to F while part 2 moves from D to F'
        '''
        
        testFunction = lambda vlq: vlq.hiddenOctave()
        textFunction = lambda vlq, pn1, pn2: "Hidden octave in measure " + str(vlq.v1n1.measureNumber) +": "\
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    def identifyImproperResolutions(self, partNum1 = None, partNum2 = None, color = None, dictKey = 'improperResolution', editorialMarkList=[]):
        '''
        Identifies improper resolutions of dissonant intervals (calls :meth:`~music21.voiceLeading.improperResolution`) 
        between two parts (if specified) or between all possible pairs of parts (if not specified) 
        and stores the resulting list of VLQTheoryResult objects in self.resultDict['improperResolution']. 
        Optionally, a color attribute may be specified to color all corresponding notes in the score.
        
        >>> from music21 import *
        
        >>> sc = stream.Score()
        >>> part0 = stream.Part()
        >>> p0measure1 = stream.Measure(number=1)
        >>> p0measure1.append(note.Note('f#4'))
        >>> p0measure1.append(note.Note('a4'))
        >>> part0.append(p0measure1)
        >>> part1 = stream.Part()
        >>> p1measure1 = stream.Measure(number=1)
        >>> p1measure1.append(note.Note('C3'))
        >>> p1measure1.append(note.Note('B2'))
        >>> part1.append(p1measure1)
        >>> sc.insert(part0)
        >>> sc.insert(part1)
        >>> ta = TheoryAnalyzer(sc)
        >>> ta.identifyImproperResolutions()
        >>> len(ta.resultDict['improperResolution'])
        1
        >>> ta.resultDict['improperResolution'][0].text
        'Improper resolution of Augmented Fourth in measure 1: Part 1 moves from F# to A while part 2 moves from C to B'

        '''
        #TODO: incorporate Jose's resolution rules into this method (italian6, etc.)
        testFunction = lambda vlq: vlq.improperResolution()
        textFunction = lambda vlq, pn1, pn2: "Improper resolution of " + vlq.vIntervals[0].simpleNiceName +" in measure " + str(vlq.v1n1.measureNumber) +": "\
                 + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                 + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name + " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction, editorialDictKey='isImproperResolution',editorialValue=True, editorialMarkList=editorialMarkList)
        
    def identifyLeapNotSetWithStep(self, partNum1 = None, partNum2 = None, color = None,dictKey = 'LeapNotSetWithStep'):
        '''
        Identifies a leap/skip in one voice not set with a step in the other voice 
        (calls :meth:`~music21.voiceLeading.leapNotSetWithStep`) 
        between two parts (if specified) or between all possible pairs of parts (if not specified) 
        and stores the resulting list of VLQTheoryResult objects in self.resultDict['leapNotSetWithStep']. 
        Optionally, a color attribute may be specified to color all corresponding notes in the score.
        
        >>> from music21 import *
        
        >>> sc = stream.Score()
        >>> part0 = stream.Part()
        >>> p0measure1 = stream.Measure(number=1)
        >>> p0measure1.append(note.Note('C4'))
        >>> p0measure1.append(note.Note('G3'))
        >>> part0.append(p0measure1)
        >>> part1 = stream.Part()
        >>> p1measure1 = stream.Measure(number=1)
        >>> p1measure1.append(note.Note('A2'))
        >>> p1measure1.append(note.Note('D2'))
        >>> part1.append(p1measure1)
        >>> sc.insert(part0)
        >>> sc.insert(part1)
        >>> ta = TheoryAnalyzer(sc)
        >>> ta.identifyLeapNotSetWithStep()
        >>> len(ta.resultDict['LeapNotSetWithStep'])
        1
        >>> ta.resultDict['LeapNotSetWithStep'][0].text
        'Leap not set with step in measure 1: Part 1 moves from C to G while part 2 moves from A to D'
        '''
        
        testFunction = lambda vlq: vlq.leapNotSetWithStep()
        textFunction = lambda vlq, pn1, pn2: "Leap not set with step in measure " + str(vlq.v1n1.measureNumber) +": "\
                 + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                 + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name + " to " + vlq.v2n2.name
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
    
    def identifyOpensIncorrectly(self, partNum1 = None, partNum2 = None, color = None,dictKey = 'opensIncorrectly'):
        '''
        Identifies if the piece opens correctly; calls :meth:`~music21.voiceLeading.opensIncorrectly`
        
        >>> from music21 import *
        
        >>> sc = stream.Score()
        >>> part0 = stream.Part()
        >>> p0measure1 = stream.Measure(number=1)
        >>> p0measure1.append(note.Note('C#4'))
        >>> p0measure1.append(note.Note('G3'))
        >>> part0.append(p0measure1)
        >>> part1 = stream.Part()
        >>> p1measure1 = stream.Measure(number=1)
        >>> p1measure1.append(note.Note('A2'))
        >>> p1measure1.append(note.Note('D2'))
        >>> part1.append(p1measure1)
        >>> sc.insert(part0)
        >>> sc.insert(part1)
        >>> ta = TheoryAnalyzer(sc)
        >>> ta.identifyOpensIncorrectly()
        >>> len(ta.resultDict['opensIncorrectly'])
        1
        >>> ta.resultDict['opensIncorrectly'][0].text
        'Opening harmony is not in style'

        '''
        
        testFunction = lambda vlq: vlq.opensIncorrectly()
        textFunction = lambda vlq, pn1, pn2: "Opening harmony is not in style"
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction, startIndex = 0, endIndex = 1)
        
    def identifyClosesIncorrectly(self, partNum1 = None, partNum2 = None, color = None,dictKey = 'closesIncorrectly'):
        '''
        Identifies if the piece closes correctly; calls :meth:`~music21.voiceLeading.closesIncorrectly`
        
        >>> from music21 import *
        
        >>> sc = stream.Score()
        >>> part0 = stream.Part()
        >>> p0measure1 = stream.Measure(number=1)
        >>> p0measure1.append(note.Note('B4'))
        >>> p0measure1.append(note.Note('A4'))
        >>> p0measure1.append(note.Note('A4'))
        >>> part0.append(p0measure1)
        >>> part1 = stream.Part()
        >>> p1measure1 = stream.Measure(number=1)
        >>> p1measure1.append(note.Note('G2'))
        >>> p1measure1.append(note.Note('F2'))
        >>> p1measure1.append(note.Note('G2'))
        >>> part1.append(p1measure1)
        >>> sc.insert(part0)
        >>> sc.insert(part1)
        >>> ta = TheoryAnalyzer(sc)
        >>> ta.keyMeasureMap = {1:'G'}
        >>> ta.identifyClosesIncorrectly()
        >>> len(ta.resultDict['closesIncorrectly'])
        1
        >>> ta.resultDict['closesIncorrectly'][0].text
        'Closing harmony is not in style'
        
        '''
        testFunction = lambda vlq: vlq.closesIncorrectly() 
        textFunction = lambda vlq, pn1, pn2: "Closing harmony is not in style"
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction, startIndex=-1)    

#method not really useful now, but as we add methods to this class will serve as a nice template, so keep commeted out!
#    # Using the Three Note Linear Segment Template
#    def identifyCouldBePassingTone(self, partNum = None, color = None, dictKey = 'possiblePassingTone'):
#        testFunction = lambda tnls: tnls.couldBePassingTone()
#        textFunction = lambda tnls, pn: tnls.n2.name + ' in part ' + str(pn+1) + ' identified as a possible passing tone '
#        self._identifyBasedOnThreeNoteLinearSegment(partNum, color, dictKey, testFunction, textFunction)

    # Using the Vertical Slice N Tuplet Template
    def identifyPassingTones(self, partNumToIdentify = None, color = None, dictKey = None, unaccentedOnly=True, \
                             editorialDictKey=None,editorialValue=True):
        '''
        Identifies the passing tones in the piece by looking at the vertical and horizontal cross-sections. Optionally
        specify unaccentedOnly to identify only unaccented passing tones (passing tones on weak beats). unaccentedOnly
        by default set to True
        
        Optionally label each identified passing tone with an editorial :class:`~music21.editorial.NoteEditorial` value of 
        editorialValue at note.editorial.misc[editorialDictKey]
        
        >>> from music21 import *
        
        >>> sc = stream.Score()
        >>> sc.insert(0, meter.TimeSignature('2/4'))
        >>> part0 = stream.Part()
        >>> p0measure1 = stream.Measure(number=1)
        >>> p0measure1.append(note.Note('A4', quarterLength = 0.5))
        >>> p0measure1.append(note.Note('G4', quarterLength = 0.5))
        >>> p0measure1.append(note.Note('F#4', quarterLength = 1.0))
        >>> part0.append(p0measure1)
        >>> part1 = stream.Part()
        >>> p1measure1 = stream.Measure(number=1)
        >>> p1measure1.append(note.Note('A2', quarterLength = 1.0))
        >>> p1measure1.append(note.Note('D3', quarterLength = 1.0))
        >>> part1.append(p1measure1)
        >>> sc.insert(part0)
        >>> sc.insert(part1)
        >>> ta = TheoryAnalyzer(sc)
        >>> ta.identifyPassingTones()
        >>> len(ta.resultDict['unaccentedPassingTones'])
        1
        >>> ta.resultDict['unaccentedPassingTones'][0].text
        'G identified as a passing tone in part 1'
        
        '''
        if dictKey == None and unaccentedOnly:
            dictKey = 'unaccentedPassingTones'
        elif dictKey == None:
            dictKey = 'accentedPassingTones'
        testFunction = lambda vst, pn: vst.hasPassingTone(pn, unaccentedOnly)
        textFunction = lambda vsnt, pn:  vsnt.tnlsDict[pn].n2.name + ' identified as a passing tone in part ' + str(pn+1)
        self._identifyBasedOnVerticalSliceNTuplet(partNumToIdentify, color, dictKey, testFunction, textFunction, editorialDictKey, editorialValue, editorialMarkDict={1:[partNumToIdentify]}, nTupletNum=3)

    def identifyNeighborTones(self, partNumToIdentify = None, color = None, dictKey = None, unaccentedOnly=True, \
                              editorialDictKey='isNeighborTone', editorialValue=True):
        '''
        Identifies the neighbor tones in the piece by looking at the vertical and horizontal cross-sections. Optionally
        specify unaccentedOnly to identify only unaccented neighbor tones (neighbor tones on weak beats). unaccentedOnly
        by default set to True
        
        >>> from music21 import *
        
        >>> sc = stream.Score()
        >>> sc.insert(0, meter.TimeSignature('2/4'))
        >>> part0 = stream.Part()
        >>> p0measure1 = stream.Measure(number=1)
        >>> p0measure1.append(note.Note('E-3', quarterLength = 1.0))
        >>> p0measure1.append(note.Note('C3', quarterLength = 1.0))
        >>> part0.append(p0measure1)
        >>> part1 = stream.Part()
        >>> p1measure1 = stream.Measure(number=1)
        >>> p1measure1.append(note.Note('C2', quarterLength = 0.5))
        >>> p1measure1.append(note.Note('B1', quarterLength = 0.5))
        >>> p1measure1.append(note.Note('C2', quarterLength = 1.0))
        >>> part1.append(p1measure1)
        >>> sc.insert(part0)
        >>> sc.insert(part1)
        >>> ta = TheoryAnalyzer(sc)
        >>> ta.identifyNeighborTones()
        >>> len(ta.resultDict['unaccentedNeighborTones'])
        1
        >>> ta.resultDict['unaccentedNeighborTones'][0].text
        'B identified as a neighbor tone in part 2'
        '''
        if dictKey == None and unaccentedOnly:
            dictKey = 'unaccentedNeighborTones'
        elif dictKey == None:
            dictKey = 'accentedNeighborTones'
            
        testFunction = lambda vst, pn: vst.hasNeighborTone(pn, unaccentedOnly)
        textFunction = lambda vsnt, pn:  vsnt.tnlsDict[pn].n2.name + ' identified as a neighbor tone in part ' + str(pn+1)
        self._identifyBasedOnVerticalSliceNTuplet(partNumToIdentify, color, dictKey, testFunction, textFunction, editorialDictKey, editorialValue, editorialMarkDict={1:[partNumToIdentify]}, nTupletNum=3)

    def identifyDissonantHarmonicIntervals(self, partNum1 = None, partNum2 = None, color = None, dictKey = 'dissonantHarmonicIntervals'):
        '''
        Identifies dissonant harmonic intervals (calls :meth:`~music21.interval.isConsonant`) 
        between the two parts (if specified) or between all possible pairs of parts (if not specified) 
        and stores the resulting list of IntervalTheoryResultObject objects in self.resultDict['dissonantHarmonicIntervals']. 
        Optionally, a color attribute may be specified to color all corresponding notes in the score.
                
        >>> from music21 import *
        
        >>> sc = stream.Score()
        >>> part0 = stream.Part()
        >>> p0measure1 = stream.Measure(number=1)
        >>> p0measure1.append(note.Note('c'))
        >>> p0measure1.append(note.Note('f'))
        >>> p0measure1.append(note.Note('b'))
        >>> p0measure1.append(note.Note('c'))
        >>> part0.append(p0measure1)
        >>> part1 = stream.Part()
        >>> p1measure1 = stream.Measure(number=1)
        >>> p1measure1.append(note.Note('b-'))
        >>> p1measure1.append(note.Note('c'))
        >>> p1measure1.append(note.Note('f'))
        >>> p1measure1.append(note.Note('c'))
        >>> part1.append(p1measure1)
        >>> sc.insert(part0)
        >>> sc.insert(part1)
        >>> ta = TheoryAnalyzer(sc)
        >>> ta.identifyDissonantHarmonicIntervals()
        >>> len(ta.resultDict['dissonantHarmonicIntervals'])
        3
        >>> ta.resultDict['dissonantHarmonicIntervals'][2].text
        'Dissonant harmonic interval in measure 1: Augmented Fourth from F to B between part 1 and part 2'
        '''
        testFunction = lambda hIntv: hIntv is not None and not hIntv.isConsonant()
        textFunction = lambda hIntv, pn1, pn2: "Dissonant harmonic interval in measure " + str(hIntv.noteStart.measureNumber) +": " \
                     + str(hIntv.simpleNiceName) + " from " + str(hIntv.noteStart.name) + " to " + str(hIntv.noteEnd.name) \
                     + " between part " + str(pn1 + 1) + " and part " + str(pn2 + 1)
        self._identifyBasedOnHarmonicInterval(partNum1, partNum2, color, dictKey, testFunction, textFunction)


    def identifyImproperDissonantIntervals(self, partNum1 = None, partNum2 = None, color = None, \
                                           dictKey = 'improperDissonantInterval', unaccentedOnly=True):
        '''
        Identifies dissonant harmonic intervals that are not passing tones or neighbor tones or don't resolve correctly
        
        >>> from music21 import *
        >>> sc = stream.Score()
        >>> part0 = stream.Part()
        >>> p0measure1 = stream.Measure(number=1)
        >>> p0measure1.append(note.Note('a3'))
        >>> p0measure1.append(note.Note('f3'))
        >>> p0measure1.append(note.Note('e3'))
        >>> p0measure1.append(note.Note('c4'))
        >>> part0.append(p0measure1)
        >>> part1 = stream.Part()
        >>> p1measure1 = stream.Measure(number=1)
        >>> p1measure1.append(note.Note('b2'))
        >>> p1measure1.append(note.Note('c3'))
        >>> p1measure1.append(note.Note('b2'))
        >>> p1measure1.append(note.Note('c3'))
        >>> part1.append(p1measure1)
        >>> sc.insert(part0)
        >>> sc.insert(part1)
        >>> ta = TheoryAnalyzer(sc)
        >>> ta.identifyImproperDissonantIntervals()
        >>> len(ta.resultDict['improperDissonantInterval'])
        2
        >>> ta.resultDict['improperDissonantInterval'][1].text
        'Improper dissonant harmonic interval in measure 1: Perfect Fourth from C to F between part 1 and part 2'

        '''
        if dictKey not in self.resultDict.keys():
            self.resultDict[dictKey] = []
        
        if partNum1 == None or partNum2 == None:
            for (partNum1,partNum2) in self.getAllPartNumPairs():
                self.identifyImproperDissonantIntervals(partNum1, partNum2, color, dictKey, unaccentedOnly)
        else:
            self.identifyDissonantHarmonicIntervals(partNum1, partNum2, dictKey='h1')
            self.identifyPassingTones(partNum1, dictKey='pt1', unaccentedOnly=unaccentedOnly)
            self.identifyPassingTones(partNum2, dictKey='pt2', unaccentedOnly=unaccentedOnly)
            
            self.identifyNeighborTones(partNum1, dictKey='nt1', unaccentedOnly=unaccentedOnly)
            self.identifyNeighborTones(partNum1, dictKey='nt2', unaccentedOnly=unaccentedOnly)
            
            self.identifyImproperResolutions(partNum1, partNum2, dictKey='res', editorialMarkList=[1,2,3,4])
            
            for resultTheoryObject in self.resultDict['h1']:
                if  (resultTheoryObject.hasEditorial('isPassingTone', True) or resultTheoryObject.hasEditorial('isNeigborTone', True)) or \
                    not resultTheoryObject.hasEditorial('isImproperResolution', True):
                    continue
                else:
                    intv = resultTheoryObject.intv
                    tr = theoryResult.IntervalTheoryResult(intv)
                    #tr.value = valueFunction(hIntv)
                    tr.text = "Improper dissonant harmonic interval in measure " + str(intv.noteStart.measureNumber) +": " \
                     + str(intv.niceName) + " from " + str(intv.noteStart.name) + " to " + str(intv.noteEnd.name) \
                     + " between part " + str(partNum1 + 1) + " and part " + str(partNum2 + 1)
                    if color is not None:
                        tr.color(color)
                    self.resultDict[dictKey].append(tr)
    
            self.removeFromResultDict(['h1','pt1', 'pt2', 'nt1', 'nt2', 'res'])
        
        
    def identifyDissonantMelodicIntervals(self, partNum = None, color = None, dictKey = 'dissonantMelodicIntervals'):
        '''
        Identifies dissonant melodic intervals (A2, A4, d5, m7, M7) in the part (if specified) 
        or for all parts (if not specified) and stores the resulting list of 
        IntervalTheoryResultObject objects in self.resultDict['dissonantMelodicIntervals']. 
        Optionally, a color attribute may be specified to color all corresponding notes in the score.
        
        >>> from music21 import *
        >>> sc = stream.Score()
        >>> part0 = stream.Part()
        >>> p0measure1 = stream.Measure(number=1)
        >>> p0measure1.append(note.Note('f3'))
        >>> p0measure1.append(note.Note('g#3'))
        >>> part0.append(p0measure1)
        >>> part1 = stream.Part()
        >>> p1measure1 = stream.Measure(number=1)
        >>> p1measure1.append(note.Note('d2'))
        >>> p1measure1.append(note.Note('a-2'))
        >>> part1.append(p1measure1)
        >>> sc.insert(part0)
        >>> sc.insert(part1)
        >>> ta = TheoryAnalyzer(sc)
        >>> ta.identifyDissonantMelodicIntervals()
        >>> len(ta.resultDict['dissonantMelodicIntervals'])
        2
        >>> ta.resultDict['dissonantMelodicIntervals'][0].text
        'Dissonant melodic interval in part 1 measure 1: Augmented Second from F to G#'
        >>> ta.resultDict['dissonantMelodicIntervals'][1].text
        'Dissonant melodic interval in part 2 measure 1: Diminished Fifth from D to A-'

        '''
        testFunction = lambda mIntv: mIntv is not None and mIntv.simpleName in ["A2","A4","d5","m7","M7"]
        textFunction = lambda mIntv, pn: "Dissonant melodic interval in part " + str(pn + 1) + " measure " + str(mIntv.noteStart.measureNumber) +": "\
                     + str(mIntv.simpleNiceName) + " from " + str(mIntv.noteStart.name) + " to " + str(mIntv.noteEnd.name)
        self._identifyBasedOnMelodicInterval(partNum, color, dictKey, testFunction, textFunction)                
    
    #-------------------------------------------------------------------------------           
    # Other Theory Properties to Identify (not specifically checking errors in a counterpoint assignment)
    
    # Theory Properties using VLQ template - No doc tests needed
        
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

    # More Properties, not using VLQ template
    
    def identifyTonicAndDominantRomanNumerals(self, color = None, dictKey = 'romanNumeralsVandI', responseOffsetMap = []):
        '''
        Identifies the roman numerals in the piece by iterating throgh the vertical slices and figuring
        out which roman numeral best corresponds to that vertical slice. Optionally specify the responseOffsetMap
        which limits the resultObjects returned to only those with verticalSlice's.offset(leftAlign=True) included
        in the list. For example, if only roman numerals were to be written for the vertical slice at offset 0, 6, and 7
        in the piece, pass responseOffsetMap = [0,6,7]
        
        >>> from music21 import *
        >>> from music21.demos.theoryAnalysis import theoryAnalyzer
        >>> sc = stream.Score()
        >>> part0 = stream.Part()
        >>> p0measure1 = stream.Measure(number=1)
        >>> p0measure1.append(note.Note('a3'))
        >>> p0measure1.append(note.Note('B-3'))
        >>> part0.append(p0measure1)
        >>> part1 = stream.Part()
        >>> p1measure1 = stream.Measure(number=1)
        >>> p1measure1.append(note.Note('c2'))
        >>> p1measure1.append(note.Note('g2'))
        >>> part1.append(p1measure1)
        >>> sc.insert(part0)
        >>> sc.insert(part1)
        >>> ta = TheoryAnalyzer(sc)
        >>> ta.keyMeasureMap = {0:'Bb'}
        >>> ta.identifyTonicAndDominantRomanNumerals()
        >>> len(ta.resultDict['romanNumeralsVandI'])
        2
        >>> ta.resultDict['romanNumeralsVandI'][0].text
        'Roman Numeral of A,C is V64'
        >>> ta.resultDict['romanNumeralsVandI'][1].text
        'Roman Numeral of B-,G is I'
        
        '''
        def testFunction(vs):
            noteList = vs.getObjectsByClass('Note')
            if not None in noteList:
                inChord = chord.Chord(noteList)
                inKey = self.keyAtMeasure(noteList[0].measureNumber)
                chordBass = noteList[-1]
                inChord.bass(chordBass.pitch)
                return roman.identifyAsTonicOrDominant(inChord, inKey)
            else:
                return False
           
        def textFunction(vs, rn):
            notes = ''
            for n in vs.getObjectsByClass('Note'):
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
        
        METHOD NEEDS DEVELOPMENT - dependent on roman.fromChordAndKey, which is not well developed
        
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
        
    def identifyHarmonicIntervals(self, partNum1 = None, partNum2 = None, color = None, dictKey = 'harmonicIntervals'):
        '''
        identify all the harmonic intervals in the score between partNum1 or partNum2, or if not specified ALL
        possible combinations
        
        :class:`~music21.theoryAnalyzer.IntervalTheoryResult` created with .value set to the the string most commonly
        used to identify the interval (0 through 9, with A4 and d5)
        
        >>> from music21 import *
        >>> from music21.demos.theoryAnalysis import theoryAnalyzer
        >>> sc = stream.Score()
        >>> part0 = stream.Part()
        >>> p0measure1 = stream.Measure(number=1)
        >>> p0measure1.append(note.Note('a3'))
        >>> p0measure1.append(note.Note('f#3'))
        >>> p0measure1.append(note.Note('e3'))
        >>> p0measure1.append(note.Note('c4'))
        >>> part0.append(p0measure1)
        >>> part1 = stream.Part()
        >>> p1measure1 = stream.Measure(number=1)
        >>> p1measure1.append(note.Note('b2'))
        >>> p1measure1.append(note.Note('c3'))
        >>> p1measure1.append(note.Note('b2'))
        >>> p1measure1.append(note.Note('c3'))
        >>> part1.append(p1measure1)
        >>> sc.insert(part0)
        >>> sc.insert(part1)
        >>> ta = TheoryAnalyzer(sc)
        >>> ta.identifyHarmonicIntervals()
        >>> len(ta.resultDict['harmonicIntervals'])
        4
        >>> ta.resultDict['harmonicIntervals'][1].value
        'A4'
        >>> ta.resultDict['harmonicIntervals'][0].text
        'harmonic interval between B and A between parts 1 and 2 is a Minor Seventh'

        '''
        testFunction = lambda hIntv: hIntv.generic.undirected if hIntv is not None else False
        textFunction = lambda hIntv, pn1, pn2: "harmonic interval between " + hIntv.noteStart.name + ' and ' + hIntv.noteEnd.name + \
                     ' between parts ' + str(pn1 + 1) + ' and ' + str(pn2 + 1) + ' is a ' + str(hIntv.niceName)
        def valueFunction(hIntv):
            augordimIntervals = ['A4','d5']
            if hIntv.simpleName in augordimIntervals:
                return hIntv.simpleName
            else:
                value = hIntv.generic.undirected
                while value > 9:
                    value -= 7
                return value
        self._identifyBasedOnHarmonicInterval(partNum1, partNum2, color, dictKey, testFunction, textFunction, valueFunction=valueFunction)
        
    def identifyScaleDegrees(self, partNum = None, color = None, dictKey = 'scaleDegrees'):
        '''
        identify all the scale degrees in the score in partNum, or if not specified ALL partNums
        
        >>> from music21 import *
        >>> from music21.demos.theoryAnalysis import theoryAnalyzer
        >>> sc = stream.Score()
        >>> part0 = stream.Part()
        >>> p0measure1 = stream.Measure(number=1)
        >>> p0measure1.append(note.Note('a3'))
        >>> p0measure1.append(note.Note('f#3'))
        >>> p0measure1.append(note.Note('e3'))
        >>> p0measure1.append(note.Note('c4'))
        >>> part0.append(p0measure1)
        >>> part1 = stream.Part()
        >>> p1measure1 = stream.Measure(number=1)
        >>> p1measure1.append(note.Note('b2'))
        >>> p1measure1.append(note.Note('c3'))
        >>> p1measure1.append(note.Note('b2'))
        >>> p1measure1.append(note.Note('c3'))
        >>> part1.append(p1measure1)
        >>> sc.insert(part0)
        >>> sc.insert(part1)
        >>> ta = TheoryAnalyzer(sc)
        >>> ta.keyMeasureMap = {0:'G'}
        >>> ta.identifyScaleDegrees()
        >>> len(ta.resultDict['scaleDegrees'])
        8
        >>> ta.resultDict['scaleDegrees'][1].value
        '7'
        >>> ta.resultDict['scaleDegrees'][1].text
        'scale degree of F# in part 1 is 7'
        '''
        testFunction = lambda n:  (str(self.keyAtMeasure(n.measureNumber).getScale().getScaleDegreeFromPitch(n.pitch)) ) if n is not None else False
        textFunction = lambda n, pn, scaleDegree: "scale degree of " + n.name + ' in part ' + str(pn+ 1) + ' is ' + str(scaleDegree) 
        self._identifyBasedOnNote(partNum, color, dictKey, testFunction, textFunction)
            
    def identifyMotionType(self, partNum1 = None, partNum2 = None, color = None, dictKey = 'motionType'):
        '''
        Identifies the motion types in the score by analyzing each voice leading quartet between partNum1 and
        partNum2, or all possible voiceLeadingQuartets if not specified
        
        :class:`~music21.theoryAnalyzer.VLQTheoryResult` by calling :meth:`~music21.voiceLeading.motionType`
        Possible values for VLQTheoryResult are 'Oblique', 'Parallel', 'Similar', 'Contrary', 'Anti-Parallel', 'No Motion'
        
        >>> from music21 import *
        >>> from music21.demos.theoryAnalysis import theoryAnalyzer
        >>> sc = stream.Score()
        >>> part0 = stream.Part()
        >>> p0measure1 = stream.Measure(number=1)
        >>> p0measure1.append(note.Note('a3'))
        >>> p0measure1.append(note.Note('f#3'))
        >>> p0measure1.append(note.Note('e3'))
        >>> p0measure1.append(note.Note('c4'))
        >>> part0.append(p0measure1)
        >>> part1 = stream.Part()
        >>> p1measure1 = stream.Measure(number=1)
        >>> p1measure1.append(note.Note('b2'))
        >>> p1measure1.append(note.Note('c3'))
        >>> p1measure1.append(note.Note('b2'))
        >>> p1measure1.append(note.Note('c3'))
        >>> part1.append(p1measure1)
        >>> sc.insert(part0)
        >>> sc.insert(part1)
        >>> ta = TheoryAnalyzer(sc)
        >>> ta.identifyMotionType()
        >>> len(ta.resultDict['motionType'])
        3
        >>> ta.resultDict['motionType'][1].value
        'Similar'
        >>> ta.resultDict['motionType'][1].text
        'Similar Motion in measure 1: Part 1 moves from F# to E while part 2 moves from C to B'
        '''
        
        testFunction = lambda vlq: vlq.motionType()
        textFunction = lambda vlq, pn1, pn2: (vlq.motionType() + ' Motion in measure '+ str(vlq.v1n1.measureNumber) +": " \
                     + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                     + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name)  if vlq.motionType() != "No Motion" else 'No motion'
        self._identifyBasedOnVLQ(partNum1, partNum2, color, dictKey, testFunction, textFunction)
        
    #-------------------------------------------------------------------------------
    # Combo method that wraps many identify methods into one 
    
    def identifyCommonPracticeErrors(self, partNum1=None,partNum2=None,dictKey='commonPracticeErrors'):
        '''
        wrapper method that calls all identify methods for common-practice counterpoint errors, 
        assigning a color identifier to each
        
        ParallelFifths = red, ParallelOctaves = yellow, HiddenFifths = orange, HiddenOctaves = green, 
        ParallelUnisons = blue, ImproperResolutions = purple, improperDissonances = white, 
        DissonantMelodicIntervals = cyan, incorrectOpening = brown, incorrectClosing = gray
        '''
        self.identifyParallelFifths(partNum1, partNum2, 'red', dictKey)
        self.identifyParallelOctaves(partNum1, partNum2, 'yellow', dictKey)
        self.identifyHiddenFifths(partNum1, partNum2, 'orange', dictKey)
        self.identifyHiddenOctaves(partNum1, partNum2, 'green', dictKey)
        self.identifyParallelUnisons(partNum1, partNum2, 'blue', dictKey)
        self.identifyImproperResolutions(partNum1, partNum2, 'purple', dictKey)
        #self.identifyLeapNotSetWithStep(partNum1, partNum2, 'white', dictKey)
        self.identifyImproperDissonantIntervals(partNum1, partNum2, 'white', dictKey, unaccentedOnly = True)
        self.identifyDissonantMelodicIntervals(partNum1,'cyan', dictKey)  
        self.identifyOpensIncorrectly(partNum1, partNum2, 'brown', dictKey)
        self.identifyClosesIncorrectly(partNum1, partNum2, 'gray', dictKey)              
        
        
    #------------------------------------------------------------------------------- 
    # Output methods for reading out information from theoryAnalyzerResult objects
               
    def getResultsString(self, typeList=None):
        '''
        returns string of all results found by calling all identify methods on the TheoryAnalyzer score

        >>> from music21 import *
        >>> from music21.demos.theoryAnalysis import theoryAnalyzer
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
        >>> ta.identifyCommonPracticeErrors()
        >>> print ta.getResultsString()
        commonPracticeErrors: 
        Parallel fifth in measure 1: Part 1 moves from D to E while part 2 moves from G to A
        Parallel fifth in measure 1: Part 1 moves from E to G while part 2 moves from A to C
        Hidden fifth in measure 1: Part 1 moves from C to D while part 2 moves from C to G
        Closing harmony is not in style
        '''
        resultStr = ""
        for resultType in self.resultDict.keys():
            if typeList is None or resultType in typeList:
                resultStr+=resultType+": \n"
                for result in self.resultDict[resultType]:
                    resultStr += result.text
                    resultStr += "\n"
        resultStr = resultStr[0:-1] #remove final new line character
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
        colors the notes of all results found in typeList by calling all identify methods on Theory Analyzer.
        '''
        for resultType in self.resultDict.keys():
            if typeList is None or resultType in typeList:
                for result in self.resultDict[resultType]:
                    result.color(color)
            
    def show(self, value=None):
        '''
        show the score, usually after running some identify and color routines
        '''
        if value!= None:
            self._theoryScore.show(value)
        else:
            self._theoryScore.show()
                

class TheoryAnalyzerException(music21.Music21Exception):
    pass

# ------------------------------------------------------------

class Test(unittest.TestCase):
    
    def runTest(self):
        pass
        
class TestExternal(unittest.TestCase):
    
    def runTest(self):
        pass 
    
    def demo(self):

        #s = converter.parse('C:/Users/bhadley/Dropbox/Music21Theory/WWNortonWorksheets/WWNortonXMLFiles/XML11_worksheets/S11_1_II_cleaned.xml')
        #s = converter.parse('/Users/larsj/Dropbox/Music21Theory/WWNortonWorksheets/WWNortonXMLFiles/XML11_worksheets/S11_1_II_cleaned.xml')
        #s = converter.parse('C:/Users/bhadley/Dropbox/Music21Theory/WWNortonWorksheets/WWNortonXMLFiles/XML11_worksheets/S11_6_IA_completed.xml')
        #s = converter.parse('C:/Users/bhadley/Dropbox/Music21Theory/TestFiles/FromServer/11_3_A_1.xml')
        #s = converter.parse('/Users/larsj/Dropbox/Music21Theory/TestFiles/TheoryAnalyzer/TATest.xml')
        #s = converter.parse('C:/Users/bhadley/Dropbox/Music21Theory/TestFiles/TheoryAnalyzer/S11_6_IA_student.xml')
        s = corpus.parse('bwv7.7')
        ta = TheoryAnalyzer(s)
        #ta.keyMeasureMap = {1:'C', 2:'D', 3:'Bb', 4:'c', 5:'g',6:'e',7:'G'}
        #ta.keyMeasureMap = {1:'C',3:'d',4:'F',5:'G',6:'e',7:'g',8:'B-',9:'A-',10:'E',11:'f',12:'c#'}
        #ta.keyMeasureMap = {0:'G',5:'D',8:'F'}

        #ta.key = music21.key.Key('D')
        #ta.getTwoByThreeLinearSegments(0,1)
        #ta.identifyParallelFifths(color='red')
        #ta.identifyParallelOctaves(color='orange')
        #ta.identifyHiddenFifths(color='yellow')
        #ta.identifyHiddenOctaves(color='green')
        #ta.identifyParallelUnisons(color='blue')
        #ta.identifyImproperResolutions(color='red')
        #ta.identifyLeapNotSetWithStep(color='white')
        #ta.identifyDissonantHarmonicIntervals(color='magenta')
        #ta.identifyDissonantMelodicIntervals(color='cyan')
        #ta.identifyMotionType()
        #ta.identifyScaleDegrees()
        #ta.identifyHarmonicIntervals()
        #ta.identifyOpensIncorrectly()

        #rom = [0,6,7,8]
        #ta.identifyTonicAndDominantRomanNumerals(rom)

        #ta.identifyHarmonicIntervals()

        #ta.identifyClosesIncorrectly()
        ta.identifyPassingTones(color = 'red')
        ta.identifyNeighborTones(color = 'yellow')
       
        #ta.identifyImproperDissonantIntervals(color='blue', partNum1=0, partNum2=1)
        print "identifying..."
#        ta.identifyRomanNumerals()
#        ta.identifyObliqueMotion()
#        ta.identifySimilarMotion()
#        ta.identifyParallelMotion()
#        ta.identifyContraryMotion()
#        ta.identifyOutwardContraryMotion()
#        ta.identifyInwardContraryMotion()
#        ta.identifyAntiParallelMotion()

        #for vsResult in ta.resultDict['harmonicIntervals']:
        #    vsResult.lyric(str(vsResult.value))
        
        print ta.getResultsString()
        ta.show()
        #for n in ta._theoryScore.flat.notes:
        #    print 'h', n.color

    
if __name__ == "__main__":
    music21.mainTest(Test)
    #te = TestExternal()
    #te.demo()
    