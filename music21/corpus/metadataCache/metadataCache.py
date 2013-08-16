# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         corpus.metadata.metadataCache.py
# Purpose:      Build the metadata cache
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#-------------------------------------------------------------------------------

'''
Run this module to process all files in the corpus. 
Either the 'core', 'local', or 'virtual' corpus.
'''

from music21 import common
from music21 import exceptions21

from music21 import environment
_MOD = "metadataCache.py"
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------


class MetadataCacheException(exceptions21.Music21Exception):
    pass


def cacheMetadata(domains=('local', 'core', 'virtual')): 
    '''
    The core cache is all locally-stored corpus files. 
    '''
    from music21 import corpus, metadata

    if not common.isListLike(domains):
        domains = (domains,)

    timer = common.Timer()
    timer.start()

    # store list of file paths that caused an error
    filePathErrors = []

    # the core cache is based on local files stored in music21
    # virtual is on-line
    for domain in domains:
        # the domain passed here becomes the name of the bundle
        # determines the file name of the json bundle
        metadataBundle = metadata.MetadataBundle(domain)
        if domain == 'virtual':
            getPaths = corpus.getVirtualPaths
        elif domain == 'core':
            getPaths = corpus.getCorePaths
        elif domain == 'local':
            getPaths = corpus.getLocalPaths  
        else:
            raise MetadataCacheException('invalid domain provided: {0}'.format(
                domain))
        paths = getPaths()
        environLocal.warn(
            'metadata cache: starting processing of paths: {0}'.format(
                len(paths)))
        #metadataBundle.addFromPaths(paths[-3:])
        # returns any paths that failed to load
        filePathErrors += metadataBundle.addFromPaths(
            paths, printDebugAfter=0) 
        #print metadataBundle.storage
        metadataBundle.write() # will use a default file path based on domain
        environLocal.warn(
            'cache: writing time: {0} md items: {1}'.format(
                timer, len(metadataBundle.storage)))
        del metadataBundle

    environLocal.warn('cache: final writing time: {0}'.format(timer))
    for filePath in filePathErrors:
        environLocal.warn('path failed to parse: {0}'.format(filePath))


### multiprocessing module


def cacheCoreMetadataMultiprocess(ipythonMod=None, stopAfter=None): 
    '''
    The core cache is all locally-stored corpus files. 
    '''
    from music21 import corpus, metadata

    timer = common.Timer()
    timer.start()

    # store list of file paths that caused an error
    #fpError = []

    metadataBundle = metadata.MetadataBundle('core')

    pathsFull = corpus.getCorePaths()
    pathsShort = []
    lenCorpusPath = len(common.getCorpusFilePath())
    
    for i, path in enumerate(pathsFull):
        pathsShort.append(path[lenCorpusPath:])
        if stopAfter is not None and i >= stopAfter:
            break
    
    environLocal.warn(
        'metadata cache: starting processing of paths: {0}'.format(
            len(pathsShort)))
    
    #metadataBundle.addFromPaths(paths[-3:])
    # returns any paths that failed to load
    for i in range(0, len(pathsShort), 100):
        maxI = min(i+100, len(pathsShort))
        pathsChunk = pathsShort[i:maxI]
        environLocal.warn(
            'Starting multiprocessing with chunk {0}, first is {1}'.format(
                i, pathsChunk[0]))
        allKeys = ipythonMod.map_async(
            cacheCoreMetadataMultiprocessHelper, pathsChunk)
        for key in keys:
            for subkey in key:
                metadataBundle.storage[subkey[0]] = subkey[1]
    
    #print metadataBundle.storage
    metadataBundle.write() # will use a default file path based on domain

    environLocal.warn(
        'cache: writing time: {0} md items: {1}'.format(
            timer, len(metadataBundle.storage)))
    del metadataBundle


def cacheCoreMetadataMultiprocessHelper(filePath=None):
    from music21 import metadata
    metadataBundle = metadata.MetadataBundle('core')
    unused_fpError = metadataBundle.addFromPaths(
        [filePath], printDebugAfter=0, useCorpus=True) 
    result = []
    for key in metadataBundle.storage:
        result.append((key, metadataBundle.storage[key]))
    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        cacheMetadata(sys.argv[1])
    else:
        cacheMetadata()

