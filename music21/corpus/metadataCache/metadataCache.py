#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         corpus/metadataCache/cache.py
# Purpose:      Build the metadata cache
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2010-2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''
Run this module to process all files in the corpus. 
'''

from music21 import common


from music21 import environment
_MOD = "metadataCache.py"
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------
class MetadataCacheException(Exception):
    pass




def cacheMetadata(domainList=['core', 'virtual']): 
    '''The core cache is all locally-stored corpus files. 
    '''
    from music21 import corpus, metadata

    if not common.isListLike(domainList):
        domainList = [domainList]

    t = common.Timer()
    t.start()

    # store list of file paths that caused an error
    fpError = []

    # the core cache is based on local files stored in music21
    # virtual is on-line
    for domain in domainList:
        # the domain passed here becomes the name of the bundle
        # determines the file name of the json bundle
        mdb = metadata.MetadataBundle(domain)

        if domain == 'virtual':
            getPaths = corpus.getVirtualPaths
        elif domain == 'core':
            getPaths = corpus.getCorePaths
        elif domain == 'local':
            getPaths = corpus.getLocalPaths  
        else:
            raise MetadataCacheException('invalid domain provided: %s' % domain)
            
        paths = getPaths()
    
        environLocal.printDebug([
            'metadata cache: starting processing of paths:', len(paths)])
    
        #mdb.addFromPaths(paths[-3:])
        # returns any paths that failed to load
        fpError += mdb.addFromPaths(paths) 
        #print mdb._storage
        mdb.write() # will use a default file path based on domain

        environLocal.printDebug(['cache: writing time:', t, 'md items:', len(mdb._storage)])
        del mdb

    environLocal.printDebug(['cache: final writing time:', t])
    
    for fp in fpError:
        environLocal.warn('path failed to parse: %s' % fp)        


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        cacheMetadata(sys.argv[1])
    else:
        cacheMetadata()







