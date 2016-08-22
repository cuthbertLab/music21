# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         corpus/manager.py
# Purpose:      Manage multiple corpora
#
# Authors:      Christopher Ariza
#               Josiah Wolf Oberholtzer
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009, 2013, 2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------
'''
The manager module handles requests across multiple corpora.  It should be the default
interface to searching corpora.

New in v3 -- previously most were static methods on corpus.corpora.Corpus, but that
seemed inappropriate since these work across corpora.
'''
import os

from music21 import common
from music21 import converter
from music21 import environment
from music21 import metadata

from music21.corpus import corpora
from music21.exceptions21 import CorpusException

_metadataBundles = {
    'core': None,
    'local': None,
    'virtual': None,
    }

#------------------------------------------------------------------------------
def fromName(name):
    '''
    Instantiate a specific corpus based on `name`:

    >>> corpus.manager.fromName('core')
    <music21.corpus.corpora.CoreCorpus>

    >>> corpus.manager.fromName('virtual')
    <music21.corpus.corpora.VirtualCorpus>

    >>> corpus.manager.fromName('local')
    <music21.corpus.corpora.LocalCorpus: 'local'>

    >>> corpus.manager.fromName(None)
    <music21.corpus.corpora.LocalCorpus: 'local'>


    Note that this corpus probably does not exist on disk, but it's ready to have
    paths added to it and to be stored on disk.

    >>> corpus.manager.fromName('testDummy')
    <music21.corpus.corpora.LocalCorpus: 'testDummy'>
    '''
    if name == 'core':
        return corpora.CoreCorpus()
    elif name == 'virtual':
        return corpora.VirtualCorpus()
    elif name == 'local':
        return corpora.LocalCorpus()
    else:
        return corpora.LocalCorpus(name=name)

def fromCacheName(name):
    '''
    Instantiate a specific corpus based on its `cacheName`:

    These are the same as `fromName`.

    >>> corpus.manager.fromCacheName('core')
    <music21.corpus.corpora.CoreCorpus>

    >>> corpus.manager.fromCacheName('virtual')
    <music21.corpus.corpora.VirtualCorpus>

    >>> corpus.manager.fromCacheName('local')
    <music21.corpus.corpora.LocalCorpus: 'local'>

    >>> corpus.manager.fromCacheName(None)
    <music21.corpus.corpora.LocalCorpus: 'local'>

    Other local corpora are different and prefaced by "local-":

    >>> corpus.manager.fromCacheName('local-testDummy')
    <music21.corpus.corpora.LocalCorpus: 'testDummy'>

    Raises a corpus exception if
    it is not an allowable cache name.

    >>> corpus.manager.fromCacheName('testDummy')
    Traceback (most recent call last):
    music21.exceptions21.CorpusException: Cannot parse a cacheName of 'testDummy'
    '''
    if name == 'core':
        return corpora.CoreCorpus()
    elif name == 'virtual':
        return corpora.VirtualCorpus()
    elif name == 'local' or name is None:
        return corpora.LocalCorpus()
    elif name.startswith('local-'):
        return corpora.LocalCorpus(name=name[6:])
    else:
        raise CorpusException("Cannot parse a cacheName of '{0}'".format(name))


def iterateCorpora(returnObjects=True):
    '''
    a generator that iterates over the corpora (either as objects or as names)
    for use in pan corpus searching.
    
    This test will only show the first three, because it needs to run the same
    on every system:
    
    >>> for i, corpusObject in enumerate(corpus.manager.iterateCorpora()):
    ...     print(corpusObject)
    ...     if i == 2:
    ...        break
    <music21.corpus.corpora.CoreCorpus>
    <music21.corpus.corpora.VirtualCorpus>
    <music21.corpus.corpora.LocalCorpus: 'local'>    

    We can also get names instead... Note that the name of the main localcorpus is 'local' not
    None

    >>> for i, corpusName in enumerate(corpus.manager.iterateCorpora(returnObjects=False)):
    ...     print(corpusName)
    ...     if i == 2:
    ...        break
    core
    virtual
    local
    
    New in v.3 
    '''
    if returnObjects is True:
        yield corpora.CoreCorpus()
        yield corpora.VirtualCorpus()
        for cn in listLocalCorporaNames():
            yield corpora.LocalCorpus(cn)
    else:
        yield corpora.CoreCorpus().name
        yield corpora.VirtualCorpus().name
        for cn in listLocalCorporaNames():
            if cn is None:
                yield 'local'
            else:
                yield cn

# pylint: disable=redefined-builtin
def getWork(workName,
            movementNumber=None,
            fileExtensions=None,
        ):
    '''
    this parse method is called from `corpus.parse()` and does nothing differently from it.
    
    Searches all corpora for a file that matches the name and returns it parsed.
    '''
    addXMLWarning = False
    workNameJoined = workName
    mxlWorkName = workName
    
    if workName in (None, ''):
        raise CorpusException(
            'a work name must be provided as an argument')
    if not common.isListLike(fileExtensions):
        fileExtensions = [fileExtensions]
    if common.isIterable(workName):
        workNameJoined = os.path.sep.join(workName)

    if workNameJoined.endswith(".xml"):
        # might be compressed MXL file
        mxlWorkName = os.path.splitext(workNameJoined)[0] + ".mxl"
        addXMLWarning = True

    filePaths = None    
    for corpusObject in iterateCorpora():    
        workList = corpusObject.getWorkList(workName, movementNumber, fileExtensions)
        if not workList and addXMLWarning:
            workList = corpusObject.getWorkList(mxlWorkName, movementNumber, fileExtensions)
            if not workList:
                continue
        if len(workList) >= 1:
            filePaths = workList
            break

    if filePaths is None:
        warningMessage = 'Could not find a'
        if addXMLWarning:
            warningMessage += 'n xml or mxl'
        warningMessage += ' work that met this criterion: {0};'.format(workName)
        warningMessage += ' if you are searching for a file on disk, '
        warningMessage += 'use "converter" instead of "corpus".'
        raise CorpusException(warningMessage)
    else:
        if len(filePaths) == 1:
            return filePaths[0]
        else:
            return filePaths

