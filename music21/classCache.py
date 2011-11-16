# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         classCache.py
# Purpose:      music21 class for optimizing access to Elements
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import unittest
import collections

import music21


from music21 import environment
_MOD = "classCache.py"  
environLocal = environment.Environment(_MOD)

class ClassCacheException(Exception):
    pass


class Repository(object):
    # perhaps use 
    # from collections import deque
    # for elements
    def __init__(self):
        self.classObj = None
        self.classes = []
        self._elements = collections.deque()
        self._endElements = collections.deque()

    def __len__(self):
        return len(self._elements) + len(self._endElements)

    def addElement(self, e):
        '''Add an element to the repository

        >>> from music21 import *
        >>> n = note.Note()
        >>> r = classCache.Repository()
        >>> r.addElement(n)
        >>> r.classes
        ['Note', 'NotRest', 'GeneralNote', 'Music21Object', 'JSONSerializer',     'object']

        '''
        if len(self._elements) == 0:            
            # set class name and key
            self.classObj = e.__class__
            self.classes = e.classes
        self._elements.append(e)
            
    def addEndElement(self, e):
        '''Add an element to the repository

        >>> from music21 import *
        >>> n = note.Note()
        >>> r = classCache.Repository()
        >>> r.addElement(n)
        >>> r.classes
        ['Note', 'NotRest', 'GeneralNote', 'Music21Object', 'JSONSerializer',     'object']

        '''
        # check elements first for first match
        if len(self._elements) == 0 and len(self._endElements) == 0:
            # set class name and key
            self.classObj = e.__class__
            self.classes = e.classes
        self._endElements.append(e)
            

    def insertIntoStream(self, targetStream, offsetSite):
        '''
        >>> from music21 import *
        >>> s1 = stream.Stream()
        >>> n1 = note.Note()
        >>> s1.insert(30, n1)

        >>> s2 = stream.Stream()
        >>> r = classCache.Repository()
        >>> r.addElement(n1)
        >>> r.insertIntoStream(s2, s1)
        >>> [(e, e.getOffsetBySite(s2)) for e in s2]
        [(<music21.note.Note C>, 30.0)]
        >>> len(n1.getSites()) # does not add a site (2 streams, 1 None)
        3
        '''
#         for e in self.elements:
#             targetStream._insertCore(e.getOffsetBySite(offsetSite), e)
#         targetStream._elementsChanged()
# 

        for e in self._elements:
            targetStream._insertCore(e.getOffsetBySite(offsetSite), e, 
                                    ignoreSort=True)
        for e in self._endElements:
            targetStream._storeAtEndCore(e)

        targetStream._elementsChanged()

#-------------------------------------------------------------------------------
class ClassCache(object):

    def __init__(self, srcStream=None):
        self.repositories = {}
        self.parent = None

        if srcStream is not None:
            self.load(srcStream)

    def load(self, srcStream):
        '''
        >>> from music21 import *
        >>> s1 = stream.Stream()
        >>> s1.repeatAppend(note.Note(), 4)
        >>> s1.repeatAppend(note.Rest(), 4)
        >>> cc = classCache.ClassCache()
        >>> cc.load(s1)
        >>> cc.repositories.keys()
        ['Note', 'Rest', 'NotRest', 'GeneralNote']
        '''
        self.parent = srcStream # store this to get offsets later
        #environLocal.printDebug(['loading parent:', srcStream])

        # elements must already be sorted
        for e in srcStream._elements:
            #environLocal.printDebug(['loading', e, e.classes])
            for className in e.classes:
                if className == 'Music21Object': 
                    break
                try:
                    dst = self.repositories[className]
                except KeyError:
                    # store a repository for each entry
                    self.repositories[className] = Repository()
                    dst = self.repositories[className]
                dst.addElement(e)                

        for e in srcStream._endElements:
            for className in e.classes:
                if className == 'Music21Object':
                    break
                try:
                    dst = self.repositories[className]
                except KeyError:
                    # store a repository for each entry
                    self.repositories[className] = Repository()
                    dst = self.repositories[className]
                dst.addEndElement(e)                

