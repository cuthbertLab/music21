#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         converter.py
# Purpose:      Provide a common way to create Streams from any data music21
#               handles
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''Public interface for importing file formats into music21. 
'''


import doctest
import unittest
import os
import pickle

import music21

from music21 import chord
from music21 import clef
from music21 import common
from music21 import dynamics
from music21 import humdrum
from music21 import instrument
from music21 import meter
from music21 import musicxml
from music21 import note
from music21 import notationMod
from music21 import stream


from music21 import environment
_MOD = 'converter.py'
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------
class PickleFilterException(Exception):
    pass

class ConverterException(Exception):
    pass

class ConverterFileException(Exception):
    pass


#-------------------------------------------------------------------------------
class PickleFilter(object):
    '''Before opening a file path, this class can check if there is an up 
    to date version pickled and stored in the scratch directory. 

    If the user has not specified a scratch directory, a pickle path will 
    not be created. 
    '''
    def __init__(self, fp, forceSource=False):
        '''Provide a file path to check if there is pickled version.

        If forceSource is True, pickled files, if available, will not be
        returned.
        '''
        self.fp = fp
        self.forceSource = forceSource

    def _getPickleFp(self, dir):
        if dir == None:
            raise ValueError
        return os.path.join(dir, 'm21-' + common.getMd5(self.fp) + '.p')

    def status(self):
        # look for an up to date pickled version
        # if it exists, return its fp, other wise return fp
        fpScratch = environLocal['directoryScratch']
        format = common.findFormatFile(self.fp)

        if format == 'pickle': # do not pickle a pickle
            if self.forceSource:
                raise PickleFilterException('cannot access source file when only given a file path to a pickled file.')
            writePickle = False # cannot write pickle if no scratch dir
            fpLoad = self.fp
            fpPickle = None                    
        elif fpScratch == None or self.forceSource:
            writePickle = False # cannot write pickle if no scratch dir
            fpLoad = self.fp
            fpPickle = None
        else: # see which is more up to doate
            fpPickle = self._getPickleFp(fpScratch)
            if not os.path.exists(fpPickle):
                writePickle = True # if pickled file does not exist
                fpLoad = self.fp
            else:
                post = common.sortFilesRecent([self.fp, fpPickle])
                if post[0] == fpPickle: # pickle is most recent
                    writePickle = False
                    fpLoad = fpPickle
                elif post[0] == self.fp: # file is most recent
                    writePickle = True
                    fpLoad = self.fp
        return fpLoad, writePickle, fpPickle






#-------------------------------------------------------------------------------
class ConverterHumdrum(object):


    def __init__(self):
        self.stream = None

    #---------------------------------------------------------------------------
    def parseData(self, humdrumString):
        '''Open from a string'''
        self.data = humdrum.parseData(humdrumString)
        self.stream = self.data.stream
        return self.data

    def parseFile(self, filepath):
        '''Open from file path'''
        self.data = humdrum.parseFile(filepath)
        self.stream = self.data.stream
        return self.data





#-------------------------------------------------------------------------------
class ConverterMusicXML(object):

    def __init__(self, forceSource):
        self._mxScore = None
        self._stream = stream.Score()
        self.forceSource = forceSource

    #---------------------------------------------------------------------------
    def getPartNames(self):
        return self._mxScore.getPartNames()

    def load(self):
        '''Load all parts.
        This determines the order parts are found in the stream
        '''
        t = common.Timer()
        t.start()
        self._stream.mx = self._mxScore
        t.stop()
        environLocal.printDebug(['music21 object creation time:', t])

    #---------------------------------------------------------------------------
    # properties

    def _getStream(self):
        return self._stream

    stream = property(_getStream)


    #---------------------------------------------------------------------------
    def parseData(self, xmlString):
        '''Open from a string'''
        c = musicxml.Document()
        c.read(xmlString)
        self._mxScore = c.score
        if len(self._mxScore) == 0:
            raise ConverterException('score from xmlString (%s...) has no parts defined' % xmlString[:30])
        self.load()

    def parseFile(self, fp):
        '''Open from file path; check to see if there is a pickled
        version available and up to date; if so, open that, otherwise
        open source.
        '''
        # return fp to load, if pickle needs to be written, fp pickle
        pfObj = PickleFilter(fp, self.forceSource)
        fpDst, writePickle, fpPickle = pfObj.status() # get status

        formatSrc = common.findFormatFile(fp)
        format = common.findFormatFile(fpDst)
        pickleError = False

        c = musicxml.Document()
        if format == 'pickle':
            environLocal.printDebug(['opening pickled file', fpDst])
            try:
                c.openPickle(fpDst)
            except (ImportError, EOFError):
                msg = 'pickled file (%s) is damaged; a new file will be created.' % fpDst
                pickleError = True
                writePickle = True
                if formatSrc == 'musicxml':
                    environLocal.printDebug([msg], environLocal)
                    fpDst = fp # set to orignal file path
                else:
                    raise ConverterException(msg)

        if format == 'musicxml' or (formatSrc == 'musicxml' and pickleError):
            environLocal.printDebug(['opening musicxml file', fpDst])
            c.open(fpDst)

        if writePickle:
            environLocal.printDebug(['writing pickled file', fpPickle])
            c.writePickle(fpPickle)

        self._mxScore = c.score
        if len(self._mxScore) == 0:
            raise ConverterException('score from file path (...%s) no parts defined' % fp[-10:])
        self.load()









#-------------------------------------------------------------------------------
class Converter(object):
    '''Not a subclass, but a wrapper for different converter objects based on format.
    '''

    def __init__(self):
        self._converter = None

    def _setConverter(self, format, forceSource=False):
        # assume for now tt pickled files are alwasy musicxml
        # this may change in the future
        if format in ['musicxml', 'pickle']: 
            self._converter = ConverterMusicXML(forceSource)
        elif format == 'humdrum':
            self._converter = ConverterHumdrum()
        else:
            raise ConverterException('no such format: %s' % format)

    def parseFile(self, fp, forceSource=False):
        if not os.path.exists(fp):
            raise ConverterFileException('no such file eists: %s' % fp)
        format = common.findFormatFile(fp) 
        self._setConverter(format, forceSource)
        self._converter.parseFile(fp)

    def parseData(self, dataStr):
        '''need to look at data and determine if it is xml or humdrum
        '''
        dataStr = dataStr.lstrip()
        if dataStr.startswith('<?xml'):
            format = 'musicxml'
        elif dataStr.startswith('!!!') or dataStr.startswith('**'):
            format = 'humdrum'
        else:
            raise ConverterException('no such format found for: %s' % dataStr)

        self._setConverter(format)
        self._converter.parseData(dataStr)


    #---------------------------------------------------------------------------
    # properties

    def _getStream(self):
        return self._converter.stream 
        # not _stream: please don't look in other objects' private variables; 
        #              humdrum worked differently.

    stream = property(_getStream)




#-------------------------------------------------------------------------------
# module level convenience methods


def parseFile(fp, forceSource=False):
    v = Converter()
    v.parseFile(fp, forceSource)
    return v.stream

def parseData(dataStr):
    v = Converter()
    v.parseData(dataStr)
    return v.stream

def parse(value, forceSource=False):
    '''
    Determine if the file is a file path or a string 
    '''
    if os.path.exists(value):
        return parseFile(value, forceSource)
    else:
        return parseData(value)



#-------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):
    # interpreter loading

    def runTest(self):
        pass

    def testMusicXMLConversion(self):
        from music21.musicxml import testFiles
        mxString = testFiles.ALL[1]
        a = ConverterMusicXML()
        a.parseData(mxString)

    def testConversionMusicXml(self):
        c = stream.Score()

        from music21.musicxml import testPrimitive
        mxString = testPrimitive.chordsThreeNotesDuration21c
        a = parseData(mxString)

        mxString = testPrimitive.beams01
        b = parseData(mxString)
        #b.show()

        c.append(a[0])
        c.append(b[0])
        c.show()
        # TODO: this is only showing the minimum number of measures


class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testCopyAndDeepcopy(self):
        '''Test copyinng all objects defined in this module
        '''
        import sys, types, copy
        for part in sys.modules[self.__module__].__dict__.keys():
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            obj = getattr(sys.modules[self.__module__], part)
            if callable(obj) and not isinstance(obj, types.FunctionType):
                a = copy.copy(obj)
                b = copy.deepcopy(obj)


    def testConversionMX(self):
        from music21.musicxml import testPrimitive
        from music21.musicxml import testFiles
        from music21 import corpus


        mxString = testPrimitive.pitches01a
        a = parse(mxString)
        a = a.flat
        b = a.getElementsByClass(note.Note)
        # there should be 102 notes
        self.assertEqual(len(b), 102)


        # test directions, dynamics, wedges
        mxString = testPrimitive.directions31a
        a = parse(mxString)
        a = a.flat
        b = a.getElementsByClass(dynamics.Dynamic)
        # there should be 27 dyanmics found in this file
        self.assertEqual(len(b), 27)
        c = a.getElementsByClass(note.Note)
        self.assertEqual(len(c), 53)
        d = a.getElementsByClass(dynamics.Wedge)
        self.assertEqual(len(d), 4)


        # test lyrics
        mxString = testPrimitive.lyricsMelisma61d
        a = parse(mxString)
        a = a.flat
        b = a.getElementsByClass(note.Note)
        found = []
        for noteObj in b:
            for obj in noteObj.lyrics:
                found.append(obj)
        self.assertEqual(len(found), 3)


        # test we are getting rests
        mxString = testPrimitive.restsDurations02a
        a = parse(mxString)
        a = a.flat
        b = a.getElementsByClass(note.Rest)
        self.assertEqual(len(b), 19)


        # test if we can get trills
        mxString = testPrimitive.notations32a
        a = parse(mxString)
        a = a.flat
        b = a.getElementsByClass(note.Note)


        
        mxString = testPrimitive.rhythmDurations03a
        a = parse(mxString)
        self.assertEqual(len(a), 1) # one part
        for part in a:
            self.assertEqual(len(part), 7) # seven measures
            measures = part.getElementsByClass(stream.Measure)
            self.assertEqual(int(measures[0].measureNumber), 1)
            self.assertEqual(int(measures[-1].measureNumber), 7)

        # print a.recurseRepr()


        
        # print a.recurseRepr()

        # get the third movement
#         mxFile = corpus.getWork('opus18no1')[2]
#         a = parse(mxFile)
#         a = a.flat
#         b = a.getElementsByClass(dynamics.Dynamic)
#         # 110 dynamics
#         self.assertEqual(len(b), 110)
# 
#         c = a.getElementsByClass(note.Note)
#         # over 1000 notes
#         self.assertEqual(len(c), 1289)



    def testConversionMXChords(self):

        from music21.musicxml import testPrimitive

        mxString = testPrimitive.chordsThreeNotesDuration21c
        a = parse(mxString)
        for part in a:
            chords = part.flat.getElementsByClass(chord.Chord)
            self.assertEqual(len(chords), 7)
            knownSize = [3, 2, 3, 3, 3, 3, 3]
            for i in range(len(knownSize)):
                #print chords[i].pitches, len(chords[i].pitches)
                self.assertEqual(knownSize[i], len(chords[i].pitches))


    def testConversionMXBeams(self):

        from music21.musicxml import testPrimitive

        mxString = testPrimitive.beams01
        a = parse(mxString)
        part = a[0]
        notes = part.flat.getNotes()
        beams = []
        for n in notes:
            if n.isClass(note.Note):
                beams += n.beams.beamsList
        self.assertEqual(len(beams), 152)


    def testConversionMXTime(self):

        from music21.musicxml import testPrimitive

        mxString = testPrimitive.timeSignatures11c
        a = parse(mxString)
        part = a[0]


        mxString = testPrimitive.timeSignatures11d
        a = parse(mxString)
        part = a[0]


        notes = part.flat.getNotes()
        self.assertEqual(len(notes), 11)


    def testConversionMXClef(self):

        from music21.musicxml import testPrimitive
        mxString = testPrimitive.clefs12a
        a = parse(mxString)
        part = a[0]

        clefs = part.flat.getElementsByClass(clef.Clef)
        self.assertEqual(len(clefs), 18)


    def testConversionMXClefCorpus(self):
    
        from music21 import corpus
        a = corpus.parseWork('luca')
        clefs = a[0].flat.getElementsByClass(clef.Clef)
        self.assertEqual(len(clefs), 1)
        clefs = a[1].flat.getElementsByClass(clef.Clef)
        self.assertEqual(len(clefs), 1)
        clefs = a[2].flat.getElementsByClass(clef.Clef)
        self.assertEqual(len(clefs), 1)



if __name__ == "__main__":
    music21.mainTest(Test)
    #music21.mainTest(Test, TestExternal)