# pylint: disable=redefined-builtin
def parse(workName,
            movementNumber=None,
            number=None,
            fileExtensions=None,
            forceSource=False,
            format=None # @ReservedAssignment
        ):
    filePath = getWork(workName=workName,
                        movementNumber=movementNumber,
                        fileExtensions=fileExtensions,
                       )
    if isinstance(filePath, list):
        filePath = filePath[0]

    streamObject = converter.parse(
        filePath,
        forceSource=forceSource,
        number=number,
        format=format
        )
    _addCorpusFilepathToStreamObject(streamObject, filePath)
    return streamObject

def _addCorpusFilepathToStreamObject(streamObj, filePath):
    # metadata attribute added to store the file path,
    # for use later in identifying the score
    #if streamObj.metadata == None:
    #    streamObj.insert(metadata.Metadata())
    corpusFilePath = common.getCorpusFilePath()
    lenCFP = len(corpusFilePath) + len(os.sep)
    if filePath.startswith(corpusFilePath):
        fp2 = filePath[lenCFP:]
        ### corpus fix for windows
        dirsEtc = fp2.split(os.sep)
        fp3 = '/'.join(dirsEtc)
        streamObj.corpusFilepath = fp3
    else:
        streamObj.corpusFilepath = filePath

def search(
    query,
    field=None,
    corpusNames=None,
    fileExtensions=None,
    ):
    '''
    Search all stored metadata bundles and return a list of file paths.

    The ``names`` parameter can be used to specify which corpora to search,
    for example:

    >>> corpus.manager.search(
    ...     'bach',
    ...     corpusNames=('core', 'virtual'),
    ...     )
    <music21.metadata.bundles.MetadataBundle {151 entries}>

    If ``names`` is None, all corpora known to music21 will be searched.

    This method uses stored metadata and thus, on first usage, will incur a
    performance penalty during metadata loading.
    '''
    readAllMetadataBundlesFromDisk()
    allSearchResults = metadata.bundles.MetadataBundle()
    
    if corpusNames is None:
        corpusNames = list(iterateCorpora(returnObjects=False))
    
    for corpusName in corpusNames:
        c = fromName(corpusName)
        searchResults = c.metadataBundle.search(
                query, field, fileExtensions=fileExtensions)
        allSearchResults = allSearchResults.union(searchResults)
    
    return allSearchResults


def getMetadataBundleByCorpus(corpusObject):
    '''
    Return the metadata bundle for a single Corpus object
    
    >>> vc = corpus.corpora.VirtualCorpus()
    >>> mdb1 = corpus.manager.getMetadataBundleByCorpus(vc)
    >>> mdb1
    <music21.metadata.bundles.MetadataBundle 'virtual': {11 entries}>
    
    This is the same as calling `metadataBundle` on the corpus itself,
    but this is the routine that actually does the work. In other words,
    it's the call on the object that is redundant, not this routine.
    
    >>> mdb1 is vc.metadataBundle
    True
    '''
    cacheMetadataBundleFromDisk(corpusObject)
    cacheName = corpusObject.cacheName
    return _metadataBundles[cacheName]

def cacheMetadataBundleFromDisk(corpusObject):
    r'''
    Update a corpus' metadata bundle from its stored JSON file on disk.
    '''
    corpusCacheName = corpusObject.cacheName
    if (corpusCacheName not in _metadataBundles or
            _metadataBundles[corpusCacheName] is None):
        metadataBundle = metadata.bundles.MetadataBundle(corpusCacheName)
        metadataBundle.read()
        metadataBundle.validate()
        _metadataBundles[corpusCacheName] = metadataBundle


def readAllMetadataBundlesFromDisk():
    '''
    Read each corpus's metadata bundle and store it in memory.
    '''
    for corpusObject in iterateCorpora():
        cacheMetadataBundleFromDisk(corpusObject)

def listLocalCorporaNames():
    '''
    List the names of all user-defined local corpora.

    The entry for None refers to the default local corpus.
    '''
    userSettings = environment.UserSettings()
    result = [None]
    result.extend(userSettings['localCorporaSettings'].keys())
    return result

def listSearchFields():
    r'''
    List all available search field names:

    >>> for field in corpus.manager.listSearchFields():
    ...     field
    ...
    'alternativeTitle'
    'ambitus'
    'composer'
    'date'
    'keySignatureFirst'
    'keySignatures'
    'localeOfComposition'
    'movementName'
    'movementNumber'
    'noteCount'
    'number'
    'opusNumber'
    'pitchHighest'
    'pitchLowest'
    'quarterLength'
    'tempoFirst'
    'tempos'
    'timeSignatureFirst'
    'timeSignatures'
    'title'

    '''
    return tuple(sorted(metadata.RichMetadata.searchAttributes))

#------------------------------------------------------------------------------


if __name__ == "__main__":
    import music21
    music21.mainTest()
