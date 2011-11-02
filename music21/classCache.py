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

import music21


from music21 import environment
_MOD = "classCache.py"  
environLocal = environment.Environment(_MOD)



class Repository(object):
    def __init__(self):
        self.classObj = None
        self.classes = []
        self._elements = []
        self._endElements = []


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

    def __init__(self):
        self.repositories = {}
        self.parent = None

    def load(self, srcStream):
        '''
        >>> from music21 import *
        >>> s1 = stream.Stream()
        >>> s1.repeatAppend(note.Note(), 4)
        >>> s1.repeatAppend(note.Rest(), 4)
        >>> cc = classCache.ClassCache()
        >>> cc.load(s1)
        >>> cc.repositories.keys()
        ['Note', 'Rest']
        '''
        self.parent = srcStream # store this to get offsets later
        for e in srcStream._elements:
            try:
                dst = self.repositories[e.classes[0]]
            except KeyError:
                # store a repository for each entry
                self.repositories[e.classes[0]] = Repository()
                dst = self.repositories[e.classes[0]]
            dst.addElement(e)                

        for e in srcStream._endElements:
            try:
                dst = self.repositories[e.classes[0]]
            except KeyError:
                # store a repository for each entry
                self.repositories[e.classes[0]] = Repository()
                dst = self.repositories[e.classes[0]]
            dst.addEndElement(e)                


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

        >>> # can use class names as well
        >>> s4 = stream.Stream()
        >>> cc.getElementsByClass(s4, [note.Note, note.Rest]).show('t')
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note C>
        {2.0} <music21.note.Note C>
        {3.0} <music21.note.Note C>
        {4.0} <music21.note.Rest rest>
        {5.0} <music21.note.Rest rest>
        {6.0} <music21.note.Rest rest>
        {7.0} <music21.note.Rest rest>
        '''
        matchKeys = []
        #environLocal.pd(['getElementsByClass', 'classFilterList', classFilterList])

        # if the ancestry of one classFilterList is entirely within
        # another, duplicate items will be placed in the stream

        if len(classFilterList) == 1:
            try: # for performance, try a direct match first
                self.repositories[classFilterList[0]]
                matchKeys.append(classFilterList[0])
            except KeyError:    
                pass
        if matchKeys == []:
            for classNameOrStr in classFilterList:
                #environLocal.pd(['classNameOrStr', classNameOrStr])
                if isinstance(classNameOrStr, str):
                    for r in self.repositories.values(): 
                        if classNameOrStr in r.classes:
                            # they key is always the first class
                            matchKeys.append(r.classes[0])
                else:
                    for r in self.repositories.values():
                        # see if the requested class is or is subclass      
                        # of the stored class
                        if issubclass(classNameOrStr, r.classObj):
                            # they key is always the first class
                            matchKeys.append(r.classes[0])
        #environLocal.pd(['matchKeys', matchKeys, 'self.repositories.keys()', self.repositories.keys()])

        for key in matchKeys:
            # rather than directly assign, can build list of offset/value?
            self.repositories[key].insertIntoStream(targetStream=targetStream, 
                                    offsetSite=self.parent)
        # must sort, as ordering is sequential
        # if sort, remove all performance boost
        #targetStream.sort()
        return targetStream


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
            s1.getElementsByClass('GeneralNote')
            s1.getElementsByClass('Clef')
            s1.getElementsByClass('TimeSignature')
        environLocal.printDebug(['Stream.getOffsetBySite()', t1])
        #classCache.py: Stream.getOffsetBySite() 0.988

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
            cc.getElementsByClass(s, ['Clef'])
            s = stream.Stream()
            cc.getElementsByClass(s, ['TimeSignature'])
        environLocal.printDebug(['Stream.getOffsetBySite()', t1])
        #Stream.getOffsetBySite() 0.557

#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []

if __name__ == "__main__":
    # sys.arg test options will be used in mainTest()
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof



