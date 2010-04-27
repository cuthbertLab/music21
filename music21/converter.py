#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         converter.py
# Purpose:      Provide a common way to create Streams from any data music21
#               handles
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''Public interface for importing file formats into music21. 
'''


import doctest
import unittest
import os
import urllib
import time
import copy

try:
    import cPickle as pickleMod
except ImportError:
    import pickle as pickleMod


import music21
from music21 import chord
from music21 import clef
from music21 import common
from music21 import dynamics
from music21 import humdrum
from music21 import instrument
from music21 import key
from music21 import meter
from music21 import musicxml
from music21 import note
from music21 import expressions
from music21 import stream
from music21 import tinyNotation


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
        '''Given a file path specified with __init__, look for an up to date pickled version of this file path. If it exists, return its fp, other wise return the original file path.

        Return arguments are file path to load, boolean whether to write a pickle, and the file path of the pickle.
        '''
        fpScratch = environLocal.getTempDir()
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
class StreamFreezer(object):


    def __init__(self, streamObj=None):
        # may want to make a copy, as we are destructively modifying
        self.stream = streamObj
        #self.stream = copy.deepcopy(streamObj)

    def _getPickleFp(self, dir):
        if dir == None:
            raise ValueError
        # cannot get data from stream, as offsets are broken
        streamStr = str(time.time())
        return os.path.join(dir, 'm21-' + common.getMd5(streamStr) + '.p')


    #---------------------------------------------------------------------------
    def writePickle(self, fp=None):

        if fp == None:
            dir = environLocal.getTempDir()
            fp = self._getPickleFp(dir)
        elif os.sep in fp: # assume its a complete path
            fp = fp
        else:
            dir = environLocal.getTempDir()
            fp = os.path.join(dir, fp)

        #self.stream._printDefinedContexts()
        self.stream.setupPickleScaffold()
        #self.stream._printDefinedContexts()

        environLocal.printDebug(['writing fp', fp])
        f = open(fp, 'wb') # binary
        # a negative protocal value will get the highest protocal; 
        # this is generally desirable 

        storage = {'stream': self.stream, 'm21Version': music21.VERSION}
        pickleMod.dump(storage, f, protocol=-1)
        f.close()
        return fp

    def openPickle(self, fp):

        if os.sep in fp: # assume its a complete path
            fp = fp
        else:
            dir = environLocal.getTempDir()
            fp = os.path.join(dir, fp)

        environLocal.printDebug(['opening fp', fp])
        f = open(fp, 'rb')
        storage = pickleMod.load(f)
        f.close()
        #self.stream._printDefinedContexts()

        version = storage['m21Version']
        if version != music21.VERSION:
            environLocal.warn('this pickled file is out of data and my not function properly.')

        self.stream = storage['stream']
        self.stream.teardownPickleScaffold()
        #self.stream._printDefinedContexts()




#-------------------------------------------------------------------------------
class ConverterHumdrum(object):
    '''Simple class wrapper for parsing Humdrum data provided in a file or in a string.
    '''

    def __init__(self):
        self.stream = None

    #---------------------------------------------------------------------------
    def parseData(self, humdrumString):
        '''Open Humdrum data from a string

        >>> humdata = '**kern\\n*M2/4\\n=1\\n24r\\n24g#\\n24f#\\n24e\\n24c#\\n24f\\n24r\\n24dn\\n24e-\\n24gn\\n24e-\\n24dn\\n*-'
        >>> c = ConverterHumdrum()
        >>> s = c.parseData(humdata)
        '''
        self.data = humdrum.parseData(humdrumString)
        self.stream = self.data.stream
        return self.data

    def parseFile(self, filepath):
        '''Open Humdram data from a file path.'''
        self.data = humdrum.parseFile(filepath)
        self.stream = self.data.stream
        return self.data




#-------------------------------------------------------------------------------
class ConverterTinyNotation(object):
    '''Simple class wrapper for parsing TinyNotation data provided in a file or in a string.
    '''

    def __init__(self):
        self.stream = None

    #---------------------------------------------------------------------------
    def parseData(self, tnData):
        '''Open TinyNotation data from a string or list

        >>> tnData = ["E4 r f# g=lastG trip{b-8 a g} c", "3/4"]
        >>> c = ConverterTinyNotation()
        >>> s = c.parseData(tnData)
        '''
        if common.isStr(tnData):
            tnStr = tnData
            tnTs = None
        else: # assume a 2 element sequence
            tnStr = tnData[0]
            tnTs = tnData[1]
    
        self.stream = tinyNotation.TinyNotationStream(tnStr, tnTs)

    def parseFile(self, fp):
        '''Open TinyNotation data from a file path.'''

        f = open(fp)
        tnStr = f.read()
        f.close()
        self.stream = tinyNotation.TinyNotationStream(tnStr)







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
        '''Load all parts from a MusicXML object representation.
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
        '''Open MusicXML data from a string.'''
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
            # check if this pickle is up to date
            if (hasattr(c.score, 'm21Version') and 
                c.score.m21Version >= musicxml.VERSION_MINIMUM):
                environLocal.printDebug(['pickled file version is compatible',
                c.score.m21Version])
            else:
                try:
                    environLocal.printDebug(['pickled file version is not compatible', c.score.m21Version])
                except AttributeError:
                    ## some old pickles have no versions
                    pass
                pickleError = True
                writePickle = True
                fpDst = fp # set to orignal file path

        if format == 'musicxml' or (formatSrc == 'musicxml' and pickleError):
            environLocal.printDebug(['opening musicxml file', fpDst])
            c.open(fpDst)

        if writePickle:
            if fpPickle == None: # if original file cannot be found
                raise ConverterException('attempting to write pickle but no file path is given')
            environLocal.printDebug(['writing pickled file', fpPickle])
            c.writePickle(fpPickle)

        self._mxScore = c.score
        if len(self._mxScore) == 0:
            raise ConverterException('score from file path (...%s) no parts defined' % fp[-10:])
        self.load()









