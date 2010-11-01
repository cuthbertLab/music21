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


from music21 import corpus, metadata, common


from music21 import environment
_MOD = "cahce.py"
environLocal = environment.Environment(_MOD)



def cacheCore(): 
    '''The core cache is all locally-stored corpus files. 
    '''

    t = common.Timer()
    t.start()

    # the core cache is based on local files stored in music21
    # virtual is on-line
    for name, getPaths in [('virtual', corpus.getVirtualPaths), 
                          ('core', corpus.getPaths), 
                      ]:

        mdb = metadata.MetadataBundle(name)
        paths = getPaths()
    
        environLocal.printDebug(['cache: starting processing of paths:', 
                                len(paths)])
    
        #mdb.addFromPaths(paths[-3:])
        mdb.addFromPaths(paths) # all paths
        #print mdb._storage
        mdb.write() # will use a default file path and  name


    environLocal.printDebug(['cache: writing time:', t, 'md items:', len(mdb._storage)])



if __name__ == "__main__":
    cacheCore()