#         environLocal.printDebug(['loaded parent:', srcStream, 'got repository keys', self.repositories.keys()])
#         for r in self.repositories.keys():
#             environLocal.printDebug([r, len(self.repositories[r])])


    def hasElementOfClass(self, className):
        '''Return True/False if this class is found. 
        '''
        try: # for performance, try a direct match first
            r = self.repositories[className]
            return True
        except KeyError: # string match not possible
            return False


    def getElementsByClass(self, targetStream, classFilterList):
        '''
        `classFilterList` must be a list.
        `targetStream` is the Stream to build and return

        >>> from music21 import *
        >>> s1 = stream.Stream()
        >>> s1.repeatAppend(note.Note(), 4)
        >>> s1.repeatAppend(note.Rest(), 4)
        >>> cc = classCache.ClassCache()
        >>> cc.load(s1.flat)

        >>> s2 = stream.Stream()
        >>> cc.getElementsByClass(s2, ['Note']).show('t')
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note C>
        {2.0} <music21.note.Note C>
        {3.0} <music21.note.Note C>

        >>> s3 = stream.Stream()
        >>> cc.getElementsByClass(s3, ['Rest']).show('t')
        {4.0} <music21.note.Rest rest>
        {5.0} <music21.note.Rest rest>
        {6.0} <music21.note.Rest rest>
        {7.0} <music21.note.Rest rest>

        >>> # cannot match more than one class
        >>> s4 = stream.Stream()
        >>> len(cc.getElementsByClass(s4, [note.Note, note.Rest]))
        Traceback (most recent call last):
        ClassCacheException: can only process single class names given as a string
        '''
        matchKeys = []
        #environLocal.pd(['getElementsByClass', 'classFilterList', classFilterList])

        # for now, can only match a single class, as this will be in the 
        # correct order
        if len(classFilterList) == 1:
            classNameOrStr = classFilterList[0]
            r = None
            try: # for performance, try a direct match first
                r = self.repositories[classNameOrStr]
            except KeyError: # string match not possible
                pass
            if r is not None:
                r.insertIntoStream(targetStream=targetStream, 
                        offsetSite=self.parent)
        else:
            raise ClassCacheException('can only process single class names given as a string')

        # found may be unaltered; check length
        return targetStream 

#         if matchKeys == []:
#             for classNameOrStr in classFilterList:
#                 #environLocal.pd(['classNameOrStr', classNameOrStr])
#                 if isinstance(classNameOrStr, str):
#                     for r in self.repositories.values(): 
#                         if classNameOrStr in r.classes:
#                             # they key is always the first class
#                             matchKeys.append(r.classes[0])
#                 else:
#                     for r in self.repositories.values():
#                         # see if the requested class is or is subclass      
#                         # of the stored class
#                         if issubclass(classNameOrStr, r.classObj):
#                             # they key is always the first class
#                             matchKeys.append(r.classes[0])
        #environLocal.pd(['matchKeys', matchKeys, 'self.repositories.keys()', self.repositories.keys()])

#         for key in matchKeys:
#             # rather than directly assign, can build list of offset/value?
#             self.repositories[key].insertIntoStream(targetStream=targetStream, 
#                                     offsetSite=self.parent)
#         # must sort, as ordering is sequential
#         # if sort, remove all performance boost
#         #targetStream.sort()
#         return targetStream