#-------------------------------------------------------------------------------
class Converter(object):
    '''A class used for converting all supported data formats into music21 objects. 

    Not a subclass, but a wrapper for different converter objects based on format.
    '''

    def __init__(self):
        self._converter = None

    def _setConverter(self, format, forceSource=False):
        # assume for now tt pickled files are alwasy musicxml
        # this may change in the future
        if format in ['musicxml', 'pickle']: 
            self._converter = ConverterMusicXML(forceSource=forceSource)
        elif format == 'humdrum':
            self._converter = ConverterHumdrum()
        elif format == 'tinyNotation':
            self._converter = ConverterTinyNotation()
        else:
            raise ConverterException('no such format: %s' % format)

    def _getDownloadFp(self, dir, ext, url):
        if dir == None:
            raise ValueError
        return os.path.join(dir, 'm21-' + common.getMd5(url) + ext)

    def parseFile(self, fp, forceSource=False):
        '''Given a file path, parse and store a music21 Stream.
        '''
        #environLocal.printDebug(['attempting to parseFile', fp])
        if not os.path.exists(fp):
            raise ConverterFileException('no such file eists: %s' % fp)
        # TODO: no extension matching for tinyNotation
        format = common.findFormatFile(fp) 
        self._setConverter(format, forceSource=forceSource)
        self._converter.parseFile(fp)

    def parseData(self, dataStr):
        '''Given raw data, determine format and parse into a music21 Stream.
        '''
        format = None
        if common.isListLike(dataStr):
            format = 'tinyNotation'
        
        if format == None: # its a string
            dataStr = dataStr.lstrip()
            if dataStr.startswith('<?xml'):
                format = 'musicxml'
            elif dataStr.startswith('!!!') or dataStr.startswith('**'):
                format = 'humdrum'
            else:
                raise ConverterException('no such format found for: %s' % dataStr)

        self._setConverter(format)
        self._converter.parseData(dataStr)


    def parseURL(self, url):
        '''Given a url, download and parse the file into a music21 Stream.

        Note that this check the user Environment `autoDownlaad` setting before downloading. 
        '''
        autoDownload = environLocal['autoDownload']
        if autoDownload == 'allow':
            pass
        elif autoDownload == 'deny':
            raise ConverterException('automatic downloading of URLs is presently set to "%s"; configure your Environment "autoDownload" setting to "allow" to permit automatic downloading.' % autoDownload)
        elif autoDownload == 'ask':
            raise ConverterException('automatic downloading of URLs is presently set to "%s"; configure your Environment "autoDownload" setting to "allow" to permit automatic downloading.' % autoDownload)

        #url = urllib.quote(url) may need?
        format, ext = common.findFormatExtURL(url)
        if format == None: # cannot figure out what it is
            raise ConverterException('cannot determine file format of url: %s' % url)
        dir = environLocal.getTempDir()
        #dst = environLocal.getTempFile(ext)

        dst = self._getDownloadFp(dir, ext, url)

        if not os.path.exists(dst):
            try:
                environLocal.printDebug(['downloading to:', dst])
                fp, headers = urllib.urlretrieve(url, filename=dst)
            except IOError:
                raise ConverterException('cannot access file: %s' % url)
        else:
            environLocal.printDebug(['using already downloaded file:', dst])
            fp = dst

        # update format based on downloaded fp
        format = common.findFormatFile(fp) 
        self._setConverter(format, forceSource=False)
        self._converter.parseFile(fp)


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
    '''Given a file path, attempt to parse the file into a Stream.
    '''
    v = Converter()
    v.parseFile(fp, forceSource=forceSource)
    return v.stream

