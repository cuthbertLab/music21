# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         converter/__init__.py
# Purpose:      Provide a common way to create Streams from any data music21
#               handles
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
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



>>> #_DOCS_SHOW s = converter.parse('d:/mydocs/schubert.krn')
>>> s = converter.parse(humdrum.testFiles.schubert) #_DOCS_HIDE
>>> s
<music21.stream.Score ...>
'''


import unittest

import copy
import os
import re
import types
import urllib
import zipfile

__ALL__ = ['subConverters']

from music21.converter import subConverters

from music21 import exceptions21
from music21 import common
from music21 import stream
from music21.ext import six
from music21 import musedata as musedataModule

from music21 import _version
from music21 import environment
_MOD = 'converter/__init__.py'
environLocal = environment.Environment(_MOD)

# use the faster library if possible (won't be possible on Jython, PyPy, etc.)
try:
    import xml.etree.cElementTree as ETree
except ImportError:
    import xml.etree.ElementTree as ETree



#-------------------------------------------------------------------------------
class ArchiveManagerException(exceptions21.Music21Exception):
    pass

class PickleFilterException(exceptions21.Music21Exception):
    pass

class ConverterException(exceptions21.Music21Exception):
    pass

class ConverterFileException(exceptions21.Music21Exception):
    pass


#-------------------------------------------------------------------------------
class ArchiveManager(object):
    r'''Before opening a file path, this class can check if this is an 
    archived file collection, such as a .zip or or .mxl file. This will return the 
    data from the archive.
    
    >>> fnCorpus = corpus.getWork('bwv66.6', fileExtensions=('.xml',))
    
    This is likely a unicode string
    
    >>> #_DOCS_SHOW fnCorpus
    >>> '/Users/cuthbert/git/music21base/music21/corpus/bach/bwv66.6.mxl' #_DOCS_HIDE
    '/Users/cuthbert/git/music21base/music21/corpus/bach/bwv66.6.mxl'
    >>> am = converter.ArchiveManager(fnCorpus)
    >>> am.isArchive()
    True
    >>> am.getNames()
    ['bwv66.6.xml', 'META-INF/container.xml']
    >>> data = am.getData()
    >>> data[0:70]
    '<?xml version="1.0" encoding="UTF-8"?>\r<!DOCTYPE score-partwise PUBLIC'
    '''
    # for info on mxl files, see
    # http://www.recordare.com/xml/compressed-mxl.html

    def __init__(self, fp, archiveType='zip'):
        '''Only archive type supported now is zip. But .mxl is zip...
        '''
        self.fp = fp
        self.archiveType = archiveType

    def isArchive(self):
        '''
        Return True or False if the filepath is an 
        archive of the supplied archiveType.
        '''
        if self.archiveType == 'zip':
            # some .md files can be zipped
            if self.fp.endswith('mxl') or self.fp.endswith('md'):
                # try to open it, as some mxl files are not zips
                try:
                    unused = zipfile.ZipFile(self.fp, 'r')
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


    def getData(self, name=None, dataFormat='musicxml' ):
        '''Return data from the archive by name. If no name is given, 
        a default may be available.

        For 'musedata' format this will be a list of strings. 
        For 'musicxml' this will be a single string.
        '''
        if self.archiveType == 'zip':
            f = zipfile.ZipFile(self.fp, 'r')
            if name == None and dataFormat == 'musicxml': # try to auto-harvest
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
                        if six.PY3 and isinstance(post, bytes):
                            foundEncoding = re.match(br"encoding=[\'\"](\S*?)[\'\"]", post[:1000])
                            if foundEncoding:
                                defaultEncoding = foundEncoding.group(1).decode('ascii')
                                #print("FOUND ENCODING: ", defaultEncoding)
                            else:
                                defaultEncoding = 'UTF-8'
                            try:
                                post = post.decode(encoding=defaultEncoding)
                            except UnicodeDecodeError: # sometimes windows written...
                                post = post.decode(encoding='utf-16-le')
                                post = re.sub(r"encoding=([\'\"]\S*?[\'\"])", "encoding='UTF-8'", post)

                        break

            elif name == None and dataFormat == 'musedata':
                # this might concatenate all parts into a single string
                # or, return a list of strings
                # alternative, a different method might return one at a time
                mdd = musedataModule.MuseDataDirectory(f.namelist())
                #environLocal.printDebug(['mdd object, namelist', mdd, f.namelist])

                post = []
                for subFp in mdd.getPaths():
                    component = f.open(subFp, 'rU')
                    lines = component.readlines()
                    #environLocal.printDebug(['subFp', subFp, len(lines)])
                    if six.PY2:
                        post.append(''.join(lines))
                    else:
                        try:
                            post.append(''.join([l.decode(encoding='UTF-8') for l in lines]))
                        except UnicodeDecodeError:
                            # python3 UTF-8 fails to read corpus/haydn/opus103/movement1.zip
                            post.append(''.join([l.decode(encoding='ISO-8859-1') for l in lines]))

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
    '''
    Before opening a file path, this class checks to see if there is an up-to-date
    version of the file pickled and stored in the scratch directory.
    
    If the user has not specified a scratch directory, or if forceSource is True
    then a pickle path will not be created.
    '''
    def __init__(self, fp, forceSource=False, number=None):
        '''Provide a file path to check if there is pickled version.

        If forceSource is True, pickled files, if available, will not be
        returned.
        '''
        self.fp = fp
        self.forceSource = forceSource
        self.number = number
        #environLocal.printDebug(['creating pickle filter'])

    def _getPickleFp(self, directory, zipType=None):
        import sys
        if directory == None:
            raise ValueError
        if zipType is None:
            extension = '.p'
        else:
            extension = '.pgz'
        pythonVersion = 'py' + str(sys.version_info[0]) + '.' + str(sys.version_info[1])

        baseName = '-'.join(['m21', _version.__version__, pythonVersion, common.getMd5(self.fp)])
        if self.number is not None:
            baseName += '-' + str(self.number)
        baseName += extension
        
        return os.path.join(directory, baseName)

    def status(self):
        '''
        Given a file path specified with __init__, look for an up to date pickled 
        version of this file path. If it exists, return its fp, otherwise return the 
        original file path.

        Return arguments are file path to load, boolean whether to write a pickle, and 
        the file path of the pickle.
        
        Does not check that fp exists or create the pickle file.
        
        >>> fp = '/Users/Cuthbert/Desktop/musicFile.mxl'
        >>> pickfilt = converter.PickleFilter(fp)
        >>> #_DOCS_SHOW pickfilt.status()
        ('/Users/Cuthbert/Desktop/musicFile.mxl', True, '/var/folders/x5/rymq2tx16lqbpytwb1n_cc4c0000gn/T/music21/m21-18b8c5a5f07826bd67ea0f20462f0b8d.pgz')

        '''
        fpScratch = environLocal.getRootTempDir()
        m21Format = common.findFormatFile(self.fp)

        if m21Format == 'pickle': # do not pickle a pickle
            if self.forceSource:
                raise PickleFilterException('cannot access source file when only given a file path to a pickled file.')
            writePickle = False # cannot write pickle if no scratch dir
            fpLoad = self.fp
            fpPickle = None
        elif fpScratch == None or self.forceSource:
            writePickle = False # cannot write pickle if no scratch dir
            fpLoad = self.fp
            fpPickle = None
        else: # see which is more up to date
            fpPickle = self._getPickleFp(fpScratch, zipType='gz')
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
_registeredSubconverters = []
_deregisteredSubconverters = [] # default subconverters to skip

def resetSubconverters():
    '''
    Reset state to default (removing all registered and deregistered subconverters.
    '''
    global _registeredSubconverters # pylint: disable=global-statement
    global _deregisteredSubconverters # pylint: disable=global-statement
    _registeredSubconverters = []
    _deregisteredSubconverters = []

def registerSubconverter(newSubConverter):
    '''
    Add a Subconverter to the list of registered subconverters.
    
    Example, register a converter for the obsolete Amiga composition software Sonix (so fun...)
    
    >>> class ConverterSonix(converter.subConverters.SubConverter):
    ...    registerFormats = ('sonix',)
    ...    registerInputExtensions = ('mus',)
    >>> converter.registerSubconverter(ConverterSonix)
    >>> scf = converter.Converter().getSubConverterFormats()
    >>> for x in sorted(list(scf.keys())):
    ...     x, scf[x] 
    ('abc', <class 'music21.converter.subConverters.ConverterABC'>)
    ...
    ('sonix', <class 'music21.ConverterSonix'>)   
    ...

    See `converter.qmConverter` for an example of an extended subconverter.

    >>> converter.resetSubconverters() #_DOCS_HIDE

    '''
    _registeredSubconverters.append(newSubConverter)

def unregisterSubconverter(removeSubconverter):
    '''
    Remove a Subconverter from the list of registered subconverters.
    
    >>> converter.resetSubconverters() #_DOCS_HIDE    
    >>> mxlConverter = converter.subConverters.ConverterMusicXML

    >>> c = converter.Converter()
    >>> mxlConverter in c.subconvertersList()
    True
    >>> converter.unregisterSubconverter(mxlConverter)
    >>> mxlConverter in c.subconvertersList()
    False
    
    if there is no such subConverter registered and it is not a default subconverter, 
    then a converter.ConverterException is raised:
    
    >>> class ConverterSonix(converter.subConverters.SubConverter):
    ...    registerFormats = ('sonix',)
    ...    registerInputExtensions = ('mus',)
    >>> converter.unregisterSubconverter(ConverterSonix)
    Traceback (most recent call last):
    ConverterException: Could not remove <class 'music21.ConverterSonix'> from registered subconverters
    
    The special command "all" removes everything including the default converters:

    >>> converter.unregisterSubconverter('all')
    >>> c.subconvertersList()
    []

    >>> converter.resetSubconverters() #_DOCS_HIDE

    '''
    global _registeredSubconverters # pylint: disable=global-statement
    global _deregisteredSubconverters # pylint: disable=global-statement
    if removeSubconverter == 'all':
        _registeredSubconverters = []
        _deregisteredSubconverters = ['all']
        return
    
    try:
        _registeredSubconverters.remove(removeSubconverter)
    except ValueError:
        c = Converter()
        dsc = c.defaultSubconverters()
        if removeSubconverter in dsc:
            _deregisteredSubconverters.append(removeSubconverter)
        else:       
            raise ConverterException("Could not remove %r from registered subconverters" % removeSubconverter)




#-------------------------------------------------------------------------------


class Converter(object):
    '''
    A class used for converting all supported data formats into music21 objects.

    Not a subclass, but a wrapper for different converter objects based on format.
    '''
    _DOC_ATTR = {'subConverter': 'a ConverterXXX object that will do the actual converting.',}
    
    def __init__(self):
        self.subConverter = None
        self._thawedStream = None # a stream object unthawed


    def _getDownloadFp(self, directory, ext, url):
        if directory == None:
            raise ValueError
        return os.path.join(directory, 'm21-' + _version.__version__ + '-' + common.getMd5(url) + ext)

    def parseFileNoPickle(self, fp, number=None, format=None, forceSource=False, **keywords): # @ReservedAssignment
        '''
        Given a file path, parse and store a music21 Stream.

        If format is None then look up the format from the file
        extension using `common.findFormatFile`.
        
        Does not use or store pickles in any circumstance.
        '''
        #environLocal.printDebug(['attempting to parseFile', fp])
        if not os.path.exists(fp):
            raise ConverterFileException('no such file exists: %s' % fp)
        useFormat = format

        if useFormat is None:
            useFormat = self.getFormatFromFileExtension(fp)

        self.setSubconverterFromFormat(useFormat)
        self.subConverter.keywords = keywords
        self.subConverter.parseFile(fp, number=number)
        self.stream.filePath = fp
        self.stream.fileNumber = number
        self.stream.fileFormat = useFormat
    
    def getFormatFromFileExtension(self, fp):
        '''
        gets the format from a file extension.
        
        >>> import os
        >>> fp = os.path.join(common.getSourceFilePath(), 'musedata', 'testZip.zip')
        >>> c = converter.Converter()
        >>> c.getFormatFromFileExtension(fp)
        'musedata'
        '''
        # if the file path is to a directory, assume it is a collection of
        # musedata parts
        useFormat = None
        if os.path.isdir(fp):
            useFormat = 'musedata'
        else:
            useFormat = common.findFormatFile(fp)
            if useFormat is None:
                raise ConverterFileException('cannot find a format extensions for: %s' % fp)
        return useFormat
    
    def parseFile(self, fp, number=None, format=None, forceSource=False, storePickle=True, **keywords): # @ReservedAssignment
        '''
        Given a file path, parse and store a music21 Stream.

        If format is None then look up the format from the file
        extension using `common.findFormatFile`.
        
        Will load from a pickle unless forceSource is True
        Will store as a pickle unless storePickle is False
        '''
        from music21 import freezeThaw
        if not os.path.exists(fp):
            raise ConverterFileException('no such file exists: %s' % fp)
        useFormat = format

        if useFormat is None:
            useFormat = self.getFormatFromFileExtension(fp)
        pfObj = PickleFilter(fp, forceSource, number)
        unused_fpDst, writePickle, fpPickle = pfObj.status()
        if writePickle is False and fpPickle is not None and forceSource is False:
            environLocal.printDebug("Loading Pickled version")
            try:
                self._thawedStream = thaw(fpPickle, zipType='zlib')
            except freezeThaw.FreezeThawException:
                environLocal.warn("Could not parse pickle, %s ...rewriting" % fpPickle)
                os.remove(fpPickle)
                self.parseFileNoPickle(fp, number, format, forceSource)

            self.stream.filePath = fp
            self.stream.fileNumber = number
            self.stream.fileFormat = useFormat
        else:
            environLocal.printDebug("Loading original version")
            self.parseFileNoPickle(fp, number, format, forceSource)
            if writePickle is True and fpPickle is not None and storePickle is True:
                # save the stream to disk...
                environLocal.printDebug("Freezing Pickle")
                s = self.stream
                sf = freezeThaw.StreamFreezer(s, fastButUnsafe=True)
                sf.write(fp=fpPickle, zipType='zlib')
                
                environLocal.printDebug("Replacing self.stream")
                # get a new stream
                self._thawedStream = thaw(fpPickle, zipType='zlib')
                self.stream.filePath = fp
                self.stream.fileNumber = number
                self.stream.fileFormat = useFormat

            

    def parseData(self, dataStr, number=None, format=None, forceSource=False, **keywords): # @ReservedAssignment
        '''
        Given raw data, determine format and parse into a music21 Stream.
        '''
        useFormat = format
        # get from data in string if not specified
        if useFormat is None: # its a string
            dataStr = dataStr.lstrip()
            useFormat, dataStr = self.formatFromHeader(dataStr)

            if six.PY3 and isinstance(dataStr, bytes):
                dataStrMakeStr = dataStr.decode('utf-8','ignore')
            else:
                dataStrMakeStr = dataStr

            if useFormat is not None:
                pass
            elif dataStrMakeStr.startswith('<?xml'):
                # is it MEI or MusicXML?
                if '<mei' in dataStrMakeStr:
                    useFormat = 'mei'
                else:
                    useFormat = 'musicxml'
            elif dataStrMakeStr.startswith('mei:') or dataStrMakeStr.lower().startswith('mei:'):
                useFormat = 'mei'
            elif dataStrMakeStr.startswith('musicxml:') or dataStrMakeStr.lower().startswith('musicxml:'):
                useFormat = 'musicxml'
            elif dataStrMakeStr.startswith('MThd') or dataStrMakeStr.lower().startswith('midi:'):
                useFormat = 'midi'
            elif dataStrMakeStr.startswith('!!!') or dataStrMakeStr.startswith('**') or dataStrMakeStr.lower().startswith('humdrum:'):
                useFormat = 'humdrum'
            elif dataStrMakeStr.lower().startswith('tinynotation:'):
                useFormat = 'tinyNotation'

            # assume MuseData must define a meter and a key
            elif 'WK#:' in dataStrMakeStr and 'measure' in dataStrMakeStr:
                useFormat = 'musedata'
            elif 'M:' in dataStrMakeStr and 'K:' in dataStrMakeStr:
                useFormat = 'abc'
            elif 'Time Signature:' in dataStrMakeStr and 'm1' in dataStrMakeStr:
                useFormat = 'romanText'
            else:
                raise ConverterException('File not found or no such format found for: %s' % dataStrMakeStr)

        self.setSubconverterFromFormat(useFormat)
        self.subConverter.keywords = keywords
        self.subConverter.parseData(dataStr, number=number)


    def parseURL(self, url, format=None, number=None, **keywords): # @ReservedAssignment
        '''Given a url, download and parse the file
        into a music21 Stream stored in the `stream`
        property of the converter object.

        Note that this checks the user Environment
        `autoDownlaad` setting before downloading.

        >>> #_DOCS_SHOW jeanieLightBrownURL = 'https://github.com/cuthbertLab/music21/raw/master/music21/corpus/leadSheet/fosterBrownHair.mxl'
        >>> c = converter.Converter()
        >>> #_DOCS_SHOW c.parseURL(jeanieLightBrownURL)
        >>> #_DOCS_SHOW jeanieStream = c.stream
        '''
        autoDownload = environLocal['autoDownload']
        if autoDownload in ('deny', 'ask'):
            message = 'Automatic downloading of URLs is presently set to {!r};'
            message += ' configure your Environment "autoDownload" setting to '
            message += '"allow" to permit automatic downloading: '
            message += "environment.set('autoDownload', 'allow')"
            message = message.format(autoDownload)
            raise ConverterException(message)

        # this format check is here first to see if we can find the format
        # in the url; if forcing a format we do not need this
        # we do need the file extension to construct file path below
        if format is None:
            formatFromURL, ext = common.findFormatExtURL(url)
            if formatFromURL is None: # cannot figure out what it is
                raise ConverterException('cannot determine file format of url: %s' % url)
        else:
            unused_formatType, ext = common.findFormat(format)
            if ext is None:
                ext = '.txt'

        directory = environLocal.getRootTempDir()
        dst = self._getDownloadFp(directory, ext, url)
        if (hasattr(urllib, 'urlretrieve')): 
            # python 2
            urlretrieve = urllib.urlretrieve
        else: #python3
            urlretrieve = urllib.request.urlretrieve # @UndefinedVariable
        
        if not os.path.exists(dst):
            try:
                environLocal.printDebug(['downloading to:', dst])
                fp, unused_headers = urlretrieve(url, filename=dst)
            except IOError:
                raise ConverterException('cannot access file: %s' % url)
        else:
            environLocal.printDebug(['using already downloaded file:', dst])
            fp = dst

        # update format based on downloaded fp
        if format is None: # if not provided as an argument
            useFormat = common.findFormatFile(fp)
        else:
            useFormat = format
        self.setSubconverterFromFormat(useFormat)
        self.subConverter.keywords = keywords
        self.subConverter.parseFile(fp, number=number)
        self.stream.filePath = fp
        self.stream.fileNumber = number
        self.stream.fileFormat = useFormat

    #------------------------------------------------------------------------#
    # Subconverters
    def subconvertersList(self, converterType='any'):
        '''
        Gives a list of all the subconverters that are registered.
        
        If converterType is 'any' (true), then input or output
        subconverters are listed.
        
        Otherwise, 'input', or 'output' can be used to filter.
        
        >>> converter.resetSubconverters() #_DOCS_HIDE
        >>> c = converter.Converter()
        >>> scl = c.subconvertersList()
        >>> defaultScl = c.defaultSubconverters()
        >>> tuple(scl) == tuple(defaultScl)
        True
        
        >>> sclInput = c.subconvertersList('input')
        >>> sclInput
        [<class 'music21.converter.subConverters.ConverterABC'>, 
         <class 'music21.converter.subConverters.ConverterCapella'>, 
         <class 'music21.converter.subConverters.ConverterClercqTemperley'>, 
         <class 'music21.converter.subConverters.ConverterHumdrum'>, 
         <class 'music21.converter.subConverters.ConverterMEI'>, 
         <class 'music21.converter.subConverters.ConverterMidi'>, 
         <class 'music21.converter.subConverters.ConverterMuseData'>, 
         <class 'music21.converter.subConverters.ConverterMusicXML'>, 
         <class 'music21.converter.subConverters.ConverterMusicXMLET'>, 
         <class 'music21.converter.subConverters.ConverterNoteworthy'>, 
         <class 'music21.converter.subConverters.ConverterNoteworthyBinary'>, 
         <class 'music21.converter.subConverters.ConverterRomanText'>, 
         <class 'music21.converter.subConverters.ConverterScala'>, 
         <class 'music21.converter.subConverters.ConverterTinyNotation'>]

        >>> sclOutput = c.subconvertersList('output')
        >>> sclOutput
        [<class 'music21.converter.subConverters.ConverterBraille'>, 
         <class 'music21.converter.subConverters.ConverterLilypond'>, 
         <class 'music21.converter.subConverters.ConverterMidi'>, 
         <class 'music21.converter.subConverters.ConverterMusicXML'>, 
         <class 'music21.converter.subConverters.ConverterMusicXMLET'>, 
         <class 'music21.converter.subConverters.ConverterScala'>, 
         <class 'music21.converter.subConverters.ConverterText'>, 
         <class 'music21.converter.subConverters.ConverterTextLine'>, 
         <class 'music21.converter.subConverters.ConverterVexflow'>]

        
        
        >>> class ConverterSonix(converter.subConverters.SubConverter):
        ...    registerFormats = ('sonix',)
        ...    registerInputExtensions = ('mus',)
        >>> converter.registerSubconverter(ConverterSonix)
        >>> ConverterSonix in c.subconvertersList()
        True

        >>> converter.resetSubconverters() #_DOCS_HIDE
        '''
        subConverterList = []
        for reg in _registeredSubconverters:
            #print reg
            subConverterList.append(reg)

        if _deregisteredSubconverters and _deregisteredSubconverters[0] == 'all':
            pass
        else:
            subConverterList.extend(self.defaultSubconverters())
            for unreg in _deregisteredSubconverters:
                try:
                    subConverterList.remove(unreg)
                except ValueError:
                    pass
        
        if converterType == 'any':
            return subConverterList
        
        filteredSubConvertersList = []
        for sc in subConverterList:
            if converterType == 'input' and len(sc.registerInputExtensions) == 0:
                continue
            if converterType == 'output' and len(sc.registerOutputExtensions) == 0:
                continue
            filteredSubConvertersList.append(sc)
                     
        return filteredSubConvertersList

    def defaultSubconverters(self):
        '''
        return an alphabetical list of the default subconverters: those in converter.subConverters
        with the class Subconverter.
        
        Do not use generally.  use c.subConvertersList()
        
        >>> c = converter.Converter()
        >>> for sc in c.defaultSubconverters():
        ...     print(sc)
        <class 'music21.converter.subConverters.ConverterABC'>
        <class 'music21.converter.subConverters.ConverterBraille'>
        <class 'music21.converter.subConverters.ConverterCapella'>
        <class 'music21.converter.subConverters.ConverterClercqTemperley'>
        <class 'music21.converter.subConverters.ConverterHumdrum'>
        <class 'music21.converter.subConverters.ConverterIPython'>
        <class 'music21.converter.subConverters.ConverterLilypond'>
        <class 'music21.converter.subConverters.ConverterMEI'>
        <class 'music21.converter.subConverters.ConverterMidi'>
        <class 'music21.converter.subConverters.ConverterMuseData'>
        <class 'music21.converter.subConverters.ConverterMusicXML'>
        <class 'music21.converter.subConverters.ConverterMusicXMLET'>
        <class 'music21.converter.subConverters.ConverterNoteworthy'>
        <class 'music21.converter.subConverters.ConverterNoteworthyBinary'>
        <class 'music21.converter.subConverters.ConverterRomanText'>
        <class 'music21.converter.subConverters.ConverterScala'>
        <class 'music21.converter.subConverters.ConverterText'>
        <class 'music21.converter.subConverters.ConverterTextLine'>
        <class 'music21.converter.subConverters.ConverterTinyNotation'>
        <class 'music21.converter.subConverters.ConverterVexflow'>
        <class 'music21.converter.subConverters.SubConverter'>
        '''
        defaultSubconverters = []
        for i in sorted(list(subConverters.__dict__.keys())):
            name = getattr(subConverters, i)
            if callable(name) and not isinstance(name, types.FunctionType) and subConverters.SubConverter in name.__mro__:
                defaultSubconverters.append(name)
        return defaultSubconverters

    def getSubConverterFormats(self):
        '''
        Get a dictionary of subConverters for various formats.
        
        >>> scf = converter.Converter().getSubConverterFormats()
        >>> scf['abc']
        <class 'music21.converter.subConverters.ConverterABC'>
        >>> for x in sorted(list(scf.keys())):
        ...     x, scf[x]
        ('abc', <class 'music21.converter.subConverters.ConverterABC'>)
        ('braille', <class 'music21.converter.subConverters.ConverterBraille'>)
        ('capella', <class 'music21.converter.subConverters.ConverterCapella'>)
        ('cttxt', <class 'music21.converter.subConverters.ConverterClercqTemperley'>)
        ('har', <class 'music21.converter.subConverters.ConverterClercqTemperley'>)
        ('humdrum', <class 'music21.converter.subConverters.ConverterHumdrum'>)
        ('ipython', <class 'music21.converter.subConverters.ConverterIPython'>)
        ('lily', <class 'music21.converter.subConverters.ConverterLilypond'>)
        ('lilypond', <class 'music21.converter.subConverters.ConverterLilypond'>)
        ('mei', <class 'music21.converter.subConverters.ConverterMEI'>)
        ('midi', <class 'music21.converter.subConverters.ConverterMidi'>)
        ('musedata', <class 'music21.converter.subConverters.ConverterMuseData'>)
        ('musicxml', <class 'music21.converter.subConverters.ConverterMusicXMLET'>)
        ('noteworthy', <class 'music21.converter.subConverters.ConverterNoteworthyBinary'>)
        ('noteworthytext', <class 'music21.converter.subConverters.ConverterNoteworthy'>)
        ('oldmusicxml', <class 'music21.converter.subConverters.ConverterMusicXML'>)
        ('oldxml', <class 'music21.converter.subConverters.ConverterMusicXML'>)
        ('rntext', <class 'music21.converter.subConverters.ConverterRomanText'>)
        ('romantext', <class 'music21.converter.subConverters.ConverterRomanText'>)
        ('scala', <class 'music21.converter.subConverters.ConverterScala'>)
        ('t', <class 'music21.converter.subConverters.ConverterText'>)
        ('text', <class 'music21.converter.subConverters.ConverterText'>)
        ('textline', <class 'music21.converter.subConverters.ConverterTextLine'>)
        ('tinynotation', <class 'music21.converter.subConverters.ConverterTinyNotation'>)
        ('txt', <class 'music21.converter.subConverters.ConverterText'>)
        ('vexflow', <class 'music21.converter.subConverters.ConverterVexflow'>)
        ('xml', <class 'music21.converter.subConverters.ConverterMusicXMLET'>)       
        '''
        converterFormats = {}
        for name in self.subconvertersList():
            if hasattr(name, 'registerFormats'):
                formatsTuple = name.registerFormats
                for f in formatsTuple:
                    converterFormats[f.lower()] = name
        return converterFormats

    def setSubconverterFromFormat(self, converterFormat): 
        '''
        sets the .subConverter according to the format of `converterFormat`:
        
        >>> convObj = converter.Converter()       
        >>> convObj.setSubconverterFromFormat('humdrum')
        >>> convObj.subConverter
        <music21.converter.subConverters.ConverterHumdrum object at 0x...>
        '''
        if converterFormat is None:
            raise ConverterException('Did not find a format from the source file')
        converterFormat = converterFormat.lower()
        scf = self.getSubConverterFormats()
        if converterFormat not in scf: 
            raise ConverterException('no converter available for format: %s' % converterFormat)
        subConverterClass = scf[converterFormat]
        self.subConverter = subConverterClass()


    def formatFromHeader(self, dataStr):
        '''
        if dataStr begins with a text header such as  "tinyNotation:" then
        return that format plus the dataStr with the head removed.

        Else, return (None, dataStr) where dataStr is the original untouched.

        Not case sensitive.

        >>> c = converter.Converter()
        >>> c.formatFromHeader('tinynotation: C4 E2')
        ('tinynotation', 'C4 E2')

        >>> c.formatFromHeader('C4 E2')
        (None, 'C4 E2')

        >>> c.formatFromHeader('romanText: m1: a: I b2 V')
        ('romantext', 'm1: a: I b2 V')

        New formats can register new headers:

        >>> class ConverterSonix(converter.subConverters.SubConverter):
        ...    registerFormats = ('sonix',)
        ...    registerInputExtensions = ('mus',)
        >>> converter.registerSubconverter(ConverterSonix)
        >>> c.formatFromHeader('sonix: AIFF data')
        ('sonix', 'AIFF data')
        >>> converter.resetSubconverters() #_DOCS_HIDE    
        '''
        dataStrStartLower = dataStr[:20].lower()
        if six.PY3 and isinstance(dataStrStartLower, bytes):
            dataStrStartLower = dataStrStartLower.decode('utf-8','ignore')

        foundFormat = None
        sclist = self.subconvertersList()
        for sc in sclist:
            for possibleFormat in sc.registerFormats:
                if dataStrStartLower.startswith(possibleFormat.lower() + ':'):
                    foundFormat = possibleFormat
                    dataStr = dataStr[len(foundFormat) + 1:]
                    dataStr = dataStr.lstrip()
                    break
        return (foundFormat, dataStr)

    def regularizeFormat(self, fmt):
        '''
        Take in a string representing a format, a file extension (w/ or without leading dot)
        etc. and find the format string that best represents the format that should be used.
        
        Searches SubConverter.registerFormats first, then SubConverter.registerInputExtensions,
        then SubConverter.registerOutputExtensions
        
        Returns None if no format applies:
        
        >>> c = converter.Converter()
        >>> c.regularizeFormat('mxl')
        'musicxml'
        >>> c.regularizeFormat('t')
        'text'
        >>> c.regularizeFormat('abc')
        'abc'
        >>> c.regularizeFormat('lily.png')
        'lilypond'
        >>> c.regularizeFormat('blah') is None
        True              
        
        '''
        # make lower case, as some lilypond processing used upper case
        fmt = fmt.lower().strip()
        if fmt.startswith('.'):
            fmt = fmt[1:] # strip .
        foundSc = None
        
        formatList = fmt.split('.')
        fmt = formatList[0]
        if len(formatList) > 1:
            unused_subformats = formatList[1:]
        else:
            unused_subformats = []
        scl = self.subconvertersList()
        
        for sc in scl:
            formats = sc.registerFormats        
            for scFormat in formats:
                if fmt == scFormat:
                    foundSc = sc
                    break
            if foundSc is not None:
                break

        if foundSc is None:
            for sc in scl:
                extensions = sc.registerInputExtensions
                for ext in extensions:
                    if fmt == ext:
                        foundSc = sc
                        break
                if foundSc is not None:
                    break
        if foundSc is None:
            for sc in scl:
                extensions = sc.registerInputExtensions
                for ext in extensions:
                    if fmt == ext:
                        foundSc = sc
                        break
                if foundSc is not None:
                    break

        if sc.registerFormats:
            return sc.registerFormats[0]
        else:
            return None


    #---------------------------------------------------------------------------
    # properties

    def _getStream(self):
        '''
        Returns the .subConverter.stream object.
        '''
        if self._thawedStream is not None:
            return self._thawedStream
        elif self.subConverter is not None:
            return self.subConverter.stream
        else:
            return None
        # not _stream: please don't look in other objects' private variables;
        #              humdrum worked differently.

    stream = property(_getStream)




#-------------------------------------------------------------------------------
# module level convenience methods


def parseFile(fp, number=None, format=None, forceSource=False, **keywords):  #@ReservedAssignment
    '''
    Given a file path, attempt to parse the file into a Stream.
    '''
    v = Converter()
    v.parseFile(fp, number=number, format=format, forceSource=forceSource, **keywords)
    return v.stream

def parseData(dataStr, number=None, format=None, **keywords): # @ReservedAssignment
    '''
    Given musical data represented within a Python string, attempt to parse the
    data into a Stream.
    '''
    v = Converter()
    v.parseData(dataStr, number=number, format=format, **keywords)
    return v.stream

def parseURL(url, number=None, format=None, forceSource=False, **keywords): # @ReservedAssignment
    '''
    Given a URL, attempt to download and parse the file into a Stream. Note:
    URL downloading will not happen automatically unless the user has set their
    Environment "autoDownload" preference to "allow".
    '''
    v = Converter()
    v.parseURL(url, format=format, **keywords)
    return v.stream

def parse(value, *args, **keywords):
    r'''
    Given a file path, encoded data in a Python string, or a URL, attempt to
    parse the item into a Stream.  Note: URL downloading will not happen
    automatically unless the user has set their Environment "autoDownload"
    preference to "allow".

    Keywords can include `number` which specifies a piece number in a file of
    multipiece file.

    `format` specifies the format to parse the line of text or the file as.

    A string of text is first checked to see if it is a filename that exists on
    disk.  If not it is searched to see if it looks like a URL.  If not it is
    processed as data.

    PC File:
    
    >>> #_DOCS_SHOW s = converter.parse(r'c:\users\myke\desktop\myfile.xml') 
    
    Mac File:
    
    >>> #_DOCS_SHOW s = converter.parse('/Users/cuthbert/Desktop/myfile.xml') 

    URL:
    
    >>> #_DOCS_SHOW s = converter.parse('http://midirepository.org/file220/file.mid') 


    Data is preceded by an identifier such as "tinynotation:"

    >>> s = converter.parse("tinyNotation: 3/4 E4 r f# g=lastG trip{b-8 a g} c", makeNotation=False)
    >>> s.getElementsByClass(meter.TimeSignature)[0]
    <music21.meter.TimeSignature 3/4>

    or the format can be passed directly:

    >>> s = converter.parse("2/16 E4 r f# g=lastG trip{b-8 a g} c", format='tinyNotation').flat
    >>> s.getElementsByClass(meter.TimeSignature)[0]
    <music21.meter.TimeSignature 2/16>
    '''

    #environLocal.printDebug(['attempting to parse()', value])
    if 'forceSource' in keywords:
        forceSource = keywords['forceSource']
        del(keywords['forceSource'])
    else:
        forceSource = False

    # see if a work number is defined; for multi-work collections
    if 'number' in keywords:
        number = keywords['number']
        del(keywords['number'])
    else:
        number = None

    if 'format' in keywords:
        m21Format = keywords['format']
        del(keywords['format'])
    else:
        m21Format = None

    if six.PY3 and isinstance(value, bytes):
        valueStr = value.decode('utf-8', 'ignore')
    else:
        valueStr = value

    if (common.isListLike(value) and len(value) == 2 and
        value[1] == None and os.path.exists(value[0])):
        # comes from corpus.search
        return parseFile(value[0], format=m21Format, **keywords)
    elif (common.isListLike(value) and len(value) == 2 and
        isinstance(value[1], int) and os.path.exists(value[0])):
        # corpus or other file with movement number
        return parseFile(value[0], format=m21Format, **keywords).getScoreByNumber(value[1])
    elif common.isListLike(value) or args: # tiny notation list # TODO: Remove.
        if args: # add additional args to a list
            value = [value] + list(args)
        return parseData(value, number=number, **keywords)
    # a midi string, must come before os.path.exists test
    elif valueStr.startswith('MThd'):
        return parseData(value, number=number, format=m21Format, **keywords)
    elif os.path.exists(value):
        return parseFile(value, number=number, format=m21Format, forceSource=forceSource, **keywords)
    elif (valueStr.startswith('http://') or valueStr.startswith('https://')):
        # its a url; may need to broaden these criteria
        return parseURL(value, number=number, format=m21Format, forceSource=forceSource, **keywords)
    else:
        return parseData(value, number=number, format=m21Format, **keywords)



def freeze(streamObj, fmt=None, fp=None, fastButUnsafe=False, zipType='zlib'):
    '''Given a StreamObject and a file path, serialize and store the Stream to a file.

    This function is based on the :class:`~music21.converter.StreamFreezer` object.

    The serialization format is defined by the `fmt` argument; 'pickle' (the default) is only one
    presently supported.  'json' or 'jsonnative' will be used once jsonpickle is good enough.

    If no file path is given, a temporary file is used.

    The file path is returned.


    >>> c = converter.parse('tinynotation: 4/4 c4 d e f')
    >>> c.show('text')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note D>
        {2.0} <music21.note.Note E>
        {3.0} <music21.note.Note F>
        {4.0} <music21.bar.Barline style=final>
    >>> fp = converter.freeze(c, fmt='pickle')
    >>> #_DOCS_SHOW fp
    '/tmp/music21/sjiwoe.pgz'

    The file can then be "thawed" back into a Stream using the :func:`~music21.converter.thaw` method.

    >>> d = converter.thaw(fp)
    >>> d.show('text')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note D>
        {2.0} <music21.note.Note E>
        {3.0} <music21.note.Note F>
        {4.0} <music21.bar.Barline style=final>
    '''
    from music21 import freezeThaw
    v = freezeThaw.StreamFreezer(streamObj, fastButUnsafe=fastButUnsafe)
    return v.write(fmt=fmt, fp=fp, zipType=zipType) # returns fp


def thaw(fp, zipType='zlib'):
    '''Given a file path of a serialized Stream, defrost the file into a Stream.

    This function is based on the :class:`~music21.converter.StreamFreezer` object.

    See the documentation for :meth:`~music21.converter.freeze` for demos.
    '''
    from music21 import freezeThaw
    v = freezeThaw.StreamThawer()
    v.open(fp, zipType=zipType)
    return v.stream


def freezeStr(streamObj, fmt=None):
    '''
    Given a StreamObject
    serialize and return a serialization string.

    This function is based on the
    :class:`~music21.converter.StreamFreezer` object.

    The serialization format is defined by
    the `fmt` argument; 'pickle' (the default),
    is the only one presently supported.


    >>> c = converter.parse('tinyNotation: 4/4 c4 d e f', makeNotation=False)
    >>> c.show('text')
    {0.0} <music21.meter.TimeSignature 4/4>
    {0.0} <music21.note.Note C>
    {1.0} <music21.note.Note D>
    {2.0} <music21.note.Note E>
    {3.0} <music21.note.Note F>
    >>> data = converter.freezeStr(c, fmt='pickle')
    >>> len(data) > 20 # pickle implementation dependent
    True
    >>> d = converter.thawStr(data)
    >>> d.show('text')
    {0.0} <music21.meter.TimeSignature 4/4>
    {0.0} <music21.note.Note C>
    {1.0} <music21.note.Note D>
    {2.0} <music21.note.Note E>
    {3.0} <music21.note.Note F>

    '''
    from music21 import freezeThaw
    v = freezeThaw.StreamFreezer(streamObj)
    return v.writeStr(fmt=fmt) # returns a string

def thawStr(strData):
    '''
    Given a serialization string, defrost into a Stream.

    This function is based on the :class:`~music21.converter.StreamFreezer` object.
    '''
    from music21 import freezeThaw
    v = freezeThaw.StreamThawer()
    v.openStr(strData)
    return v.stream




#-------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):
    # interpreter loading

    def runTest(self):
        pass

    def testMusicXMLConversion(self):
        from music21.musicxml import testFiles
        for mxString in testFiles.ALL: # @UndefinedVariable
            a = subConverters.ConverterMusicXML()
            a.parseData(mxString)

    def testMusicXMLTabConversion(self):
        from music21.musicxml import testFiles
        
        mxString = testFiles.ALL[5] # @UndefinedVariable
        a = subConverters.ConverterMusicXML()
        a.parseData(mxString)

        b = parseData(mxString)
        b.show('text')

        #{0.0} <music21.metadata.Metadata object at 0x04501CD0>
        #{0.0} <music21.stream.Part Electric Guitar>
        #    {0.0} <music21.instrument.Instrument P0: Electric Guitar: >
        #    {0.0} <music21.stream.Measure 0 offset=0.0>
        #        {0.0} <music21.layout.StaffLayout distance None, staffNumber None, staffSize None, staffLines 6>
        #        {0.0} <music21.clef.TabClef>
        #        {0.0} <music21.tempo.MetronomeMark animato Quarter=120.0>
        #        {0.0} <music21.key.KeySignature of no sharps or flats, mode major>
        #        {0.0} <music21.meter.TimeSignature 4/4>
        #        {0.0} <music21.note.Note F>
        #        {2.0} <music21.note.Note F#>
        
        b.show()
        pass        


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
        urlB = 'http://kern.ccarh.org/cgi-bin/ksdata?l=users/craig/classical/schubert/piano/d0576&file=d0576-06.krn&f=kern'
        urlC = 'http://kern.ccarh.org/cgi-bin/ksdata?l=users/craig/classical/bach/cello&file=bwv1007-01.krn&f=xml'
        for url in [urlB, urlC]:
            try:
                unused_post = parseURL(url)
            except:
                print(url)
                raise

    def testFreezer(self):
        from music21 import corpus
        s = corpus.parse('bach/bwv66.6.xml')
        fp = freeze(s)
        s2 = thaw(fp)
        s2.show()


class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        import sys
        for part in sys.modules[self.__module__].__dict__:
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            obj = getattr(sys.modules[self.__module__], part)
            if callable(obj) and not isinstance(obj, types.FunctionType):
                i = copy.copy(obj)
                j = copy.deepcopy(obj)


    def testConversionMX(self):
        from music21.musicxml import testPrimitive
        from music21 import dynamics
        from music21 import note


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
        # there should be 27 dynamics found in this file
        self.assertEqual(len(b), 27)
        c = a.getElementsByClass(note.Note)
        self.assertEqual(len(c), 53)

        # two starts and two stops == 2!
        d = a.getElementsByClass(dynamics.DynamicWedge)
        self.assertEqual(len(d), 2)


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
        from music21 import chord
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
        part = a.parts[0]
        notes = part.flat.notesAndRests
        beams = []
        for n in notes:
            if "Note" in n.classes:
                beams += n.beams.beamsList
        self.assertEqual(len(beams), 152)


    def testConversionMXTime(self):

        from music21.musicxml import testPrimitive

        mxString = testPrimitive.timeSignatures11c
        a = parse(mxString)
        unused_part = a.parts[0]


        mxString = testPrimitive.timeSignatures11d
        a = parse(mxString)
        part = a.parts[0]

        notes = part.flat.notesAndRests
        self.assertEqual(len(notes), 11)


    def testConversionMXClefPrimitive(self):
        from music21 import clef
        from music21.musicxml import testPrimitive
        mxString = testPrimitive.clefs12a
        a = parse(mxString)
        part = a.parts[0]

        clefs = part.flat.getElementsByClass(clef.Clef)
        self.assertEqual(len(clefs), 18)


    def testConversionMXClefTimeCorpus(self):

        from music21 import corpus, clef, meter
        a = corpus.parse('luca')

        # there should be only one clef in each part
        clefs = a.parts[0].flat.getElementsByClass(clef.Clef)
        self.assertEqual(len(clefs), 1)
        self.assertEqual(clefs[0].sign, 'G')

        # second part
        clefs = a.parts[1].flat.getElementsByClass(clef.Clef)
        self.assertEqual(len(clefs), 1)
        self.assertEqual(clefs[0].octaveChange, -1)
        self.assertEqual(type(clefs[0]).__name__, 'Treble8vbClef')

        # third part
        clefs = a.parts[2].flat.getElementsByClass(clef.Clef)
        self.assertEqual(len(clefs), 1)

        # check time signature count
        ts = a.parts[1].flat.getElementsByClass(meter.TimeSignature)
        self.assertEqual(len(ts), 4)


    def testConversionMXArticulations(self):
        from music21 import note
        from music21.musicxml import testPrimitive

        mxString = testPrimitive.articulations01
        a = parse(mxString)
        part = a.parts[0]

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
        #a.show()

    def testConversionMXKey(self):
        from music21 import key
        from music21.musicxml import testPrimitive
        mxString = testPrimitive.keySignatures13a
        a = parse(mxString)
        part = a.parts[0]

        keyList = part.flat.getElementsByClass(key.KeySignature)
        self.assertEqual(len(keyList), 46)


    def testConversionMXMetadata(self):
        from music21.musicxml import testFiles

        a = parse(testFiles.mozartTrioK581Excerpt) # @UndefinedVariable
        self.assertEqual(a.metadata.composer, 'Wolfgang Amadeus Mozart')
        self.assertEqual(a.metadata.title, 'Quintet for Clarinet and Strings')
        self.assertEqual(a.metadata.movementName, 'Menuetto (Excerpt from Second Trio)')

        a = parse(testFiles.binchoisMagnificat) # @UndefinedVariable
        self.assertEqual(a.metadata.composer, 'Gilles Binchois')
        # this gets the best title available, even though this is movement title
        self.assertEqual(a.metadata.title, 'Excerpt from Magnificat secundi toni')


    def testConversionMXBarlines(self):
        from music21 import bar
        from music21.musicxml import testPrimitive
        a = parse(testPrimitive.barlines46a)
        part = a.parts[0]
        barlineList = part.flat.getElementsByClass(bar.Barline)
        self.assertEqual(len(barlineList), 11)

    def testConversionXMLayout(self):

        from music21.musicxml import testPrimitive
        from music21 import layout

        a = parse(testPrimitive.systemLayoutTwoPart)
        #a.show()

        part = a.getElementsByClass(stream.Part)[0]
        systemLayoutList = part.flat.getElementsByClass(layout.SystemLayout)
        measuresWithSL = []
        for e in systemLayoutList:
            measuresWithSL.append(e.measureNumber)
        self.assertEqual(measuresWithSL, [1, 3, 4, 5, 7, 8])
        self.assertEqual(len(systemLayoutList), 6)


    def testConversionMXTies(self):

        from music21.musicxml import testPrimitive
        from music21 import clef

        a = parse(testPrimitive.multiMeasureTies)
        #a.show()

        countTies = 0
        countStartTies = 0
        for p in a.parts:
            post = p.getContextByClass('Clef')
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
        s = corpus.parse('schumann_clara/opus17', 3)
        #s.show()
        is1 = s.parts[0].flat.getElementsByClass('Instrument')
        self.assertEqual(len(is1), 1)
        #self.assertIn('Violin', is1[0].classes)
        is2 = s.parts[1].flat.getElementsByClass('Instrument')
        self.assertEqual(len(is2), 1)
        #self.assertIn('Violoncello', is1[0].classes)
        is3 = s.parts[2].flat.getElementsByClass('Instrument')
        self.assertEqual(len(is3), 1)
        #self.assertIn('Piano', is1[0].classes)


    def testConversionMidiBasic(self):
        directory = common.getPackageDir(relative=False, remapSep=os.sep)
        fp = None
        for fp in directory:
            if fp.endswith('midi'):
                break
        else:
            raise ConverterException('Could not find a directory with MIDI')
        if fp is None:
            raise ConverterException('Could not find a directory with MIDI')
             
        dirLib = os.path.join(fp, 'testPrimitive')
        # a simple file created in athenacl
        fp = os.path.join(dirLib, 'test01.mid')

        unused_s = parseFile(fp)
        unused_s = parse(fp)

        c = subConverters.ConverterMidi()
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
        from music21 import meter, key, chord, note

        fp = os.path.join(common.getSourceFilePath(), 'midi', 'testPrimitive',  'test01.mid')
        # a simple file created in athenacl
        #for fn in ['test01.mid', 'test02.mid', 'test03.mid', 'test04.mid']:
        s = parseFile(fp)
        #s.show()
        self.assertEqual(len(s.flat.getElementsByClass(note.Note)), 18)


        # has chords and notes
        fp = os.path.join(common.getSourceFilePath(), 'midi', 'testPrimitive',  'test05.mid')
        s = parseFile(fp)
        #s.show()
        #environLocal.printDebug(['\nopening fp', fp])

        self.assertEqual(len(s.flat.getElementsByClass(note.Note)), 2)
        self.assertEqual(len(s.flat.getElementsByClass(chord.Chord)), 4)

        self.assertEqual(len(s.flat.getElementsByClass(meter.TimeSignature)), 0)
        self.assertEqual(len(s.flat.getElementsByClass(key.KeySignature)), 0)


        # this sample has eight note triplets
        fp = os.path.join(common.getSourceFilePath(), 'midi', 'testPrimitive',  'test06.mid')
        s = parseFile(fp)
        #s.show()

        #environLocal.printDebug(['\nopening fp', fp])

        #s.show()
        from fractions import Fraction as F
        dList = [n.quarterLength for n in s.flat.notesAndRests[:30]]
        match = [0.5, 0.5, 1.0, 0.5, 0.5, 0.5, 0.5, 1.0, 0.5, 0.5, 
                 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 
                 0.5, 0.5, 0.5, 0.5, F(1,3), F(1,3), F(1,3), 0.5, 0.5, 1.0]
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
        self.assertEqual(measures[0].rightBarline.style, 'final')

        self.assertEqual(measures[1].leftBarline, None)
        self.assertEqual(measures[1].rightBarline.style, 'final')

        mxString = testPrimitive.repeatMultipleTimes45c
        s = parse(mxString)

        self.assertEqual(len(s.flat.getElementsByClass(bar.Barline)), 4)
        part = s.parts[0]
        measures = part.getElementsByClass('Measure')

        #s.show()



    def testConversionABCOpus(self):

        from music21.abcFormat import testFiles
        from music21 import corpus

        s = parse(testFiles.theAleWifesDaughter)
        # get a Stream object, not an opus
        self.assertEqual(isinstance(s, stream.Score), True)
        self.assertEqual(isinstance(s, stream.Opus), False)
        self.assertEqual(len(s.flat.notesAndRests), 66)

        # a small essen collection
        op = corpus.parse('essenFolksong/teste')
        # get a Stream object, not an opus
        #self.assertEqual(isinstance(op, stream.Score), True)
        self.assertEqual(isinstance(op, stream.Opus), True)
        self.assertEqual([len(s.flat.notesAndRests) for s in op], [33, 51, 59, 33, 29, 174, 67, 88])
        #op.show()

        # get one work from the opus
        s = corpus.parse('essenFolksong/teste', number=6)
        self.assertEqual(isinstance(s, stream.Score), True)
        self.assertEqual(isinstance(s, stream.Opus), False)
        self.assertEqual(s.metadata.title, 'Moli hua')

        #s.show()


    def testConversionABCWorkFromOpus(self):
        # test giving a work number at loading
        from music21 import corpus
        s = corpus.parse('essenFolksong/han1', number=6)
        self.assertEqual(isinstance(s, stream.Score), True)
        self.assertEqual(s.metadata.title, 'Yi gan hongqi kongzhong piao')
        # make sure that beams are being made
        self.assertEqual(str(s.parts[0].flat.notesAndRests[4].beams), '<music21.beam.Beams <music21.beam.Beam 1/start>/<music21.beam.Beam 2/start>>')
        #s.show()



    def testConversionMusedata(self):
        fp = os.path.join(common.getSourceFilePath(), 'musedata', 'testPrimitive', 'test01')
        s = parse(fp)
        self.assertEqual(len(s.parts), 5)
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

#         # test from a file that ends in zip
#         # note: this is a stage1 file!
#         fp = os.path.join(common.getSourceFilePath(), 'musedata', 'testZip.zip')
#         af = ArchiveManager(fp)
#         # for now, only support zip
#         self.assertEqual(af.archiveType, 'zip')
#         self.assertEqual(af.isArchive(), True)
#         self.assertEqual(af.getNames(), ['01/', '01/04', '01/02', '01/03', '01/01'] )
# 
#         # returns a list of strings
#         self.assertEqual(af.getData(dataFormat='musedata')[0][:30], '378\n1080  1\nBach Gesells\nchaft')


        #mdw = musedataModule.MuseDataWork()
        # can add a list of strings from getData
        #mdw.addString(af.getData(dataFormat='musedata'))
        #self.assertEqual(len(mdw.files), 4)
#
#         mdpList = mdw.getParts()
#         self.assertEqual(len(mdpList), 4)

        # try to load parse the zip file
        #s = parse(fp)

        # test loading a directory
        fp = os.path.join(common.getSourceFilePath(), 'musedata',
                'testPrimitive', 'test01')
        cmd = subConverters.ConverterMuseData()
        cmd.parseFile(fp)

    def testMEIvsMX(self):
        '''
        Ensure Converter.parseData() distinguishes between a string with MEI data and a string with
        MusicXML data. The "subConverter" module is mocked out because we don't actually need to
        test the conversion process in this unit test.
        '''
        # These strings aren't valid documents, but they are enough to pass the detection we're
        # testing in parseData(). But it does mean we'll be testing in a strange way.
        meiString = '<?xml version="1.0" encoding="UTF-8"?><mei><note/></mei>'
        #mxlString = '<?xml version="1.0" encoding="UTF-8"?><score-partwise><note/></score-partwise>'

        # The "mei" module raises an MeiElementError with "meiString," so as long as that's raised,
        # we know that parseData() chose correctly.
        from music21.mei.base import MeiElementError
        testConv = Converter()
        self.assertRaises(MeiElementError, testConv.parseData, meiString)

        # TODO: another test -- score-partwise is good enough for new converter.
        ## The ConverterMusicXML raises a SubConverterException with "mxlString," so as long as
        ## that's raised, we know that parseData()... well at least that it didn't choose MEI.
        #from music21.converter.subConverters import SubConverterException
        #testConv = Converter()
        #self.assertRaises(SubConverterException, testConv.parseData, mxlString)


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [parse, parseFile, parseData, parseURL, freeze, thaw, freezeStr, thawStr, 
              Converter, registerSubconverter, unregisterSubconverter]


if __name__ == "__main__":
    # sys.arg test options will be used in mainTest()
    import music21
    music21.mainTest(Test)



#------------------------------------------------------------------------------
# eof

