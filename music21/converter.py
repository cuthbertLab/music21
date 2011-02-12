#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         converter.py
# Purpose:      Provide a common way to create Streams from any data music21
#               handles
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009-2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
music21.converter contains tools for loading music from various file formats,
whether from disk, from the web, or from text, into 
music21.stream.:class:`~music21.stream.Score` objects (or
other similar stream objects).  

The most powerful and easy to use tool is the :func:`~music21.converter.parse` 
function. Simply provide a filename, URL, or text string and, if the format 
is supported, a :class:`~music21.stream.Score` will be returned. 

This is the most general public interface for all formats.  Programmers
adding their own formats to the system should provide an interface here to
their own parsers (such as humdrum, musicxml, etc.)

The second and subsequent times that a file is loaded it will likely be much
faster since we store a parsed version of each file as a "pickle" object in
the temp folder on the disk.

>>> from music21 import *
>>> #_DOCS_SHOW s = converter.parse('d:/mydocs/schubert.krn')
>>> s = converter.parse(humdrum.testFiles.schubert) #_DOCS_HIDE
>>> s
<music21.stream.Score object at 0x...>
'''


import doctest
import unittest
import os
import urllib
import time
import copy
import zipfile

try:
    import cPickle as pickleMod
except ImportError:
    import pickle as pickleMod


import music21

from music21 import chord
from music21 import clef
from music21 import common
from music21 import dynamics
from music21 import expressions
from music21 import humdrum
from music21 import instrument
from music21 import key
from music21 import meter
from music21 import midi
from music21 import musicxml
from music21 import note
from music21 import stream
from music21 import tinyNotation

from music21.abc import base as abcModule
from music21.abc import translate as abcTranslate
from music21.musedata import base as musedataModule
from music21.musedata import translate as musedataTranslate

from music21.romanText import base as romanTextModule
from music21.romanText import translate as romanTextTranslate


from music21 import environment
_MOD = 'converter.py'
environLocal = environment.Environment(_MOD)

#-------------------------------------------------------------------------------
class ArchiveManagerException(Exception):
    pass

class PickleFilterException(Exception):
    pass

class ConverterException(Exception):
    pass

class ConverterFileException(Exception):
    pass


#-------------------------------------------------------------------------------
class ArchiveManager(object):
    '''Before opening a file path, this class can check if this is an archived file collection, such as a .zip or or .mxl file. This will return the data from the archive.
    '''
    # for info on mxl files, see
    # http://www.recordare.com/xml/compressed-mxl.html

    def __init__(self, fp, archiveType='zip'):
        '''Only archive type supported now is zip. 
        '''
        self.fp = fp
        self.archiveType = archiveType

    def isArchive(self):
        '''Return True or False if the filepath is an archive of the supplied archiveType.
        '''
        if self.archiveType == 'zip':
            # some .md files can be zipped
            if self.fp.endswith('mxl') or self.fp.endswith('md'):
                # try to open it, as some mxl files are not zips
                try:
                    f = zipfile.ZipFile(self.fp, 'r')
                except zipfile.BadZipfile:
                    return False
                return True
            elif self.fp.endswith('zip'):
                return True
        else:
            raise ArchiveManagerException('no support for archiveType: %s' % self.archiveType)
        return False


    def getNames(self):
        '''Return a list of all names contained in this archive. 
        '''
        post = []
        if self.archiveType == 'zip':
            f = zipfile.ZipFile(self.fp, 'r')
            for subFp in f.namelist():
                post.append(subFp)
            f.close()
        return post


    def getData(self, name=None, format='musicxml' ):
        '''Return data from the archive by name. If no name is given, a default may be available. 

        For 'musedata' format this will be a list of strings. For 'musicxml' this will be a single string. 
        '''
        if self.archiveType == 'zip':
            f = zipfile.ZipFile(self.fp, 'r')
            if name == None and format == 'musicxml': # try to auto-harvest
                # will return data as a string
                # note that we need to read the META-INF/container.xml file
                # and get the rootfile full-path
                # a common presentation will be like this:
                # ['musicXML.xml', 'META-INF/', 'META-INF/container.xml']
                for subFp in f.namelist():
                    # the name musicXML.xml is often used, or get top level
                    # xml file
                    if 'META-INF' in subFp: 
                        continue
                    if subFp.endswith('.xml'):
                        post = f.read(subFp)
                        break

            elif name == None and format == 'musedata': 
                # this might concatenate all parts into a single string
                # or, return a list of strings
                # alternative, a different method might return one at a time
                mdd = musedataModule.MuseDataDirectory(f.namelist())
                environLocal.printDebug(['mdd object, namelist', mdd, f.namelist])

                post = []
                for subFp in mdd.getPaths():
                    component = f.open(subFp, 'rU')
                    post.append(''.join(component.readlines()))    
                    
                    # note: the following methods do not properly employ
                    # universal new lines; this is a python problem:
                    # http://bugs.python.org/issue6759
                    #post.append(component.read())    
                    #post.append(f.read(subFp, 'U'))    
                    #msg.append('\n/END\n')
    
            f.close()
        else:
            raise ArchiveManagerException('no support for extension: %s' % self.archiveType)

        return post


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
        fpScratch = environLocal.getRootTempDir()
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
    '''This class is used to freeze a Stream, preparing it for pickling. 
    '''

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
        '''For a supplied Stream, write a pickled version.
        '''
        if fp == None:
            dir = environLocal.getRootTempDir()
            fp = self._getPickleFp(dir)
        elif os.sep in fp: # assume its a complete path
            fp = fp
        else:
            dir = environLocal.getRootTempDir()
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
        '''For a supplied file path to a pickled stream, unpickle
        '''
        if os.sep in fp: # assume its a complete path
            fp = fp
        else:
            dir = environLocal.getRootTempDir()
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
# Converters are associated classes; they are not subclasses, but all most define a pareData() method, a parseFile() method, and a .stream attribute or property. 


#-------------------------------------------------------------------------------
class ConverterHumdrum(object):
    '''Simple class wrapper for parsing Humdrum data provided in a file or in a string.
    '''

    def __init__(self):
        self.stream = None

    #---------------------------------------------------------------------------
    def parseData(self, humdrumString, number=None):
        '''Open Humdrum data from a string

        >>> humdata = '**kern\\n*M2/4\\n=1\\n24r\\n24g#\\n24f#\\n24e\\n24c#\\n24f\\n24r\\n24dn\\n24e-\\n24gn\\n24e-\\n24dn\\n*-'
        >>> c = ConverterHumdrum()
        >>> s = c.parseData(humdata)
        '''
        self.data = humdrum.parseData(humdrumString)
        #self.data.stream.makeNotation()
        
        self.stream = self.data.stream
        return self.data

    def parseFile(self, filepath, number=None):
        '''Open Humdram data from a file path.'''
        self.data = humdrum.parseFile(filepath)
        #self.data.stream.makeNotation()

        self.stream = self.data.stream
        return self.data

#-------------------------------------------------------------------------------
class ConverterTinyNotation(object):
    '''Simple class wrapper for parsing TinyNotation data provided in a file or in a string.
    '''

    def __init__(self):
        self.stream = None

    #---------------------------------------------------------------------------
    def parseData(self, tnData, number=None):
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

    def parseFile(self, fp, number=None):
        '''Open TinyNotation data from a file path.'''

        f = open(fp)
        tnStr = f.read()
        f.close()
        self.stream = tinyNotation.TinyNotationStream(tnStr)


#-------------------------------------------------------------------------------
class ConverterMusicXML(object):
    '''Converter for MusicXML
    '''

    def __init__(self, forceSource):
        self._mxScore = None # store the musicxml object representation
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

    def _getStream(self):
        return self._stream

    stream = property(_getStream)


    #---------------------------------------------------------------------------
    def parseData(self, xmlString, number=None):
        '''Open MusicXML data from a string.'''
        c = musicxml.Document()
        c.read(xmlString)
        self._mxScore = c.score #  the mxScore object from the musicxml Document
        if len(self._mxScore) == 0:
            raise ConverterException('score from xmlString (%s...) has no parts defined' % xmlString[:30])
        self.load()

    def parseFile(self, fp, number=None):
        '''Open from a file path; check to see if there is a pickled
        version available and up to date; if so, open that, otherwise
        open source.
        '''
        # return fp to load, if pickle needs to be written, fp pickle
        # this should be able to work on a .mxl file, as all we are doing
        # here is seeing which is more recent

        pfObj = PickleFilter(fp, self.forceSource)
        # fpDst here is the file path to load, which may or may not be
        # a pickled file 
        fpDst, writePickle, fpPickle = pfObj.status() # get status

        formatSrc = common.findFormatFile(fp)
        # here we determine if we have pickled file or a musicxml file
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
                    # some old pickles have no versions
                    pass
                pickleError = True
                writePickle = True
                fpDst = fp # set to orignal file path

        if format == 'musicxml' or (formatSrc == 'musicxml' and pickleError):
            environLocal.printDebug(['opening musicxml file:', fpDst])

            # here, we can see if this is a mxl or similar archive
            arch = ArchiveManager(fpDst)
            if arch.isArchive():
                c.read(arch.getData())
            else: # its a file path
                c.open(fpDst)

        # get mxScore object from .score attribute
        self._mxScore = c.score

        # check that we have parts
        if len(self._mxScore) == 0:
            raise ConverterException('score from file path (...%s) no parts defined' % fp[-10:])

        # movement titles can be stored in more than one place in musicxml
        # manually insert file name as a title if no titles are defined
        if self._mxScore.get('movementTitle') == None:
            mxWork = self._mxScore.get('workObj')
            if mxWork == None or mxWork.get('workTitle') == None: 
                junk, fn = os.path.split(fp)
                # set as movement title
                self._mxScore.set('movementTitle', fn)

        # only write pickle if we have parts defined
        if writePickle:
            if fpPickle == None: # if original file cannot be found
                raise ConverterException('attempting to write pickle but no file path is given')
            environLocal.printDebug(['writing pickled file', fpPickle])
            c.writePickle(fpPickle)

        self.load()




#-------------------------------------------------------------------------------
class ConverterMidi(object):
    '''Simple class wrapper for parsing MIDI.
    '''

    def __init__(self):
        # always create a score instance
        self._stream = stream.Score()

    def parseData(self, strData, number=None):
        '''Get MIDI data from a binary string representation.
        '''
        mf = midi.MidiFile()
        # do not need to call open or close on MidiFile instance
        mf.readstr(strData)
        self._stream.midiFile = mf

    def parseFile(self, fp, number=None):
        '''Get MIDI data from a file path.'''

        mf = midi.MidiFile()
        mf.open(fp)
        mf.read()
        mf.close()
        self._stream.midiFile = mf

    def _getStream(self):
        return self._stream

    stream = property(_getStream)




#-------------------------------------------------------------------------------
class ConverterABC(object):
    '''Simple class wrapper for parsing ABC.
    '''

    def __init__(self):
        # always create a score instance
        self._stream = stream.Score()

    def parseData(self, strData, number=None):
        '''Get ABC data, as token list, from a string representation. If more than one work is defined in the ABC data, a  :class:`~music21.stream.Opus` object will be returned; otherwise, a :class:`~music21.stream.Score` is returned.
        '''
        af = abcModule.ABCFile()
        # do not need to call open or close 
        abcHandler = af.readstr(strData, number=number)
        # set to stream
        if abcHandler.definesReferenceNumbers():
            # this creates an Opus object, not a Score object
            self._stream = abcTranslate.abcToStreamOpus(abcHandler,
                number=number)
        else: # just one work
            abcTranslate.abcToStreamScore(abcHandler, self._stream)

    def parseFile(self, fp, number=None):
        '''Get MIDI data from a file path. If more than one work is defined in the ABC data, a  :class:`~music21.stream.Opus` object will be returned; otherwise, a :class:`~music21.stream.Score` is returned.

        If `number` is provided, and this ABC file defines multiple works with a X: tag, just the specified work will be returned. 
        '''
        environLocal.printDebug(['ConverterABC.parseFile: got number', number])

        af = abcModule.ABCFile()
        af.open(fp)
        # returns a handler instance of parse tokens
        abcHandler = af.read(number=number) 
        af.close()

        # only create opus if multiple ref numbers
        # are defined; if a number is given an opus will no be created
        if abcHandler.definesReferenceNumbers():
            # this creates a Score or Opus object, depending on if a number
            # is given
            self._stream = abcTranslate.abcToStreamOpus(abcHandler,
                           number=number)
        # just get a single work
        else: 
            abcTranslate.abcToStreamScore(abcHandler, self._stream)

    def _getStream(self):
        return self._stream

    stream = property(_getStream)


class ConverterRomanText(object):
    '''Simple class wrapper for parsing roman text harmonic definitions.
    '''

    def __init__(self):
        # always create a score instance
        self._stream = stream.Score()

    def parseData(self, strData, number=None):
        '''
        '''
        rtf = romanTextModule.RTFile()
        rtHandler = rtf.readstr(strData) 
        romanTextTranslate.romanTextToStreamScore(rtHandler, self._stream)

    def parseFile(self, fp, number=None):
        '''
        '''
        rtf = romanTextModule.RTFile()
        rtf.open(fp)
        # returns a handler instance of parse tokens
        rtHandler = rtf.read() 
        rtf.close()
        romanTextTranslate.romanTextToStreamScore(rtHandler, self._stream)

    def _getStream(self):
        return self._stream

    stream = property(_getStream)




#-------------------------------------------------------------------------------
class ConverterMuseData(object):
    '''Simple class wrapper for parsing ABC.
    '''

    def __init__(self):
        # always create a score instance
        self._stream = stream.Score()

    def parseData(self, strData, number=None):
        '''Get musedata from a string representation. 

        '''
        if common.isStr(strData):
            strDataList = [strData]
        else:
            strDataList = strData

        mdw = musedataModule.MuseDataWork()

        for strData in strDataList:
            mdw.addString(strData)

        musedataTranslate.museDataWorkToStreamScore(mdw, self._stream)


    def parseFile(self, fp, number=None):
        '''
        '''
        mdw = musedataModule.MuseDataWork()

        af = ArchiveManager(fp)

        #environLocal.printDebug(['ConverterMuseData: parseFile', fp, af.isArchive()])
        # for dealing with one or more files
        if fp.endswith('.zip') or af.isArchive():
            #environLocal.printDebug(['ConverterMuseData: found archive', fp])
            # get data will return all data from the zip as a single string
            for partStr in af.getData(format='musedata'):
                #environLocal.printDebug(['partStr', partStr])
                mdw.addString(partStr)            
        else:
            if os.path.isdir(fp):
                mdd = musedataModule.MuseDataDirectory(fp)
                fpList = mdd.getPaths()
            elif not common.isListLike(fp):
                fpList = [fp]            
            else:
                fpList = fp

            for fp in fpList:
                mdw.addFile(fp)

        environLocal.printDebug(['ConverterMuseData: mdw file count', len(mdw.files)])

        musedataTranslate.museDataWorkToStreamScore(mdw, self._stream)



    def _getStream(self):
        return self._stream

    stream = property(_getStream)








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
        elif format == 'midi':
            self._converter = ConverterMidi()
        elif format == 'humdrum':
            self._converter = ConverterHumdrum()
        elif format.lower() in ['tinynotation']:
            self._converter = ConverterTinyNotation()
        elif format == 'abc':
            self._converter = ConverterABC()
        elif format == 'musedata':
            self._converter = ConverterMuseData()
        elif format == 'text': # based on extension
            # presently, all text files are treated as roman text
            # may need to handle various text formats
            self._converter = ConverterRomanText()
        elif format.lower() in ['romantext']:
            self._converter = ConverterRomanText()
        else:
            raise ConverterException('no such format: %s' % format)

    def _getDownloadFp(self, dir, ext, url):
        if dir == None:
            raise ValueError
        return os.path.join(dir, 'm21-' + common.getMd5(url) + ext)

    def parseFile(self, fp, number=None, format=None, forceSource=False):
        '''Given a file path, parse and store a music21 Stream.
        '''
        #environLocal.printDebug(['attempting to parseFile', fp])
        if not os.path.exists(fp):
            raise ConverterFileException('no such file eists: %s' % fp)

        if format is None:
            # if the file path is to a directory, assume it is a collection of 
            # musedata parts
            if os.path.isdir(fp):
                format = 'musedata'
            else:
                format = common.findFormatFile(fp) 
        self._setConverter(format, forceSource=forceSource)
        self._converter.parseFile(fp, number=number)


    def parseData(self, dataStr, number=None, format=None, forceSource=False):
        '''Given raw data, determine format and parse into a music21 Stream.
        '''
        if common.isListLike(dataStr):
            format = 'tinyNotation'

        # get from data in string if not specified        
        if format is None: # its a string
            dataStr = dataStr.lstrip()
            if dataStr.startswith('<?xml') or dataStr.startswith('musicxml:'):
                format = 'musicxml'
            elif dataStr.startswith('MThd') or dataStr.startswith('midi:'):
                format = 'midi'
            elif dataStr.startswith('!!!') or dataStr.startswith('**') or dataStr.startswith('humdrum:'):
                format = 'humdrum'
            elif dataStr.startswith('tinynotation:'):
                format = 'tinyNotation'
            # assume must define a meter and a key
            elif 'WK#:' in dataStr and 'measure' in dataStr:
                format = 'musedata'
            elif 'M:' in dataStr and 'K:' in dataStr:
                format = 'abc'
            elif 'Time Signature:' in dataStr and 'm1' in dataStr:
                format = 'romanText'
            else:
                raise ConverterException('no such format found for: %s' % dataStr)

        self._setConverter(format)
        self._converter.parseData(dataStr, number=number)


    def parseURL(self, url, format=None, number=None):
        '''Given a url, download and parse the file into a music21 Stream.

        Note that this checks the user Environment `autoDownlaad` setting before downloading. 
        '''
        autoDownload = environLocal['autoDownload']
        if autoDownload == 'allow':
            pass
        elif autoDownload in ['deny', 'ask']:
            # TODO: plan here is to use an interactive dialog
            raise ConverterException('automatic downloading of URLs is presently set to "%s"; configure your Environment "autoDownload" setting to "allow" to permit automatic downloading.' % autoDownload)

        # this format check is here first to see if we can find the format
        # in the url; if forcing a format we do not need this
        # we do need the file extension to construct file path below
        formatFromURL, ext = common.findFormatExtURL(url)
        if formatFromURL is None: # cannot figure out what it is
            raise ConverterException('cannot determine file format of url: %s' % url)

        dir = environLocal.getRootTempDir()
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
        if format is None: # if not provided as an argument
            format = common.findFormatFile(fp) 
        self._setConverter(format, forceSource=False)
        self._converter.parseFile(fp, number=number)


    #---------------------------------------------------------------------------
    # properties

    def _getStream(self):
        '''All converters have to have a stream property or attribute.
        '''
        return self._converter.stream 
        # not _stream: please don't look in other objects' private variables; 
        #              humdrum worked differently.

    stream = property(_getStream)




#-------------------------------------------------------------------------------
# module level convenience methods


def parseFile(fp, number=None, format=None, forceSource=False):
    '''Given a file path, attempt to parse the file into a Stream.
    '''
    v = Converter()
    v.parseFile(fp, number=number, format=format, forceSource=forceSource)
    return v.stream

def parseData(dataStr, number=None, format=None):
    '''Given musical data represented within a Python string, attempt to parse the data into a Stream.
    '''
    v = Converter()
    v.parseData(dataStr, number=number, format=format)
    return v.stream

def parseURL(url, number=None, format=None, forceSource=False):
    '''Given a URL, attempt to download and parse the file into a Stream. Note: URL downloading will not happen automatically unless the user has set their Environment "autoDownload" preference to "allow". 
    '''
    v = Converter()
    v.parseURL(url, format=format)
    return v.stream

def parse(value, *args, **keywords):
    '''Given a file path, encoded data in a Python string, or a URL, attempt to parse the item into a Stream. Note: URL downloading will not happen automatically unless the user has set their Environment "autoDownload" preference to "allow". 

    >>> from music21 import *
    >>> s = converter.parse(["E4 r f# g=lastG trip{b-8 a g} c", "3/4"])
    >>> s.getElementsByClass(meter.TimeSignature)[0]
    <music21.meter.TimeSignature 3/4>
    
    >>> s2 = converter.parse("E8 f# g#' G f g# g G#", "2/4")
    >>> s2.show('text')
    {0.0} <music21.meter.TimeSignature 2/4>
    {0.0} <music21.note.Note E>
    {0.5} <music21.note.Note F#>
    {1.0} <music21.note.Note G#>
    {1.5} <music21.note.Note G>
    {2.0} <music21.note.Note F>
    {2.5} <music21.note.Note G#>
    {3.0} <music21.note.Note G>
    {3.5} <music21.note.Note G#>
    
    '''

    #environLocal.printDebug(['attempting to parse()', value])
    if 'forceSource' in keywords.keys():
        forceSource = keywords['forceSource']
    else:   
        forceSource = False

    # see if a work number is defined; for multi-work collections
    if 'number' in keywords.keys():
        number = keywords['number']
    else:   
        number = None

    if 'format' in keywords.keys():
        format = keywords['format']
    else:   
        format = None

    if common.isListLike(value) or len(args) > 0: # tiny notation list
        if len(args) > 0: # add additional args to a lost
            value = [value] + list(args)
        return parseData(value, number=number)
     # a midi string, must come before os.path.exists test
    elif value.startswith('MThd'):
        return parseData(value, number=number, format=format)
    elif os.path.exists(value):
        return parseFile(value, number=number, format=format, forceSource=forceSource)
    elif value.startswith('http://'): 
        # its a url; may need to broaden these criteria
        return parseURL(value, number=number, format=format, forceSource=forceSource)
    else:
        return parseData(value, number=number, format=format)



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
        #a.show('t')
        self.assertEqual(len(a), 2) # one part, plus metadata
        for part in a.getElementsByClass(stream.Part):
            self.assertEqual(len(part), 7) # seven measures
            measures = part.getElementsByClass(stream.Measure)
            self.assertEqual(int(measures[0].number), 1)
            self.assertEqual(int(measures[-1].number), 7)

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
        for part in a.getElementsByClass(stream.Part):
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
            if "Note" in n.classes:
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

        # try to go the other way
        post = a.musicxml
        #a.show()        

    def testConversionMXKey(self):
        from music21.musicxml import testPrimitive
        mxString = testPrimitive.keySignatures13a
        a = parse(mxString)
        part = a[0]

        keyList = part.flat.getElementsByClass(key.KeySignature)
        self.assertEqual(len(keyList), 46)


    def testConversionMXMetadata(self):

        from music21.musicxml import testPrimitive
        from music21.musicxml import testFiles

        a = parse(testFiles.mozartTrioK581Excerpt)
        self.assertEqual(a.metadata.composer, 'Wolfgang Amadeus Mozart')
        self.assertEqual(a.metadata.title, 'Quintet for Clarinet and Strings')
        self.assertEqual(a.metadata.movementName, 'Menuetto (Excerpt from Second Trio)')

        a = parse(testFiles.binchoisMagnificat)
        self.assertEqual(a.metadata.composer, 'Gilles Binchois')
        # this gets the best title available, even though this is movement title
        self.assertEqual(a.metadata.title, 'Excerpt from Magnificat secundi toni')


    def testConversionMXBarlines(self):
        from music21 import bar
        from music21.musicxml import testPrimitive
        a = parse(testPrimitive.barlines46a)
        part = a[0]
        barlineList = part.flat.getElementsByClass(bar.Barline)
        self.assertEqual(len(barlineList), 11)

    def testConversionMXLayout(self):
        
        from music21.musicxml import testPrimitive
        from music21 import stream, layout

        a = parse(testPrimitive.systemLayoutTwoPart)
        #a.show()

        part = a.getElementsByClass(stream.Part)[0]
        systemLayoutList = part.flat.getElementsByClass(layout.SystemLayout)
        self.assertEqual(len(systemLayoutList), 6)


    def testConversionMXTies(self):
        
        from music21.musicxml import testPrimitive
        from music21 import stream, layout

        a = parse(testPrimitive.multiMeasureTies)
        #a.show()

        countTies = 0
        countStartTies = 0
        for p in a.parts:
            post = p.getClefs()[0]
            self.assertEqual(isinstance(post, clef.TenorClef), True)
            for n in p.flat.notes:
                if n.tie != None:
                    countTies += 1
                    if n.tie.type == 'start' or n.tie.type =='continue':
                        countStartTies += 1

        self.assertEqual(countTies, 57)
        self.assertEqual(countStartTies, 40)


    def testConversionMXInstrument(self):
        from music21 import corpus
        s = corpus.parseWork('beethoven/opus18no1/movement3.xml')
        #s.show()
        is1 = s.parts[0].flat.getElementsByClass('Instrument')
        self.assertEqual(len(is1), 1)
        is2 = s.parts[1].flat.getElementsByClass('Instrument')
        self.assertEqual(len(is2), 1)

        is3 = s.parts[2].flat.getElementsByClass('Instrument')
        self.assertEqual(len(is3), 1)

        is4 = s.parts[3].flat.getElementsByClass('Instrument')
        self.assertEqual(len(is4), 1)



    def testConversionMidiBasic(self):
        import common

        dir = common.getPackageDir(relative=False, remapSep=os.sep)
        for fp in dir:
            if fp.endswith('midi'):
                break

        dirLib = os.path.join(fp, 'testPrimitive')
        # a simple file created in athenacl
        fp = os.path.join(dirLib, 'test01.mid')

        s = parseFile(fp)
        s = parse(fp)

        c = ConverterMidi()
        c.parseFile(fp)

        # try low level string data passing
        f = open(fp, 'rb')
        data = f.read()
        f.close()
        
        c.parseData(data)

        # try module-leve; function
        parseData(data)
        parse(data)


    def testConversionMidiNotes(self):
        import common, meter, key

        fp = os.path.join(common.getSourceFilePath(), 'midi', 'testPrimitive',  'test01.mid')
        # a simple file created in athenacl
        #for fn in ['test01.mid', 'test02.mid', 'test03.mid', 'test04.mid']:
        s = parseFile(fp)
        #s.show()
        self.assertEqual(len(s.flat.getElementsByClass(note.Note)), 17)


        # has chords and notes
        fp = os.path.join(common.getSourceFilePath(), 'midi', 'testPrimitive',  'test05.mid')
        s = parseFile(fp)
        #s.show()
        environLocal.printDebug(['\nopening fp', fp])

        self.assertEqual(len(s.flat.getElementsByClass(note.Note)), 2)
        self.assertEqual(len(s.flat.getElementsByClass(chord.Chord)), 3)

        self.assertEqual(len(s.flat.getElementsByClass(meter.TimeSignature)), 0)
        self.assertEqual(len(s.flat.getElementsByClass(key.KeySignature)), 0)


        # this sample has eight note triplets
        fp = os.path.join(common.getSourceFilePath(), 'midi', 'testPrimitive',  'test06.mid')
        s = parseFile(fp)
        #s.show()

        environLocal.printDebug(['\nopening fp', fp])

        #s.show()
        dList = [n.quarterLength for n in s.flat.notes[:30]]
        match = [0.5, 0.5, 1.0, 0.5, 0.5, 0.5, 0.5, 1.0, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.33333333333333331, 0.33333333333333331, 0.33333333333333331, 0.5, 0.5, 1.0]
        self.assertEqual(dList, match)


        self.assertEqual(len(s.flat.getElementsByClass('TimeSignature')), 1)
        self.assertEqual(len(s.flat.getElementsByClass('KeySignature')), 1)


        # this sample has sixteenth note triplets
        # TODO much work is still needed on getting timing right
        # this produces numerous errors in makeMeasure partitioning
        fp = os.path.join(common.getSourceFilePath(), 'midi', 'testPrimitive',  'test07.mid')
        #environLocal.printDebug(['\nopening fp', fp])
        s = parseFile(fp)
        #s.show('t')
        self.assertEqual(len(s.flat.getElementsByClass('TimeSignature')), 1)
        self.assertEqual(len(s.flat.getElementsByClass('KeySignature')), 1)

       


        # this sample has dynamic changes in key signature
        fp = os.path.join(common.getSourceFilePath(), 'midi', 'testPrimitive',  'test08.mid')
        #environLocal.printDebug(['\nopening fp', fp])
        s = parseFile(fp)
        #s.show('t')
        self.assertEqual(len(s.flat.getElementsByClass('TimeSignature')), 1)
        found = s.flat.getElementsByClass('KeySignature')
        self.assertEqual(len(found), 3)
        # test the right keys
        self.assertEqual(found[0].sharps, -3)
        self.assertEqual(found[1].sharps, 3)
        self.assertEqual(found[2].sharps, -1)


    def testConversionMXRepeats(self):
        from music21 import bar
        from music21.musicxml import testPrimitive

        mxString = testPrimitive.simpleRepeat45a
        s = parse(mxString)

        part = s.parts[0]
        measures = part.getElementsByClass('Measure')
        self.assertEqual(measures[0].leftBarline, None)
        self.assertEqual(measures[0].rightBarline.style, 'light-heavy')

        self.assertEqual(measures[1].leftBarline, None)
        self.assertEqual(measures[1].rightBarline.style, 'light-heavy')

        mxString = testPrimitive.repeatMultipleTimes45c
        s = parse(mxString)

        self.assertEqual(len(s.flat.getElementsByClass(bar.Barline)), 4)
        part = s.parts[0]
        measures = part.getElementsByClass('Measure')

        #s.show()



    def testConversionABCOpus(self):
        
        from music21.abc import testFiles
        from music21 import corpus
        from music21 import stream

        s = parse(testFiles.theAleWifesDaughter)
        # get a Stream object, not an opus
        self.assertEqual(isinstance(s, stream.Score), True)
        self.assertEqual(isinstance(s, stream.Opus), False)
        self.assertEqual(len(s.flat.notes), 66)

        # a small essen collection
        op = corpus.parseWork('essenFolksong/teste')
        # get a Stream object, not an opus
        #self.assertEqual(isinstance(op, stream.Score), True)
        self.assertEqual(isinstance(op, stream.Opus), True)
        self.assertEqual([len(s.flat.notes) for s in op], [33, 51, 59, 33, 29, 174, 67, 88])
        #op.show()

        # get one work from the opus
        s = corpus.parseWork('essenFolksong/teste', number=6)
        self.assertEqual(isinstance(s, stream.Score), True)
        self.assertEqual(isinstance(s, stream.Opus), False)
        self.assertEqual(s.metadata.title, 'Moli hua')

        #s.show()


    def testConversionABCWorkFromOpus(self):
        # test giving a work number at loading
        from music21 import corpus
        s = corpus.parseWork('essenFolksong/han1', number=6)
        self.assertEqual(isinstance(s, stream.Score), True)
        self.assertEqual(s.metadata.title, 'Yi gan hongqi kongzhong piao')
        # make sure that beams are being made
        self.assertEqual(str(s.parts[0].flat.notes[4].beams), '<music21.beam.Beams <music21.beam.Beam 1/start>/<music21.beam.Beam 2/start>>')
        #s.show()



    def testConversionMusedata(self):
        
        from music21.musedata import testFiles
        from music21 import corpus
        from music21 import stream

        cmd = ConverterMuseData()
        cmd.parseData(testFiles.bach_cantata5_mvmt3)
        s = cmd.stream
        #s.show()

        # test data id
        s = parse(testFiles.bach_cantata5_mvmt3)
        self.assertEqual(s.metadata.title, 'Wo soll ich fliehen hin')
        self.assertEqual(len(s.parts), 3)


        fp = os.path.join(common.getSourceFilePath(), 'musedata', 'testZip.zip')
        s = parse(fp)
        self.assertEqual(len(s.parts), 4)
        #s.show()



    def testMixedArchiveHandling(self):
        '''Test getting data out of musedata or musicxml zip files.
        '''
        fp = os.path.join(common.getSourceFilePath(), 'musicxml', 'testMxl.mxl')
        af = ArchiveManager(fp)
        # for now, only support zip
        self.assertEqual(af.archiveType, 'zip')
        self.assertEqual(af.isArchive(), True)
        # if this is a musicxml file, there will only be single file; we
        # can cal get datat to get this 
        post = af.getData()
        self.assertEqual(post[:38], '<?xml version="1.0" encoding="UTF-8"?>')
        self.assertEqual(af.getNames(), ['musicXML.xml', 'META-INF/', 'META-INF/container.xml'])

        # test from a file that ends in zip
        # note: this is a stage1 file!
        fp = os.path.join(common.getSourceFilePath(), 'musedata', 'testZip.zip')
        af = ArchiveManager(fp)
        # for now, only support zip
        self.assertEqual(af.archiveType, 'zip')
        self.assertEqual(af.isArchive(), True)
        self.assertEqual(af.getNames(), ['01/', '01/04', '01/02', '01/03', '01/01'] )

        # returns a list of strings
        self.assertEqual(af.getData(format='musedata')[0][:30], '378\n1080  1\nBach Gesells\nchaft')


        #mdw = musedataModule.MuseDataWork()
        # can add a list of strings from getData
        #mdw.addString(af.getData(format='musedata'))
        #self.assertEqual(len(mdw.files), 4)
# 
#         mdpList = mdw.getParts()
#         self.assertEqual(len(mdpList), 4)

        # try to load parse the zip file
        #s = parse(fp)

        # test loading a directory
        fp = os.path.join(common.getSourceFilePath(), 'musedata',
                'testPrimitive', 'test01')
        cmd = ConverterMuseData()
        cmd.parseFile(fp)

#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [parse, parseFile, parseData, parseURL, Converter, ConverterMusicXML, ConverterHumdrum]


if __name__ == "__main__":
    #music21.mainTest(Test, TestExternal)
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)

    elif len(sys.argv) > 1:
        t = Test()
        #t.testConversionMXLayout()
        #t.testConversionMXTies()
        #t.testConversionMXInstrument()
        #t.testConversionMXRepeats()

        #t.testConversionABCOpus()
        #t.testConversionMusedata()

        #t.testMixedArchiveHandling()

        t.testConversionABCWorkFromOpus()


#------------------------------------------------------------------------------
# eof

