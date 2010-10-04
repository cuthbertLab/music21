#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         corpus/metadataCache/cache.py
# Purpose:      Build the metadata cache
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


from music21 import corpus, metadata

def cacheCore(self): 
    '''The core cache is all locally-stored corpus files. 
    '''

    mdb = metadata.MetadataBundle('core')
    paths = corpus.getPaths()
    mdb.addFromPaths(paths)
    #print mdb._storage
    mdb.write() # will use a default file path





if __name__ == "__main__":
    cacheCore()