def parseData(dataStr):
    '''Given musical data represented within a Python string, attempt to parse the data into a Stream.
    '''
#     if common.isListLike(dataStr):
#         environLocal.printDebug(['parseData dataStr', dataStr])
    v = Converter()
    v.parseData(dataStr)
    return v.stream

def parseURL(url, forceSource=False):
    '''Given a URL, attempt to download and parse the file into a Stream. Note: URL downloading will not happen automatically unless the user has set their Environment "autoDownload" preference to "allow". 
    '''
    v = Converter()
    v.parseURL(url)
    return v.stream

def parse(value, *args, **keywords):
    '''Given a file path, encoded data in a Python string, or a URL, attempt to parse the item into a Stream. Note: URL downloading will not happen automatically unless the user has set their Environment "autoDownload" preference to "allow". 

    >>> s = parse(["E4 r f# g=lastG trip{b-8 a g} c", "3/4"])
    >>> s = parse("E8 f# g#' G f g# g G#", "2/4")

    '''

    #environLocal.printDebug(['attempting to parse()', value])
    if 'forceSource' in keywords.keys():
        forceSource = keywords['forceSource']
    else:   
        forceSource = False

    if common.isListLike(value) or len(args) > 0: # tiny notation list
        if len(args) > 0: # add additional args to a lost
            value = [value] + list(args)
        return parseData(value)
    elif os.path.exists(value):
        return parseFile(value, forceSource=forceSource)
    elif value.startswith('http://'): 
        # its a url; may need to broaden these criteria
        return parseURL(value, forceSource=forceSource)
    else:
        return parseData(value)



def freeze(streamObj, fp=None):
    '''Given a file path, attempt to parse the file into a Stream.
    '''
    v = StreamFreezer(streamObj)
    return v.writePickle(fp) # returns fp


def unfreeze(fp):
    '''Given a file path, attempt to parse the file into a Stream.
    '''
    v = StreamFreezer()
    v.openPickle(fp)
    return v.stream




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


    def testParseURL(self):
        urlA = 'http://kern.ccarh.org/cgi-bin/ksdata?l=users/craig/classical/schubert/piano/d0576&file=d0576-06.krn&f=xml'
        urlB = 'http://kern.ccarh.org/cgi-bin/ksdata?l=users/craig/classical/schubert/piano/d0576&file=d0576-06.krn&f=kern'
        urlC = 'http://kern.ccarh.org/cgi-bin/ksdata?l=users/craig/classical/bach/cello&file=bwv1007-01.krn&f=xml'
        for url in [urlA, urlB, urlC]:
            post = parseURL(url)


    def testFreezer(self):
        from music21 import stream, note, corpus
        s = stream.Stream()
        n = note.Note()
        s.append(n)

        s = corpus.parseWork('bach')

        aConverter = StreamFreezer(s)
        fp = aConverter.writePickle()

        aConverter.openPickle(fp)
        #aConverter.stream
        aConverter.stream.show()


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
        notes = part.flat.notes
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


        notes = part.flat.notes
        self.assertEqual(len(notes), 11)


    def testConversionMXClefPrimitive(self):

        from music21.musicxml import testPrimitive
        mxString = testPrimitive.clefs12a
        a = parse(mxString)
        part = a[0]

        clefs = part.flat.getElementsByClass(clef.Clef)
        self.assertEqual(len(clefs), 18)


    def testConversionMXClefTimeCorpus(self):
    
        from music21 import corpus
        a = corpus.parseWork('luca')

        # there should be only one clef in each part
        clefs = a[0].flat.getElementsByClass(clef.Clef)
        self.assertEqual(len(clefs), 1)
        self.assertEqual(clefs[0].sign, 'G')

        # second part
        clefs = a[1].flat.getElementsByClass(clef.Clef)
        self.assertEqual(len(clefs), 1)
        self.assertEqual(clefs[0].octaveChange, -1)
        self.assertEqual(type(clefs[0]).__name__, 'Treble8vbClef')

        # third part
        clefs = a[2].flat.getElementsByClass(clef.Clef)
        self.assertEqual(len(clefs), 1)

        # check time signature count
        ts = a[1].flat.getElementsByClass(meter.TimeSignature)
        self.assertEqual(len(ts), 4)

        from music21 import corpus
        a = corpus.parseWork('mozart/k156/movement4')

        # violin part
        clefs = a[0].flat.getElementsByClass(clef.Clef)
        self.assertEqual(len(clefs), 1)
        self.assertEqual(clefs[0].sign, 'G')

        # viola
        clefs = a[2].flat.getElementsByClass(clef.Clef)
        self.assertEqual(len(clefs), 1)
        self.assertEqual(clefs[0].sign, 'C')

        # violoncello
        clefs = a[3].flat.getElementsByClass(clef.Clef)
        self.assertEqual(len(clefs), 1)
        self.assertEqual(clefs[0].sign, 'F')

        # check time signatures
        # there are
        ts = a[0].flat.getElementsByClass(meter.TimeSignature)
        self.assertEqual(len(ts), 1)


    def testConversionMXArticulations(self):
        from music21.musicxml import testPrimitive
        mxString = testPrimitive.articulations01
        a = parse(mxString)
        part = a[0]

        notes = part.flat.getElementsByClass(note.Note)
        self.assertEqual(len(notes), 4)
        post = []
        match = ["<class 'music21.articulations.Staccatissimo'>", 
        "<class 'music21.articulations.Accent'>", 
        "<class 'music21.articulations.Staccato'>", 
        "<class 'music21.articulations.Tenuto'>"]
        for i in range(len(notes)):
            post.append(str(notes[i].articulations[0].__class__))
        self.assertEqual(post, match)


    def testConversionMXKey(self):
        from music21.musicxml import testPrimitive
        mxString = testPrimitive.keySignatures13a
        a = parse(mxString)
        part = a[0]

        keyList = part.flat.getElementsByClass(key.KeySignature)
        self.assertEqual(len(keyList), 46)



#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [parse, parseFile, parseData, parseURL, Converter, ConverterMusicXML, ConverterHumdrum]


if __name__ == "__main__":
    music21.mainTest(Test)
    #music21.mainTest(Test, TestExternal)