class Test(unittest.TestCase):
    
    def runTest(self):
        pass


    def testPerformanceA(self):
        from music21 import common, stream, classCache, clef, meter, note
        
        s1 = stream.Stream()
        s1.repeatAppend(note.Note(), 300)
        s1.repeatAppend(note.Rest(), 300)
        s1.repeatInsert(meter.TimeSignature(), [0, 50, 100, 150])
        s1.repeatInsert(clef.BassClef(), [0, 50, 100, 150])

        t1 = common.Timer()
        t1.start()
        for i in range(50):
            s1.getElementsByClass('Rest')
            s1.getElementsByClass('Note')
            s1.getElementsByClass('GemeralNote')
            s1.getElementsByClass('BassClef')
            s1.getElementsByClass('TimeSignature')
        environLocal.printDebug(['Stream.getOffsetBySite()', t1])
        #classCache.py: Stream.getOffsetBySite() 0.747

        s2 = stream.Stream()
        s2.repeatAppend(note.Note(), 300)
        s2.repeatAppend(note.Rest(), 300)
        s2.repeatInsert(meter.TimeSignature(), [0, 50, 100, 150])
        s2.repeatInsert(clef.BassClef(), [0, 50, 100, 150])

        t1 = common.Timer()
        t1.start()
        cc = classCache.ClassCache()
        # simulate what would happen in getElementsByClass
        cc.load(s2)
        for i in range(50):
            s = stream.Stream()
            cc.getElementsByClass(s, ['Rest'])
            s = stream.Stream()
            cc.getElementsByClass(s, ['Note'])
            s = stream.Stream()
            cc.getElementsByClass(s, ['GeneralNote'])
            s = stream.Stream()
            cc.getElementsByClass(s, ['BassClef'])
            s = stream.Stream()
            cc.getElementsByClass(s, ['TimeSignature'])
        environLocal.printDebug(['Stream.getOffsetBySite()', t1])
        #classCache.py: Stream.getOffsetBySite() 0.261


    def testSubclassMatchingA(self):
        from music21 import stream, note, clef, meter, classCache, common, chord
        s2 = stream.Stream()
        s2.repeatAppend(note.Note(), 300)
        s2.repeatAppend(note.Rest(), 300)
        s2.repeatAppend(chord.Chord(), 300)
        s2.repeatInsert(meter.TimeSignature(), [0, 50, 100, 150])
        s2.repeatInsert(clef.BassClef(), [0, 50, 100, 150])

        t1 = common.Timer()
        t1.start()
        cc = classCache.ClassCache()
        # simulate what would happen in getElementsByClass
        cc.load(s2) 
        s = stream.Stream()
        cc.getElementsByClass(s, ['Rest'])
        self.assertEqual(len(s), 300)
        s = stream.Stream()
        cc.getElementsByClass(s, ['Note'])
        self.assertEqual(len(s), 300)
        s = stream.Stream()
        cc.getElementsByClass(s, ['GeneralNote'])
        self.assertEqual(len(s), 900)

        s = stream.Stream()
        cc.getElementsByClass(s, ['NotRest'])
        self.assertEqual(len(s), 600)

        s = stream.Stream()
        cc.getElementsByClass(s, ['BassClef'])
        self.assertEqual(len(s), 4)

        s = stream.Stream()
        cc.getElementsByClass(s, ['Clef'])
        self.assertEqual(len(s), 4)

        s = stream.Stream()
        cc.getElementsByClass(s, ['TimeSignature'])
        self.assertEqual(len(s), 4)


    def testBasicA(self):
        from music21 import corpus, stream, classCache
        s = corpus.parse('schoenberg/opus19/movement6')

        cc = classCache.ClassCache(s.parts[0])
        sOut = stream.Stream()
        cc.getElementsByClass(sOut, ['Measure'])
        self.assertEqual(len(sOut), 10)

        cc = classCache.ClassCache(s.parts[1])
        sOut = stream.Stream()
        cc.getElementsByClass(sOut, ['Measure'])
        self.assertEqual(len(sOut), 10)


#         s = corpus.parse('schoenberg/opus19/movement6')
#         m1 = s.parts[0].getElementsByClass('Measure', useClassCache=True)[0]
        


    def testBasicB(self):
        from music21.musicxml import testPrimitive
        from music21 import converter, clef

        mxString = testPrimitive.clefs12a
        a = converter.parse(mxString)
        part = a.parts[0]

        clefs = part.flat.getElementsByClass('Clef')
        self.assertEqual(len(clefs), 18)



#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []

if __name__ == "__main__":
    # sys.arg test options will be used in mainTest()
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof



